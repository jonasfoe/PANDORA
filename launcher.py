###    ###
from modelling_scripts import data_prep
#from modelling_scripts import cmd_modeller
import pickle
from Bio import SeqIO
import subprocess
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import IUPAC
import os
import time
from random import choice

IDD = data_prep.imgt_retrieve_clean('data/final_mhc1_3d_structure_data_with_pdb_ids.tsv')

## TODO:
## Retrieve IDs : Alleles
## Read user's input (seq and allele)
## Select template structure and get its sequence
## Compare User's input with same allele sequences (select with identity the best one)

### Retriving Dictionary with PDB IDs and chain lengths ###
#IDD_file = open('data/IDs_ChainsCounts_dict.pkl', 'rb')
#IDD = pickle.load(IDD_file)
#IDD_file.close()

### Organizing Allele IDs in a dictionary ###
allele_ID = {}
for key in IDD:
    try:
        allele_ID[IDD[key]['allele']].append(key)
    except KeyError:
        allele_ID[IDD[key]['allele']] = [key]

### Retriving target allele and sequence file ###
        
print('##############################')
print('Please enter your allele name. You can choose between the ones listed below')
print('##############################')
print('')
print('')
print(allele_ID.keys())
#allele = input()
#allele, inseq_file = 'FLA-E*01801', 'data/5xmf.fasta'
allele, inseq_file = 'H2-Kb', 'data/3roo.fasta'

print('##############################')
print('Please select your sequence file.')
print('##############################')
print('')

#inseq_file = 'data/5xmf.fasta'
#inseq_file = 'data/1tom.fasta'
inseqs = list(SeqIO.parse(inseq_file, 'fasta'))
A_target = inseqs[0]
P_target = inseqs[1]

### Producing a Fasta file for each putetive template-target alignment ###
sequences = data_prep.get_pdb_seq(allele_ID[allele])
ID_seqs_dict = {}
for i, ID in enumerate(allele_ID[allele]):
    template = SeqRecord(Seq(sequences[i]['A'], IUPAC.protein), id=ID, name = allele + ID)
    SeqIO.write((template, A_target), "data/FASTAs/%s.fasta" %ID, "fasta")
    ID_seqs_dict[ID] = (sequences[i]['P'])

### Identifying the template ID and its peptide sequence ### 
if len(allele_ID[allele]) == 1:   ### In case we have only one template for this allele ###
    template_ID = allele_ID[allele][0]
    peptide_seq = ID_seqs_dict[template_ID]
    #subprocess.check_call(['muscle', '-in %s.fasta -clw' %template_ID])
    t1 = time.time()
    os.system('muscle -in data/FASTAs/%s.fasta -out data/Alignments/%s.afa' %(ID, ID))
    tf = time.time() - t1
    print('IT TOOK: ')
    print(tf)
else:                             ### In case we have multiple templates for this allele ###
    score_dict = {}
    max_id = 0
    putative_templates = []
    for ID in allele_ID[allele]:
        alifile = 'data/Alignments/%s.afa' %ID
        muscle_commands = ['muscle', '-in', 'data/FASTAs/%s.fasta' %ID, '-out', '%s' %alifile]
        #os.system('muscle -in data/FASTAs/%s.fasta -out %s' %(ID, alifile))
        subprocess.check_call(muscle_commands)
        os.system('rm data/FASTAs/%s.fasta' %ID)
        aligned = list(SeqIO.parse(alifile, 'fasta'))
        id_count = 0
        for x, y in zip((aligned[0].seq), str(aligned[1].seq)):
            if x == y:
                id_count += 1
            else:
                pass
        if id_count > max_id:
            max_id = id_count
        score_dict[ID] = id_count
        print('ID COUNT:  ', id_count)
    for key in score_dict:
        if score_dict[key] == max_id:
            putative_templates.append(key)
        else:
            os.system('rm data/Alignments/%s.afa' %key)
    templates_dict = {}
    for i, template in enumerate(putative_templates):
        templates_dict[i] = template
    print('##############################')
    print('Please select one template between the ones listed below')
    print('##############################')
    print('')
    print('')
    print(templates_dict)
    template_ID = templates_dict[int(input())]
    #template_ID = choice(putative_templates)
    peptide_seq = ID_seqs_dict[template_ID]

### Writing a final .ali file with Template sequence / template pept sequence ; Target sequence / target pept sequence ###
final_alifile_name = 'data/Alignments/%s.ali' %template_ID
final_alifile = open(final_alifile_name, 'w')
i = 0
for line in open('data/Alignments/%s.afa' %template_ID, 'r'):
    print(line)
    if line.startswith('>') and i == 0:
        final_alifile.write(line)
        final_alifile.write('structure:%s_AP.pdb:1:A:9:P::::\n' %template_ID)
        i += 1
    elif line.startswith('>') and i == 1:
        final_alifile.write('/' + peptide_seq)
        final_alifile.write('\n')
        final_alifile.write('\n'+ line)
        final_alifile.write('sequence:::::::::\n')
    else:
        final_alifile.write(line.rstrip())
final_alifile.write('/' + str(P_target.seq))
final_alifile.close()
            
#os.system('/usr/bin/python2.7 modelling_scripts/cmd_modeller.py %s %s >3ROO:A|PDBID|CHAIN|SEQUENCE' %(final_alifile_name, template_ID))
        