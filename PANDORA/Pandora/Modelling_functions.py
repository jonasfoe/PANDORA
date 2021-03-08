from Bio.Align import substitution_matrices
PAM30 = substitution_matrices.load('PAM30')
import os
import PANDORA
import pickle
from PANDORA.PMHC import Model


def find_template(target, database):
    ''' Selects the structure that is best suited as template for homology modelling of the target

    :param target: (Target) object
    :param database: (Database) object
    :return: (Template) Template object of the best structure
    '''


    ## For MHC I
    if target.MHC_class == 'I':

        # Find template structures with matching alleles
        putative_templates = {}
        for id in database.MHCI_data:
            if any(x in database.MHCI_data[id].allele for x in target.allele):
                putative_templates[id] = list(
                    set(target.allele) & set(database.MHCI_data[id].allele))  # update dict with ID:all matching alleles

        # If the target template already occured in the database, remove it from the dict of putative templates
        putative_templates.pop(target.PDB_id)

        # Find the putative template with the best matching peptide
        pos_list = []
        for ID in putative_templates:
            score = 0
            temp_pept = database.MHCI_data[ID].peptide
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

        # Take the putative template with the max scoring peptide
        template_id = pos_list[[i[0] for i in pos_list].index(max([i[0] for i in pos_list]))][2]
        # Return the Template object of the selected template that will be used for homology modelling
        return database.MHCI_data[template_id]


    ## For MHC II
    if target.MHC_class == 'II':

        # Find template structures with matching alleles
        putative_templates = {}
        for id in database.MHCII_data:
            if any(x in database.MHCII_data[id].allele for x in target.allele):
                # putative_templates[id] = db.MHCII_data[id].allele
                putative_templates[id] = list(set(target.allele) & set(database.MHCII_data[id].allele)) #update dict with ID:all matching alleles

        # If the target template already occured in the database, remove it from the dict of putative templates
        putative_templates.pop(target.PDB_id)

        # check if there are any template that have two matching alleles
        # max([len(v) for k,v in putative_templates.items()])

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

        # Take the putative template with the max scoring peptide
        template_id = pos_list[[i[0] for i in pos_list].index(max([i[0] for i in pos_list]))][2]
        # Return the Template object of the selected template that will be used for homology modelling
        return database.MHCII_data[template_id]

def write_ini_script(target, template, alignment_file, output_dir):
    ''' Writes the MyLoop.py and cmd_modeller_ini.py files. This function takes two template python scripts and fills
    in the required information: Anchor positions for the MyLoop file and structure name + alignment file for the
    cmd_modeller_ini file.

    :param target:
    :param template:
    :param alignment_file:
    :param output_dir:
    :return:
    '''

    anch = target.anchors

    if target.MHC_class == 'I':
        with open(output_dir.replace('\\ ',' ') + '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line:
                    myloopscript.write(line % (anch[0], anch[-1]))
                elif 'SPECIAL_RESTRAINTS_BREAK' in line:
                    break
                elif 'contact_file = open' in line:
                    myloopscript.write(line % template_ID)
                else:
                    myloopscript.write(line)
            MyL_temp.close()

    if target.MHC_class == 'II':
        with open(output_dir.replace('\\ ',' ') + '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template_II.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line:
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
                modscript.write(line % (template.PDB_id, target.PDB_id))
            else:
                modscript.write(line)
        cmd_m_temp.close()



def write_modeller_script(target, template, alignment_file, output_dir):
    ''' Write script that refines the loops of the peptide

    :param target:
    :param template:
    :param alignment_file:
    :param output_dir:
    :return:  writes two files; Myloop.py and cmd_modeller.py that contain the info to run modeller
    '''


    anch = target.anchors

    if target.MHC_class == 'I':
        with open(output_dir.replace('\\ ', ' ') + '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line:
                    myloopscript.write(line % (anch[0], anch[-1]))  # write the first anchor
                elif 'contact_file = open' in line:
                    myloopscript.write(line % target.PDB_id)
                else:
                    myloopscript.write(line)
            MyL_temp.close()

    if target.MHC_class == 'II':
        with open(output_dir.replace('\\ ', ' ') + '/MyLoop.py', 'w') as myloopscript:
            MyL_temp = open(PANDORA.PANDORA_path + '/Pandora/MyLoop_template_II.py', 'r')
            for line in MyL_temp:
                if 'self.residue_range' in line:
                    myloopscript.write(line % (1, anch[0]))  # write the first anchor
                    for i in range(len(anch) - 1):  # Write all the inbetween acnhors if they are there
                        myloopscript.write(line % (anch[i] + 2, anch[i + 1]))
                    myloopscript.write(line % (anch[-1] + 2, len(target.peptide)))  # Write the last anchor
                elif 'contact_file = open' in line:
                    myloopscript.write(line % target.PDB_id)
                else:
                    myloopscript.write(line)
            MyL_temp.close()


    with open(output_dir.replace('\\ ', ' ') + '/cmd_modeller.py', 'w') as modscript:
        cmd_m_temp = open(PANDORA.PANDORA_path + '/Pandora/cmd_modeller_template.py', 'r')
        for line in cmd_m_temp:
            if 'alnfile' in line:
                modscript.write(line %(os.path.basename(alignment_file)))
            elif 'knowns' in line:
                modscript.write(line %(template.PDB_id, target.PDB_id))
            else:
                modscript.write(line)
        cmd_m_temp.close()

def run_modeller(output_dir, target, python_script = 'cmd_modeller.py', benchmark = False, pickle_out = True):
    ''' Perform the homology modelling.

    :param python_script: (string) path to script that performs the modeller modelling. cmd_modeller.py
    :return: list of Model objects
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
        if line.startswith(target.PDB_id + '.'):
            l = line.split()
            if len(l) > 2:
                logf.append(tuple(l))
    f.close()

    # Create Model object of each theoretical model and add it to results
    results = []
    for i in range(len(logf)):
        try:
            m = Model.Model(target, output_dir, model_path=output_dir + '/' + logf[i][0],
                                            molpdf=logf[i][1], dope=logf[i][2])
            if benchmark:

                m.calc_LRMSD(PANDORA.PANDORA_data + '/PDBs/pMHC' + target.MHC_class + '/' + target.PDB_id + '.pdb')
                m.calc_Core_LRMSD(PANDORA.PANDORA_data + '/PDBs/pMHC' + target.MHC_class + '/' + target.PDB_id + '.pdb')
            results.append(m)
        except:
            pass

    # Save results as pickle
    if pickle_out:
        pickle.dump(results, open("%s/results_%s.pkl" %(output_dir, os.path.basename(os.path.normpath(output_dir))), "wb"))

    return results