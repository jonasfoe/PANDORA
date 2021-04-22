from Bio.Align import substitution_matrices
import os
import PANDORA
import pickle
from PANDORA.PMHC import Model
# from Bio import Align
from Bio import pairwise2
from PANDORA.Pandora import Align
import statistics


def check_target_template(target, template):
    """ Checks if the target and the template are the same. If the user gave sequence info in the target, use that, else
        use the allele type.

    Args:
        target: (:obj:`Target`): Target object
        template: (:obj:`Template`): Template object

    Returns: (bool): True if target/template are the same, False if they are not.

    """
    out = False
    # Check if target peptide and template peptide are the same
    if target.peptide == template.peptide:
        # If the target has no sequence information, use allele type
        if target.M_chain_seq == '':
            # Check if the allele of target and template are the same
            if any(x in template.allele_type for x in target.allele_type):
                out = True

        # If the target has sequence information..
        elif target.M_chain_seq != '':
            # For MHCI, check if the M chain sequence of target and template are the same
            if target.MHC_class == 'I':
                if target.M_chain_seq == template.M_chain_seq:
                    out = True
            # For MHCII, check if the M and N chain sequence of target and template are the same
            elif target.MHC_class == 'II' and target.N_chain_seq != '':
                if target.M_chain_seq == template.M_chain_seq and target.N_chain_seq == template.N_chain_seq:
                    out = True
    if out:
        print('\n\t---- THE TARGET HAS THE SAME PEPTIDE AND ALLELE/SEQUENCE INFORMATION AS THE TEMPLATE ----')
        print('\tYou can find it at: http://www.imgt.org/3Dstructure-DB/cgi/details.cgi?pdbcode=%s\n' %(template.id))

    return out


def check_presence(target, database, seq_based_templ_selection = False):
    ''' Checks if the target the user submitted, already exists in has a template in the database with the same allele
        and peptide.

    Args:
        target: Target object
        database: Database object
        seq_based_templ_selection: bool, select the template based on the chain sequences.

    Returns: bool/Template object. If the target is already in the db, return the Template, otherwise return False
    
    '''
    putative_templates = []
    target_in_db = False
    if not seq_based_templ_selection:
        # For MHC I
        if target.MHC_class == 'I':
            # Check if there are templates with the same alleles
            for id in database.MHCI_data:
                if any(x in database.MHCI_data[id].allele_type for x in target.allele_type):
                    putative_templates.append(id)
            # Check if there is a putative template that also has the same peptide as the target
            for i in putative_templates:
                if database.MHCI_data[i].peptide == target.peptide:
                    target_in_db = database.MHCI_data[i]
        # For MHC II
        elif target.MHC_class == 'II':
            # Check if there are templates with the same alleles
            for id in database.MHCII_data:
                if any(x in database.MHCII_data[id].allele_type for x in target.allele_type):
                    putative_templates.append(id)
            # Check if there is a putative template that also has the same peptide as the target
            for i in putative_templates:
                if database.MHCII_data[i].peptide == target.peptide:
                    target_in_db = database.MHCII_data[i]

    elif seq_based_templ_selection:
        # Check for MHC I
        if target.MHC_class == 'I':
            # Check if there are templates with the same M chain sequence
            for id in database.MHCI_data:
                if database.MHCI_data[id].M_chain_seq == target.M_chain_seq:
                    putative_templates.append(id)
            # Check if there is a putative template that also has the same peptide as the target
            for i in putative_templates:
                if database.MHCI_data[i].peptide == target.peptide:
                    target_in_db = database.MHCI_data[i]
        # Check for MHC I
        if target.MHC_class == 'II':
            # Check if there are templates with the same M chain sequence
            for id in database.MHCII_data:
                if database.MHCII_data[id].M_chain_seq == target.M_chain_seq:
                    if database.MHCII_data[id].N_chain_seq == target.N_chain_seq:
                        putative_templates.append(id)
            # Check if there is a putative template that also has the same peptide as the target
            for i in putative_templates:
                if database.MHCII_data[i].peptide == target.peptide:
                    target_in_db = database.MHCII_data[i]

    return target_in_db


def predict_anchors_netMHCIIpan(peptide, allele_type, verbose = True):
    '''Uses netMHCIIpan to predict the binding core of a peptide and infer the anchor positions from that.

    Args:
        target: (Target): Target object containing the peptide sequence and allele type

    Returns: (lst): list of predicted anchor predictions

    '''
    all_netMHCpan_alleles = []
    with open(PANDORA.PANDORA_path + '/../netMHCIIpan-4.0/data/allele.list') as f:
        for line in f:
            all_netMHCpan_alleles.append(line.replace('\n',''))

    # Format the alles to netMHCIIpan readable format
    target_alleles = [i.split('-')[-1].replace('*', '_') for i in allele_type]

    # The DQ and DP alleles only function in pairs in netMHCIIpan, which we cannot match from our alleles
    # So take the first 3 partially matched allele combinations
    for i in target_alleles:
        if 'DRB' not in i:
            target_alleles = target_alleles + [al for al in all_netMHCpan_alleles if i.replace('_','') in al][:3]

    target_alleles = [i for i in target_alleles if i in all_netMHCpan_alleles]
    # If there are no target alleles that occur in netMHCIIpan, but there is a mouse allele, use the 2 mouse alleles
    # that are supported by netMHCIIpan
    if target_alleles == [] and any(al.startswith('H2') for al in allele_type):
        target_alleles = ['H-2-IAd', 'H-2-IAb']
    # If there is no target allele that occurs in netMHCIIpan, just use the standard DRB1_0101
    if target_alleles == []:
        target_alleles = ['DRB1_0101']

    target_alleles = ','.join(list(set(target_alleles)))

    # Setup files
    netmhciipan = PANDORA.PANDORA_path + '/../netMHCIIpan-4.0/netMHCIIpan'
    infile = PANDORA.PANDORA_path + '/../netMHCIIpan-4.0/tmp/pep.txt'
    outfile = PANDORA.PANDORA_path + '/../netMHCIIpan-4.0/tmp/pept_prediction.txt'

    # Write peptide sequence to input file for netMHCIIpan
    with open(infile, 'w') as f:
        f.write(peptide)

    try:
        # run netMHCIIpan
        os.system('%s -f %s -inptype 1 -a %s > %s' %(netmhciipan, infile, target_alleles, outfile))

        # Get the output from the netMHCIIpan prediction
        # {allele: (offset, core, core_reliability, score_EL, %rank_EL)}
        pred = {}
        with open(outfile) as f:
            for line in f:
                if peptide in line:
                    ln = [i for i in line[:-1].split(' ') if i != '']
                    pred[ln[1]] = (int(ln[3]), ln[4], float(ln[5]))

        # For every allele, the binding core is predicted. Take the allele with the highest reliability score
        best_allele = max((pred[i][2], i) for i in pred)[1]
    except ValueError:
        print('Could not predict binding core using netMHCIIpan. Will use the most common anchor positions instead')
        return [3, 6, 8, 11]

    # save the offset, core and prediction reliability
    offset, core, core_reliability = pred[best_allele][0], pred[best_allele][1], pred[best_allele][2]

    # Remove output file
    os.system('rm %s %s' %(infile, outfile))

    # Use the canonical spacing for 9-mer binding cores to predict the anchor positions
    predicted_anchors = [offset+1,offset+4,offset+6,offset+9]
    # Make sure the prediction is not longer than the peptide just in case
    predicted_anchors = [i for i in predicted_anchors if i <= len(peptide)]

    if verbose:
        print('\tPredicted the binding core using netMHCIIpan (4.0):\n')
        print('\toffset:\t%s\n\tcore:\t%s\n\tprob:\t%s\n' %(offset, core, core_reliability ))
        print('\tPredicted peptide anchor residues (assuming canonical spacing): %s' %predicted_anchors)

    return predicted_anchors


def predict_anchors_netMHCpan(peptide, allele_type, verbose = True):
    '''Uses netMHCIIpan to predict the binding core of a peptide and infer the anchor positions from that.

    Args:
        peptide: (str): AA sequence of the peptide
        allele_type: (lst): list of strings of allele types
        verbose: (bool):

    Returns: (lst): list of predicted anchor predictions

    '''
    all_netMHCpan_alleles = []
    with open(PANDORA.PANDORA_path + '/../netMHCpan-4.1/data/allelenames') as f:
        for line in f:
            all_netMHCpan_alleles.append(line.split(' ')[0].replace(':',''))

    # Format alleles
    target_alleles = [i.replace('*','') for i in allele_type]
    target_alleles = [i for i in target_alleles if i in all_netMHCpan_alleles]

    target_alleles = ','.join(target_alleles)

    # Setup files
    netmhcpan = PANDORA.PANDORA_path + '/../netMHCpan-4.1/netMHCpan'
    infile = PANDORA.PANDORA_path + '/../netMHCpan-4.1/tmp/pep.txt'
    outfile = PANDORA.PANDORA_path + '/../netMHCpan-4.1/tmp/pept_prediction.txt'

    # Write peptide sequence to input file for netMHCIIpan
    with open(infile, 'w') as f:
        f.write(peptide)

    os.system('%s -p %s -a %s > %s' %(netmhcpan, infile, target_alleles, outfile))

    # Get the output from the netMHCIIpan prediction
    # {allele: (core, %rank_EL)}
    pred = {}
    with open(outfile) as f:
        for line in f:
            if peptide in line:
                ln = [i for i in line[:-1].split(' ') if i != '']
                pred[ln[1]] = (ln[3], float(ln[12]))

    # For every allele, the binding core is predicted. Take the allele with the highest reliability score
    best_allele = min((pred[i][1], i) for i in pred)[1]

    # Do a quick alignment of the predicted core and the peptide to find the anchors. (the predicted binding core can
    # contain dashes -. Aligning them makes sure you take the right residue as anchor.
    alignment = pairwise2.align.globalxx(peptide, pred[best_allele][0])

    # Find the anchors by finding the first non dash from the left and from the right
    predicted_anchors = [2,len(peptide)]
    for i in range(len(alignment[0][1])):
        if alignment[0][1][i] != '-':
            predicted_anchors[0] = i + 2
            break
    for i in range(len(alignment[0][1])):
        if alignment[0][1][::-1][i] != '-':
            predicted_anchors[1] = len(alignment[0][1]) - i
            break

    if verbose:
        print('\tPredicted the binding core using netMHCpan (4.1):\n')
        print('\tcore:\t%s\n\t%%Rank EL:\t%s\n' %(pred[best_allele][0], pred[best_allele][1] ))
        print('\tPredicted peptide anchor residues (assuming canonical spacing): %s' %predicted_anchors)

    return predicted_anchors


def find_template(target, database, seq_based_templ_selection = False, benchmark=False):
    ''' Selects the template structure that is best suited as template for homology modelling of the target

    Args:
        target: Target object
        database: Database object
        seq_based_templ_selection: (bool) Use template selection based on template sequences instead of allele.

    Returns: Template object

    '''

    if not seq_based_templ_selection:

        PAM30 = substitution_matrices.load('PAM30')

        ## For MHC I
        if target.MHC_class == 'I':

            # Define available alleles in database
            available_alleles = []
            for ID in database.MHCI_data:
                if benchmark and ID == target.id:
                    pass
                else:
                    available_alleles.extend(database.MHCI_data[ID].allele_type)
            available_alleles = list(set(available_alleles))

            # Adapt the target allele name if necessary
            #target_alleles = [allele_name_adapter(allele, available_alleles) for allele in target.allele_type]
            target_alleles = allele_name_adapter(target.allele_type, available_alleles)
            target_alleles = list(set(target_alleles))

            # Find template structures with matching alleles
            putative_templates = {}
            for ID in database.MHCI_data:
                if benchmark and ID == target.id:
                    pass
                else:
                    for tar_allele in target_alleles:
                        if any(tar_allele in put_temp_allele for put_temp_allele in database.MHCI_data[ID].allele_type):
                            # update dict with ID:all matching alleles
                            #TODO: is this list of matching allele obsolete?
                            putative_templates[ID] = list(
                                set(target.allele_type) & set(database.MHCI_data[ID].allele_type))

            # If the target template already occured in the database, remove it from the dict of putative templates
            #putative_templates.pop(target.id)

            # Find the putative template with the best matching peptide
            pos_list = []
            for ID in putative_templates:
                score = 0
                try:
                    pept_anchs = target.anchors
                except:
                    pept_anchs = [1, len(target.peptide) -1]

                temp_pept = database.MHCI_data[ID].peptide
                temp_anchs = database.MHCI_data[ID].anchors
                aligned_pept, aligned_temp_pept = align_peptides(target.peptide,
                                                                 pept_anchs[0], pept_anchs[1],
                                                                 temp_pept,
                                                                 temp_anchs[0], temp_anchs[1])

                aligned_pept = aligned_pept.replace('-','*')
                aligned_temp_pept = aligned_temp_pept.replace('-','*')
                #min_len = min([len(target.peptide), len(temp_pept)])
                #score -= ((abs(len(target.peptide) - len(temp_pept)) ** 2.4))  # !!!  ## Gap Penalty #Is now handled by normal PAM30
                for i, (aa, bb) in enumerate(zip(aligned_pept, aligned_temp_pept)):
                    try:
                        # gain = MatrixInfo.pam30[aa, bb]
                        gain = PAM30[aa, bb]
                        score += gain
                    except KeyError:
                            try:
                                # gain = MatrixInfo.pam30[bb, aa]
                                gain = PAM30[bb, aa]
                                score += gain
                            except KeyError:
                                score = -50
                                pass
                pos_list.append((score, temp_pept, ID))

            if len(pos_list) == 0:
                raise Exception('Pandora could not find any putative template! Please try to define your own template or contact us for help')
            # Take the putative template with the max scoring peptide
            template_id = pos_list[[i[0] for i in pos_list].index(max([i[0] for i in pos_list]))][2]
            # Return the Template object of the selected template that will be used for homology modelling


            return database.MHCI_data[template_id], check_target_template(target, database.MHCI_data[template_id])


            ## For MHC II
        if target.MHC_class == 'II':

            # Find template structures with matching alleles
            putative_templates = {}
            for ID in database.MHCII_data:
                if benchmark:
                    if ID != target.id:
                        if any(x in database.MHCII_data[ID].allele_type for x in target.allele_type):
                            putative_templates[ID] = list(
                                set(target.allele_type) & set(database.MHCII_data[ID].allele_type))
                else:
                    if any(x in database.MHCII_data[ID].allele_type for x in target.allele_type):
                        putative_templates[ID] = list(
                            set(target.allele_type) & set(database.MHCII_data[ID].allele_type))

            # Find the peptide with the highest alignment score. If there are multiple, take the first one with same
            # same anchor positions
            # template_id = find_best_template_peptide(target=target,
            #                                          templates=[database.MHCII_data[i] for i in putative_templates])

            # Find the putative template with the best matching peptide
            pos_list = []
            for ID in putative_templates:
                score = 0
                temp_pept = database.MHCII_data[ID].peptide
                min_len = min([len(target.peptide), len(temp_pept)])
                score -= ((abs(len(target.peptide) - len(temp_pept)) ** 2.4))  # !!!  ## Gap Penalty
                for i, (aa, bb) in enumerate(zip(target.peptide[:min_len], temp_pept[:min_len])):
                    try:
                        # gain = MatrixInfo.pam30[aa, bb]
                        gain = PAM30[aa, bb]
                        score += gain
                    except KeyError:
                        try:
                            # gain = MatrixInfo.pam30[bb, aa]
                            gain = PAM30[bb, aa]
                            score += gain
                        except KeyError:
                            score = -50
                            pass
                pos_list.append((score, temp_pept, ID))

            if len(pos_list) == 0:
                raise Exception('Pandora could not find any putative template! Please try to define your own template or contact us for help')
            # Take the putative template with the max scoring peptide
            template_id = pos_list[[i[0] for i in pos_list].index(max([i[0] for i in pos_list]))][2]
            # Return the Template object of the selected template that will be used for homology modelling

            return database.MHCII_data[template_id], check_target_template(target, database.MHCII_data[template_id])

    # Sequence based template search if the sequences of the target are provided
    elif target.M_chain_seq != '' and seq_based_templ_selection:

        if target.MHC_class == 'I':

            # define target sequences
            tar_seq = database.MHCI_data[target.id].M_chain_seq
            tar_pept = database.MHCI_data[target.id].peptide
            # keep track of alignment scores
            scores = {}
            # Perform a pairwise alignment of the target and all templates for the MHC M chain and peptide
            for i in database.MHCI_data:
                aligner = Align.PairwiseAligner()
                aligner.substitution_matrix = substitution_matrices.load("BLOSUM80")  # PAM30 for pept??

                M_score = aligner.align(tar_seq, database.MHCI_data[i].M_chain_seq).score
                P_score = aligner.align(tar_pept, database.MHCI_data[i].peptide).score

                scores[i] = (M_score, P_score)
            # Remove the target structure from this dict, you cannot select the target as template
            scores.pop(target.id, None)
            # take the 10 best scoring templates
            best_MHCs = sorted(scores, key=scores.get, reverse=True)[:10]
            # take the template with the best scoring peptide
            best_template = max((v[1], k) for k, v in scores.items() if k in best_MHCs)[1]

            return database.MHCI_data[best_template], check_target_template(target, database.MHCI_data[template_id])

        if target.MHC_class == 'II':
            # define target sequences
            tar_seq = database.MHCII_data[target.id].M_chain_seq + database.MHCII_data[target.id].N_chain_seq
            tar_pept = database.MHCII_data[target.id].peptide
            # keep track of alignment scores
            scores = {}

            for i in database.MHCII_data:
                aligner = Align.PairwiseAligner()
                aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")  # or PAM30 ??

                temp_seq = database.MHCII_data[i].M_chain_seq + database.MHCII_data[i].N_chain_seq
                MN_score = aligner.align(tar_seq, temp_seq).score
                P_score = aligner.align(tar_pept, database.MHCII_data[i].peptide).score

                scores[i] = (MN_score, P_score)
            # Remove the target structure from this dict, you cannot select the target as template
            scores.pop(target.id, None)
            # take the 10 best scoring templates
            best_MHCs = sorted(scores, key=scores.get, reverse=True)[:10]
            # take the template with the best scoring peptide
            best_template = max((v[1], k) for k, v in scores.items() if k in best_MHCs)[1]

            return database.MHCII_data[best_template], check_target_template(target, database.MHCI_data[template_id])


def write_ini_script(target, template, alignment_file, output_dir):
    ''' Writes the MyLoop.py and cmd_modeller_ini.py files. This function takes two template python scripts and fills
        in the required information: Anchor positions for the MyLoop file and structure name + alignment file for the
        cmd_modeller_ini file.

    Args:
        target: Target object
        template: Template object
        alignment_file: (string) path to alignment file
        output_dir: (string) path to output directory

    '''

    anch = target.anchors

    if target.MHC_class == 'I':
        with open(output_dir+ '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line and 'M.selection' in line:
                    myloopscript.write(line % (anch[0]+1, anch[-1]-1))
                elif 'SPECIAL_RESTRAINTS_BREAK' in line:
                    break
                elif 'contact_file = open' in line:
                    myloopscript.write(line % template_ID)
                else:
                    myloopscript.write(line)
            MyL_temp.close()

    if target.MHC_class == 'II':
        with open(output_dir + '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template_II.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line and 'M.selection' in line:
                    myloopscript.write(line % (1, anch[0])) # write the first anchor
                    for i in range(len(anch)-1): # Write all the inbetween acnhors if they are there
                        myloopscript.write(line % (anch[i] + 2, anch[i+1]))
                    myloopscript.write(line % (anch[-1] + 2, len(target.peptide))) # Write the last anchor
                elif 'SPECIAL_RESTRAINTS_BREAK' in line:
                    break
                elif 'contact_file = open' in line:
                    myloopscript.write(line % template_ID)
                else:
                    myloopscript.write(line)
            MyL_temp.close()

    with open(output_dir.replace('\\ ', ' ') + '/cmd_modeller_ini.py', 'w') as modscript:
        cmd_m_temp = open(PANDORA.PANDORA_path + '/Pandora/cmd_modeller_ini.py', 'r')
        for line in cmd_m_temp:
            if 'alnfile' in line:
                modscript.write(line % os.path.basename(alignment_file))
            elif 'knowns' in line:
                modscript.write(line % (template.id, target.id))
            else:
                modscript.write(line)
        cmd_m_temp.close()


# alignment_file = mod.alignment.alignment_file
# output_dir = mod.output_dir
# template = mod.template
# helix = [3, 8]
# BETA-SHEET-MARKER


def write_modeller_script(target, template, alignment_file, output_dir, n_homology_models=1, n_loop_models = 20, n_jobs=None, stdev=0.1, helix = False, sheet = False):
    ''' Write script that refines the loops of the peptide
    Args:
        target: Target object
        template: Template object
        alignment_file: (str): path to alignment file
        output_dir: (str): path to output directory
        n_models:  (int): number of models modeller generates per run
        n_jobs: (int): number of parallel jobs. Is recommended to use as many jobs as the number of models: less will result in
                a slower run, more will not add any benefit but might occupy cores unnecessarily.
        stdev: (flt): standard deviation of modelling restraints. Higher = more flexible restraints.
        helix: (lst): List of the alpha helix start and end-positions as integers. I.e. [3,8] for a helix between
                        peptide residue 3 and 8.
        sheet: (lst): List containing: start position of B-sheet 1, start position of B-sheet 2 and the length of the
                        B-sheet in h-bonds. For example: ["O:2:P","N:54:M",2] for a parallel B-sheet; The sheet starts
                        at the Oxigen atom of the 2nd residue of chain P and at the Nitrogen of the 54th residue of
                        chain M and has a length of 2 H-bonds. Or; ["N:6:P", "O:13:P", -3], with -3 denoting an
                        anti-parallel B-sheet with a length of 3 H-bonds.
    '''



    anch = target.anchors

    if target.MHC_class == 'I':
        with open(output_dir.replace('\\ ', ' ') + '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line and 'M.selection' in line:
                    myloopscript.write(line %(anch[0]+1, anch[-1]-1))  # write the first anchor
                elif 'contact_file = open' in line:
                    myloopscript.write(line %(target.id))
                elif 'STDEV MARKER' in line:
                    myloopscript.write(line %(stdev))
                elif helix and 'ALPHA-HELIX-MARKER' in line:
                    myloopscript.write(line.replace('# ALPHA-HELIX-MARKER', 'rsr.add(M.secondary_structure.alpha(self.residue_range("%s:P", "%s:P")))' %(helix[0], helix[1])))
                elif sheet and 'BETA-SHEET-MARKER' in line:
                    myloopscript.write(line.replace('# BETA-SHEET-MARKER', 'rsr.add(M.secondary_structure.sheet(atoms["%s"], atoms["%s"], sheet_h_bonds=%s))' %(sheet[0], sheet[1], sheet[2])))
                else:
                    myloopscript.write(line)
            MyL_temp.close()

    if target.MHC_class == 'II':
        with open(output_dir.replace('\\ ', ' ') + '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template_II.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line and 'M.selection' in line:
                    myloopscript.write(line % (1, anch[0]))  # write the first anchor
                    for i in range(len(anch) - 1):  # Write all the inbetween acnhors if they are there
                        myloopscript.write(line %(anch[i] + 2, anch[i + 1]))
                    myloopscript.write(line %(anch[-1] + 2, len(target.peptide)))  # Write the last anchor
                elif 'contact_file = open' in line:
                    myloopscript.write(line %(target.id))
                elif 'STDEV MARKER' in line:
                    myloopscript.write(line %(stdev))
                elif helix and 'ALPHA-HELIX-MARKER' in line:
                    myloopscript.write(line.replace('# ALPHA-HELIX-MARKER', 'rsr.add(M.secondary_structure.alpha(self.residue_range("%s:P", "%s:P")))' %(helix[0], helix[1])))
                elif sheet and 'BETA-SHEET-MARKER' in line:
                    myloopscript.write(line.replace('# BETA-SHEET-MARKER', 'rsr.add(M.secondary_structure.sheet(atoms["%s"], atoms["%s"], sheet_h_bonds=%s))' %(sheet[0], sheet[1], sheet[2])))
                else:
                    myloopscript.write(line)
            MyL_temp.close()

    with open(output_dir.replace('\\ ', ' ') + '/cmd_modeller.py', 'w') as modscript:
        cmd_m_temp = open(PANDORA.PANDORA_path + '/Pandora/cmd_modeller_template.py', 'r')
        for line in cmd_m_temp:
            if 'alnfile' in line:
                modscript.write(line %(os.path.basename(alignment_file)))
            elif 'knowns' in line:
                modscript.write(line %(template.id, target.id))
            elif 'a.ending_model' in line:
                modscript.write(line % (n_homology_models))
            elif 'a.loop.ending_model' in line:
                modscript.write(line % (n_loop_models))
            else:
                if n_jobs != None: #If this is a parallel job
                    if 'PARALLEL_JOB_LINE_TO_COMPLETE' in line:
                        modscript.write(line %(str(n_jobs))) #specify the number of cores
                    else:
                        modscript.write(line)  #Write the line as it is
                else: #If this is not a parallel job
                    if 'PARALLEL_JOB_LINE' in line: #do not write the lines requested for parallelization
                        pass
                    else:
                        modscript.write(line)  #Write the line as it is
        cmd_m_temp.close()



def run_modeller(output_dir, target, python_script = 'cmd_modeller.py', benchmark = False, pickle_out = True, keep_IL = False):
    ''' Perform the homology modelling.

    Args:
        output_dir: (string) path to output directory
        target: Target object
        python_script:  (string) path to script that performs the modeller modelling. cmd_modeller.py
        benchmark: (bool) Perform L-RMSD calculations? only works if the target id is an existing pdb id
        pickle_out: (bool) Save a .pkl with the results

    Returns: (list) of Model objects

    '''

    # Change working directory
    os.chdir(output_dir)
    # run Modeller to perform homology modelling
    os.popen('python3 %s > modeller.log' %python_script).read()
    os.chdir(os.path.dirname(PANDORA.PANDORA_path))

    # Parse .log file
    logf = []
    f = open(output_dir + '/modeller.log')
    for line in f:
        if line.startswith(target.id + '.'):   #target.id
            l = line.split()
            if len(l) > 2:
                logf.append(tuple(l))
    f.close()

    # If keep_IL is true (happens if the target and template are the same), also use the initial model as one of the
    # results. This will also happen while benchmarking.
    if keep_IL:
        # Also take the Initial Loop model. Take the molpdf from the pdb header.
        il_file = [i for i in os.listdir(output_dir) if i.startswith(target.id + '.IL')][0]
        # il = open(output_dir + '/' + il_file)
        # for line in il:
        #     if 'MODELLER OBJECTIVE FUNCTION' in line:
        #         il_molpdf = line.split()[-1]
        # f.close()
        # Create a fake molpdf score for the IL model: the best molpdf from the real models - 1
        fake_molpdf = str(min(float(i[1]) for i in logf) - 1)
        # Append the filename and molpdf to the rest of the data
        logf.append((il_file, fake_molpdf, ''))

    # Write to output file
    f = open(output_dir + '/molpdf_DOPE.tsv', 'w')
    for i in logf:
        f.write('matched_' + i[0] + '\t' + i[1] + '\t' + i[2] + '\n')
    f.close()


    # Create Model object of each theoretical model and add it to results
    results = []
    for i in range(len(logf)):
        try:
            m = Model.Model(target, model_path=output_dir + '/' + logf[i][0], output_dir = output_dir,
                                            molpdf=logf[i][1], dope=logf[i][2])

        except:
            print('Something went wrong when calling Model.Model() for case %s' %target.id)
        if benchmark:
            try:
                m.calc_LRMSD(PANDORA.PANDORA_data + '/PDBs/pMHC' + target.MHC_class + '/' + target.id + '.pdb')
                # print('l-RMSD for %s: %f' %(target.id, m.lrmsd))
            except:
                print('Something went wrong when calculating l-RMSD for case %s' %target.id)
                pass
            if target.MHC_class == 'II': #only calculate the core L-rmsd for MHCII cases
                try:
                    m.calc_Core_LRMSD(PANDORA.PANDORA_data + '/PDBs/pMHC' + target.MHC_class + '/' + target.id + '.pdb')
                    # print('Core l-RMSD for %s: %f' %(target.id, m.core_lrmsd))
                except:
                    print('Something went wrong when calculating core l-RMSD for case %s' %target.id)
                    pass
        results.append(m)


    # Save results as pickle
    if pickle_out:
        pickle.dump(results, open("%s/results_%s.pkl" %(output_dir, os.path.basename(os.path.normpath(output_dir))), "wb"))

    return results


def top5_from_results(results):
    ''' Get the median RMSD of the top 5 best molpdf models

    Args:
        results: (lst): list of models

    Returns: (tpl): median LRMSD and median core LRMSD

    '''
    top5 = [i[0] for i in
            sorted([(m.model_path, m.moldpf) for m in results], key=lambda x: x[1], reverse=False)[
            :5]]

    median_rmsd, median_core = False, False
    try:
        top5_rmsds = []
        for m in results:
            if m.model_path in top5:
                top5_rmsds.append(m.lrmsd)
        median_rmsd = statistics.median(top5_rmsds)
    except AttributeError:
        pass

    try:
        top5_core_rmsds = []
        for m in results:
            if m.model_path in top5:
                top5_core_rmsds.append(m.core_lrmsd)
        median_core = statistics.median(top5_core_rmsds)
    except AttributeError:
        pass

    return median_rmsd, median_core


def align_peptides(seq1, anch1_seq1, anch2_seq1, seq2, anch1_seq2, anch2_seq2):
    '''
    Align two MHC-I peptides making overlap the anchors.
    This function does NOT use an alignment matrix (e.g. BLOSUM, PAM, etc).
    It computes a simple anchor position alignment and inserts gap in the
    middle part to make the final sequences have the same lenghts.

    Args:
        seq1(str) : sequence of the first peptide.
        anch1_seq1(int) : position of the first anchor of seq1. Position must be given in Python numbering (0-N)
        anch2_seq1(int) : position of the second anchor of seq1. Position must be given in Python numbering (0-N)
        seq2(str) : sequence of the second peptide.
        anch1_seq1(int) : position of the first anchor of seq1. Position must be given in Python numbering (0-N)
        anch2_seq1(int) : position of the second anchor of seq1. Position must be given in Python numbering (0-N)

    Returns:
        ali_seq1(str)
    '''

    seq1_core = anch2_seq1 - anch1_seq1
    seq2_core = anch2_seq2 - anch1_seq2
    tail1 = [x for x in seq1[anch2_seq1:]]
    tail2 = [x for x in seq2[anch1_seq2:]]

    list1 = [x for x in seq1]
    list2 = [x for x in seq2]
    #Adding gaps in cores
    if seq1_core > seq2_core:
        for x in range(seq1_core - seq2_core):
            list2.insert(int(len(seq2)/2), '-')
    elif seq1_core < seq2_core:
        for x in range(seq2_core - seq1_core):
            list1.insert(int(len(seq1)/2), '-')
    ### Adding gaps in heads
    if anch1_seq1 > anch1_seq2:
        for x in range(anch1_seq1 - anch1_seq2):
            list2.insert(0, '-')
    elif anch1_seq1 < anch1_seq2:
        for x in range(anch1_seq2 - anch1_seq1):
            list1.insert(0, '-')
    ### Adding gaps in heads
    if len(tail1) > len(tail2):
        for x in range(len(tail1) - len(tail2)):
            list2.insert(-1, '-')
    elif len(tail1) < len(tail2):
        for x in range(len(tail1) - len(tail2)):
            list1.insert(-1, '-')

    ali_seq1 = ('').join(list1)
    ali_seq2 = ('').join(list2)
    return ali_seq1, ali_seq2

def allele_name_adapter(allele, available_alleles):
    '''
    Cuts the given allele name to make it consistent with the alleles in allele_ID.

    Args:
        allele(list) : Allele names
        allele_ID(dict) : Dictionary of structure IDs (values) in the dataset for each allele (keys)
    '''
    #homolog_allele = '--NONE--'
    for a in range(len(allele)):
        if allele[a].startswith('HLA'):      # Human
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:8] in key for key in list(available_alleles)):
                allele[a] = allele[a][:8]
            elif any(allele[a][:6] in key for key in list(available_alleles)):
                allele[a] = allele[a][:6]
            else:
                allele[a] = allele[a][:4]
        elif allele[a].startswith('H2'):    # Mouse
            #homolog_allele = 'RT1'
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:4] in key for key in list(available_alleles)):
                allele[a] = allele[a][:4]
            else:
                allele[a] = allele[a][:3]
        elif allele[a].startswith('RT1'):          # Rat
            #homolog_allele = 'H2'
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:5] in key for key in list(available_alleles)):
                allele[a] = allele[a][:5]
            else:
                allele[a] = allele[a][:4]
        elif allele[a].startswith('BoLA'):        # Bovine
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:10] in key for key in list(available_alleles)):
                allele[a] = allele[a][:10]
            elif any(allele[a][:7] in key for key in list(available_alleles)):
                allele[a] = allele[a][:7]
            else:
                allele[a] = allele[a][:5]
        elif allele[a].startswith('SLA'):        # Suine
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:9] in key for key in list(available_alleles)):
                allele[a] = allele[a][:9]
            elif any(allele[a][:6] in key for key in list(available_alleles)):
                allele[a] = allele[a][:6]
            else:
                allele[a] = allele[a][:4]
        elif allele[a].startswith('MH1-B'):        # Chicken
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:8] in key for key in list(available_alleles)):
                allele[a] = allele[a][:8]
            else:
                allele[a] = allele[a][:6]
        elif allele[a].startswith('MH1-N'):        # Chicken
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:9] in key for key in list(available_alleles)):
                allele[a] = allele[a][:9]
            else:
                allele[a] = allele[a][:6]
        elif allele[a].startswith('BF2'):        # Chicken
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:6] in key for key in list(available_alleles)):
                allele[a] = allele[a][:6]
            else:
                allele[a] = allele[a][:4]
        elif allele[a].startswith('Mamu'):       # Monkey
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:13] in key for key in list(available_alleles)):
                allele[a] = allele[a][:13]
            elif any(allele[a][:9] in key for key in list(available_alleles)):
                allele[a] = allele[a][:9]
            else:
                allele[a] = allele[a][:5]
        elif allele[a].startswith('Eqca'):        # Horse
            if any(allele[a] in key for key in list(available_alleles)):
                pass
            elif any(allele[a][:10] in key for key in list(available_alleles)):
                allele[a] = allele[a][:10]
            elif any(allele[a][:7] in key for key in list(available_alleles)):
                allele[a] = allele[a][:7]
            else:
                allele[a] = allele[a][:5]
    return(allele)#, homolog_allele)