# pMHC_modelling

## Requirements

Python 3 (Prefered)
BioPython
Modeller 9.23 or later
pdb_tools
muscle
profit (only for RMSD calculation)
pdb2sql (only for RMSD calculation)


## mhc_model.py
Updated version of old_launcher_0.1.py.
Contact list generated from modeller .ini file.
All outputs (even temporary files) are now generated in the query output directory.

## neoantigen_model.py
Updated version of old_launcher_0.2.py.
Contact list generated from modeller .ini file.
All outputs (even temporary files) are now generated in the query output directory.

Takes as input a csv file and the IDD dictionary, models every neoantigen in the csv.
Parallelization in development.

## data/csv_pkl_files/IDs_ChainsCount_dict.pkl
Pickle file generated by data_prep.imgt_retrieve_clean() .
Contains two dictionaries:
IDD (IDs dictionary), crucial for both the modelling pipelines;
bad_IDs , dictionary containing all the IDs that did not resulted in a .pdb file. Reason of exclusion is reported as an error number in the dictionary, the error explanation are available in data_prep.imgt_retrieve_clean()

## old_launcher_0.1.py
First version, previously named launcher_0.1.py . Given a target fasta sequence, an allele, a template and the anchors positions runs cmd_modeller.

## launcher_0.2.py
Previously named launcher_0.2.py . Designed for modelling Neoantigens from 1,948 paper on Cartesius.
