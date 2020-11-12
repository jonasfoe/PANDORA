#!/usr/bin/env python
# Farzaneh Meimandi Parizi
#  4-Mar-2020 11:57

import sys
from Bio.PDB import PDBParser

ref_pdbf = sys.argv[1]
output = open('ref.lzone', 'w')

P = PDBParser(QUIET=1)
structure = P.get_structure('r', ref_pdbf)
for chain in structure.get_chains():
    if chain.id == 'M' or chain.id == 'N':
        output.write('zone %s2-%s172:%s2-%s172\n' %(chain.id, chain.id, chain.id, chain.id))
    elif chain.id == 'P':
        output.write('fit\n')
        for residue in chain:
            if residue.id[2] == ' ':
                output.write('rzone %s%s-%s%s\n' %(chain.id, str(residue.id[1]), chain.id, str(residue.id[1])))
    else:
        raise Exception('Unrecognized chain ID, different from M, N or P. Please check your file')

output.close()