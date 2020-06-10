#!/usr/bin/python
###    ###
from modelling_scripts import data_prep
import pickle
from Bio import SeqIO
#import subprocess
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import IUPAC
from Bio.PDB import PDBParser
import os
import time
from Bio.SubsMat import MatrixInfo
from random import choice
import csv
#import sys

### Retriving Dictionary with PDB IDs and chain lengths ###

##IDD, bad_IDs = data_prep.imgt_retrieve_clean('data/final_mhc1_3d_structure_data_with_pdb_ids.tsv')
#IDD, bad_IDs = data_prep.imgt_retrieve_clean('data/csv_pkl_files/mhc_ligand_table_export_1578913026.csv', 76, 80, ',')

#outdir_name = sys.argv[1]

outdir_name = 'anchor_weight_test'

###########################################
### Organizing dicts ###

IDD_file = open('data/csv_pkl_files/IDs_ChainsCounts_dict.pkl', 'rb')
IDD = pickle.load(IDD_file)
bad_IDs = pickle.load(IDD_file)
IDD_file.close()

### Organizing Allele IDs in a dictionary ###
allele_ID = {}
for key in IDD:
    if 'HLA' in IDD[key]['allele']:
        try:
            allele_ID[IDD[key]['allele']].append(key)
        except KeyError:
            allele_ID[IDD[key]['allele']] = [key]

###########################################
###  Setting variables 

pept_seqs = data_prep.get_peptides_from_csv('data/csv_pkl_files/table_1_AnAnalysisofNaturalTCellResponsestoPredictedTumorNeoepitopes.csv', 3, 4, ',')


anch_dict = { 8: (1, 7), 9 : (1, 8), 10 : (1, 9), 
              11 : (1, 10), 12 : (1, 11)}
scores_rules = { (anch_dict[length][0]-1) : {'pos' : 1, 'ID' : 2}, (anch_dict[length][0]+1) : {'pos' : 1, 'ID' : 2}, 
                anch_dict[length][0] : {'pos' : 5, 'ID': 10}, anch_dict[length][1] : {'pos' : 3, 'ID' : 8}}

remove_temp_outputs = False
cutoff = 5

maxs = []
maxsl = []
non_modelled = []
print_results = False

###########################################


for k, pept_seq in enumerate(pept_seqs):
    ext_flag = False
    query = 'query_' + str(k + 1)
    print( '## Wokring on %s ##' %query)
    for folder in os.listdir('outputs/%s' %outdir_name):
        if 'query' in folder:
            if str(k+1) == folder.split('_')[2]:
                print('WARNING: Existing directory for this query. Moving on.')
                ext_flag = True
                break
    if ext_flag == True:
        print('Exiting here. This is only a DEBUG message')
        continue

    pept = pept_seq[0]
    allele = pept_seq[1]
    length = len(pept)
        
    max_pos = -200
    pos_list = []
    
    anch_1, anch_2 = anch_dict[length]
    
    if allele in allele_ID.keys():
        pass
    elif allele[:9] in allele_ID.keys():
        allele = allele[:9]
    else:
        allele = allele[:6]
        
    for ID in IDD:
        if allele in IDD[ID]['allele']:                       ## Same Allele
            score = 0
            temp_pept = IDD[ID]['pept_seq']
            min_len = min([length, len(temp_pept)])
            score -= (abs(length - len(temp_pept)) * 20)      ## Penalty for gaps
            for (aa, bb) in zip(pept[:min_len], temp_pept[:min_len]):
                try:
                    score += MatrixInfo.pam30[aa, bb]
                except KeyError:
                    try:
                        score += MatrixInfo.pam30[bb, aa]
                    except KeyError:
                        #print('Broken peptide in IDD. Passing over.')
                        score = -50
                        pass

            if score > max_pos:
                max_pos = score
            pos_list.append((score, temp_pept, ID))
        else:
            pass
            
    max_list = []
    for pos in pos_list:
        if pos[0] == max_pos:
            max_list.append(pos)
    maxs.append(max_pos)
    maxsl.append(len(max_list))
    
    if len(max_list) == 0:
        non_modelled.append((query, pept, allele, "NA", "NA", "NA"))
        continue
    elif len(max_list) == 1:
        template = max_list[0]
        template_ID = template[2]
        template_pept = template[1]
    else:
        template = (choice(max_list))
        template_ID = template[2]
        template_pept = template[1]
    if print_results:
        print('####################################################')
        print('')
        print('Peptide:  ', template[1])
        print('')
        print('Pos:  ', template)
        print('')
        print('####################################################')

    ###################################
    #   CHANGING WORKING DIRECTORY
    ###################################

    sequences, empty_seqs = data_prep.get_pdb_seq([template_ID])
    
    outdir = ('outputs/%s/%s_%s' %(outdir_name, template_ID.lower(), query))
    try:
        os.mkdir(outdir)
    except FileExistsError:
        print('WARNING: Existing directory.')
        continue
    os.chdir(outdir)
    
    #Preparing template and target sequences for the .ali file, launching Muscle

    template_seqr = SeqRecord(Seq(sequences[0]['M'], IUPAC.protein), id=template_ID, name = 'HLA' + ID)
    target_seqr = SeqRecord(Seq(sequences[0]['M'], IUPAC.protein), id=query, name = 'HLA_' + query)
    SeqIO.write((template_seqr, target_seqr), "%s.fasta" %template_ID, "fasta")
    
    os.system('muscle -in %s.fasta -out %s.afa -quiet' %(template_ID, template_ID))
    os.system('rm %s.fasta' %template_ID)

    final_alifile_name = '%s.ali' %template_ID
    final_alifile = open(final_alifile_name, 'w')
    i = 0
    target_ini_flag = False
    template_ini_flag = False
    modeller_renum = 1
    for line in open('%s.afa' %template_ID, 'r'):
        #print(line)
        if line.startswith('>') and i == 0:
            final_alifile.write('>P1;' + line.split(' ')[0].strip('>') + '\n')
            final_alifile.write('structure:../../../data/PDBs/%s_MP.pdb:%s:M:%s:P::::\n' %(template_ID, str(sequences[0]['M_st_ID']), str(len(template_pept))))
            template_ini_flag = True
            i += 1
        elif line.startswith('>') and i == 1:
            final_alifile.write('/' + template_pept + '*')
            final_alifile.write('\n')
            final_alifile.write('\n>P1;' + line.split(':')[0].strip('>'))
            final_alifile.write('sequence:::::::::\n')
            target_ini_flag = True
        else:
            final_alifile.write(line.rstrip())
    final_alifile.write('/' + str(pept) + '*')
    final_alifile.close()
    
    if remove_temp_outputs:
        os.system('rm *.afa')
    
    #with open('instructions.txt', 'w') as instr_file:
    #    instr_file.write(template_ID + ' ' + str(1) + ' ' + str(9))
    
    '''
    os.system('pdb_splitchain ../../data/PDBs/%s_MP.pdb' %template_ID)
    for chain in ['M', 'P']:
        os.system('mv %s_MP_%s.pdb ../../data/PDBs/%s_MP_%s.pdb' %(template_ID, chain, template_ID, chain))
        os.system('pdb_reres -1 ../../data/PDBs/%s_MP_%s.pdb > ../../data/PDBs/%s_MP_%s.pdb.renum' %(template_ID, chain, template_ID, chain))
    os.system('pdb_merge ../../data/PDBs/%s_MP_*.pdb.renum > ../../data/PDBs/%s_MP_reres.pdb' %(template_ID, template_ID))
    os.system('rm -f data/PDBs/%s_MP_[A-Z].pdb' %template_ID)
    os.system('rm -f ../../data/PDBs/*.pdb.renum')
    '''
    
    with open('MyLoop.py', 'w') as myloopscript:
        MyL_temp = open('../../../modelling_scripts/MyLoop_template.py', 'r')
        for line in MyL_temp:
            
            if 'self.residue_range' in line:
                myloopscript.write(line %(anch_1 + 2, anch_2))
            elif 'SPECIAL_RESTRAINTS_BREAK' in line:
                break
            elif 'contact_file = open' in line:
                myloopscript.write(line %template_ID)
            else:
                myloopscript.write(line)
        MyL_temp.close()
    
    with open('cmd_modeller_ini.py', 'w') as modscript:
        cmd_m_temp = open('../../../modelling_scripts/cmd_modeller_ini.py', 'r')
        for line in cmd_m_temp:
            if 'alnfile' in line:
                modscript.write(line %final_alifile_name)
            elif 'knowns' in line:
                modscript.write(line %(template_ID, query))
            else:
                modscript.write(line)
        cmd_m_temp.close()
    
    os.popen('python3 cmd_modeller_ini.py').read()
    
    if remove_temp_outputs:
        os.system('rm cmd_modeller_ini.py')
    
    # Calculating all Atom contacts
    if "contact-chainID_allAtoms" not in os.listdir('../../../modelling_scripts'):
        os.popen('g++ ../../../modelling_scripts/contact-chainID_allAtoms.cpp -o ../../../modelling_scripts/contact-chainID_allAtoms').read()
    os.popen('../../../modelling_scripts/contact-chainID_allAtoms %s.ini %s > all_contacts_%s.list' %(query, cutoff, template_ID)).read()
    
    #Selecting only the anchors contacts
    
    real_anchor_2 = None
    anch_1_same = False
    anch_2_same = False
    
    if template_pept[anch_1-1] == pept[anch_1-1]:
        anch_1_same = True
    if anch_2 == len(pept):
        if template_pept[anch_2-1] == pept[anch_2-1]:
            anch_2_same = True
    else:
        if template_pept[-1] == pept[anch_2-1]:
            anch_2_same = True
    
    if anch_2 > len(template_pept):
        real_anchor_2 = (anch_2 + len(template_pept))
    
    ### Writing anchors contact list ###
    
    with open( 'all_contacts_%s.list' %template_ID, 'r') as contacts:
        with open('contacts_%s.list' %template_ID, 'w') as output:
            if real_anchor_2:                                                                     ### If the target peptide is longer than the templtate peptide
                for line in contacts:
                    #print(line[30:33])
                    p_aa_id = line.split("\t")[7]                                                 ### position id of the template peptide residue
                    p_atom = line.split("\t")[8]                                                  ### atom name of the template peptide residue
                    m_aa_id = (line.split("\t")[2]).split(' ')[0]
                    if anch_1_same == True:                                                       ### If the target anchor 1 residue is the same as the template anchor 1 residue
                        if int(p_aa_id) == anch_1:
                            output.write(line)
                    else:
                        if int(p_aa_id) == anch_1 and ('CA' in p_atom or 'CB' in p_atom):
                            output.write(line)
                    if anch_2_same == True:                                                       ### If the target anchor 2 residue is the same as the template anchor 2 residue
                        if int(p_aa_id) == real_anchor_2:
                            output.write(line[:30] + str(anch_2) + line[34:])
                    else:
                        if int(p_aa_id) == real_anchor_2 and ('CA' in p_atom or 'CB' in p_atom):
                            output.write(line[:30] + str(anch_2) + line[34:])
            else:
                for line in contacts:
                    #print(line.split("\t"))
                    p_aa_id = line.split("\t")[7]
                    p_atom = line.split("\t")[8]
                    m_aa_id = (line.split("\t")[2]).split(' ')[0]
                    if anch_1_same == True:                                                       ### If the target anchor 1 residue is the same as the template anchor 1 residue
                        if int(p_aa_id) == anch_1:
                            output.write(line)
                    else:
                        if int(p_aa_id) == anch_1 and ('CA' in p_atom or 'CB' in p_atom):
                            output.write(line)
                    if anch_2_same == True:                                                       ### If the target anchor 2 residue is the same as the template anchor 2 residue
                        if int(p_aa_id) == anch_2:
                            output.write(line)
                    else:
                        if int(p_aa_id) == anch_2 and ('CA' in p_atom or 'CB' in p_atom):
                            output.write(line)
                    #if (int(p_aa_id) == anch_1 or int(p_aa_id) == anch_2) and ('CA' in p_atom or 'CB' in p_atom):
                    #        output.write(line)
    
    if remove_temp_outputs:
        os.system('rm all_contacts_%s.list' %template_ID)
    
    with open('MyLoop.py', 'w') as myloopscript:
        MyL_temp = open('../../../modelling_scripts/MyLoop_template.py', 'r')
        for line in MyL_temp:
            if 'self.residue_range' in line:
                myloopscript.write(line %(anch_1 + 2, anch_2))
            elif 'contact_file = open' in line:
                myloopscript.write(line %template_ID)
            else:
                myloopscript.write(line)
        MyL_temp.close()
        
    #    with open('instructions.txt', 'w') as instr_file:
    #        instr_file.write(template_ID + ' ' + str(anch_1) + ' ' + str(anch_2) + ' ' + str(modeller_renum))
    
    #Finally launching Modeller. Hopefully.
    
    t1 = time.time()
    
    with open('cmd_modeller.py', 'w') as modscript:
        cmd_m_temp = open('../../../modelling_scripts/cmd_modeller_template.py', 'r')
        for line in cmd_m_temp:
            if 'alnfile' in line:
                modscript.write(line %final_alifile_name)
            elif 'knowns' in line:
                modscript.write(line %(template_ID, query))
            else:
                modscript.write(line)
        cmd_m_temp.close()
    
    os.popen('python3 cmd_modeller.py > modeller.log').read()
    
    t2 = time.time()
    tf = t2 - t1
    
    print('The modelling took %i seconds' %tf)

    if tf < 3:
        non_modelled.append((query, pept, allele, template_ID, template_pept, IDD[template_ID]['allele']))
    
    os.chdir('../../../')

with open('outputs/%s/non_modelled.csv' %outdir_name, 'wt') as outfile:
    tsv_writer = csv.writer(outfile, delimiter='\t')
    tsv_writer.writerow(['QUERY', 'NEOANTIGEN', 'QUERY ALLELE', 'TEMPLATE ID', 'TEMPLATE PEPTIDE', 'TEMPLATE ALLELE'])
    for query in non_modelled:
        tsv_writer.writerow(query)
