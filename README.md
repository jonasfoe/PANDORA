# PANDORA
### Peptide ANchored mODelling fRAmework for peptide-MHC complexes


![PANDORA](https://github.com/DarioMarzella/PANDORA/blob/issue_90/flowchart_pMHCI.png?raw=true)

### Contents

- [Overview](#overview)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Tutorial](#tutorial)
- [Code Design](#diagram)
- [Output File structure](#output)
- [License](./LICENSE)
- [Issues](#issues)

## Overview

PANDORA is anchor restrained modelling pipeline for generating peptide-MHC structures.

PANDORA contains multiple functions to pre-process data and it's able to exploit different crucial domain knowledge provided by the user to guide the modelling.


## Dependencies
PANDORA requires MODELLER, python and some python libraries to be installed. You can install the dependencies via the installation process in PANDORA or install from source.

Installation from source provides you the latest version(recommended).

- [Python](https://www.python.org/) 3
- conda
- pip3
- [BioPython](https://anaconda.org/conda-forge/biopython)
- [muscle](https://anaconda.org/bioconda/muscle)
- [Modeller](https://anaconda.org/salilab/modeller) 9.23 or later
- [pdb_tools](https://github.com/haddocking/pdb-tools)
- [pdb2sql](https://github.com/DeepRank/pdb2sql) (Optional, only for RMSD calculation)
- [NetMHCpan](https://services.healthtech.dtu.dk/software.php) (Optional, only if user wills to predict peptide:MHC class I anchors)
- [NetMHCIIpan](https://services.healthtech.dtu.dk/software.php) (Optional, only if user wills to predict peptide:MHC class II anchors)

## Installation

#### 1. Setup MODELLER License:
Prior to PANDORA installation, you need to first activate MODELLER's license. Please request MODELLER license at: https://salilab.org/modeller/registration.html

Replace XXXX with your MODELLER License key and run the command:
```
alias KEY_MODELLER='XXXX'
```

#### 2. Install PANDORA

Clone the repository:
```
git clone https://github.com/DarioMarzella/PANDORA.git
```
Enter the cloned directory and then install all the dependencies!
```
cd PANDORA

python install.py
```
#### 3. (Optional) Install NetMHCpan and/or NetMHCIIpan

PANDORA lets the user if he wills to predict peptide's anchor residues instead of using conventional predefined anchor residues for each allele.
In that case you need to install NetMHCpan (for peptide:MHC class I) and/or NetMHCIIpan (for peptide:MHC class II).
You can install from the [source](https://services.healthtech.dtu.dk/software.php) or simply run:
```
python netMHCpan_install.py
```

## Tutorial


#### Example 1 : Generating a peptide:MHC complex given the peptide sequence
PANDORA requires these information to generate models:
- Peptide sequence
- MHC allele

A. The database of all templates need to be generated (retrieving pMHC PDBs from IMGT). 
   You can save the database with your given name, to skip the downloading phase for later usage.
   
B. Creating a Template object based on the given information

C. Generating n number of pMHC models

```
from PANDORA.PMHC import PMHC
from PANDORA.Pandora import Pandora
from PANDORA.Database import Database

## A. Create local Database
db = Database.Database()
db.construct_database(save='pandora.Database')     

## B. Create Target object
target = PMHC.Target(
    dallele_type='HLA-A*0201'
    peptide='LLFGYPVYV',
    MHC_class='I'
    anchors = [2,9]

## C. Perform modelling
mod = Pandora.Pandora(target, db)
mod.model(n_loop_models=20, seq_based_templ_selection=False)  # Generates 20 models
```

#### Example 2 : Reproducing a pMHCI complex with known experimental PDB structure

If the target experimental structure is available, you can provide the PDB ID and set *benchmark=True* to calculate L-RMSD value.

```
from PANDORA.PMHC import PMHC
from PANDORA.Pandora import Pandora
from PANDORA.Database import Database

## A. Load pregenerated database of all pMHC PDBs
db = Database.load('pandora.Database')  

## B. Create Target object
target = PMHC.Target('1A1M',
    db.MHCI_data['1A1M'].allele_type,
    db.MHCI_data['1A1M'].peptide,
    M_chain_seq = db.MHCI_data['1A1M'].M_chain_seq,
    anchors = db.MHCI_data['1A1M'].anchors)

## C. Perform modelling
mod = Pandora.Pandora(target, db)
mod.model(n_mloop_odels=20, seq_based_templ_selection=True, benchmark=True)  
```

#### Example 3: Modelling of many peptide cases
PANDORA can modell more than one peptide, in parallel. You need to provide the following petide information in a csv file, including:
- Peptide sequence,  Allele name, PDB ID (Optional, only used when reproducing models of known peptide:MHC structures)

```
from PANDORA.Wrapper import Wrapper

## A. Load pregenerated database of all pMHC PDBs
db = Database.load('pandora.Database')

## B. Create the wrapper object
wrap =  Wrapper()

## C. Create all Target Objects
wrap.create_targets('datafile.tsv', db, MHC_class='II')

## C. Perform modelling
wrap.run_pandora(num_cores=128)
```
## Diagram
PANDORA is designed in an Object-oriented programming. This provides a comprehensible and user-friendly framework.

Pandora class: represents a user defined modelling case(s)

[Diagram](https://github.com/DarioMarzella/PANDORA/blob/issue_90/class_diagram.png?raw=true)

## Output

The following file structure is prepared to store the Database, PDB files and output data.

Please note that the modelling results consisting genretaed models are stored in *./PANDORA_files/data/outputs/* directory

```
PANDORA_files
  └── data
     ├── csv_pkl_files            Generated Database and csv files containing peptide data to be modelled
     │   └── mhcseqs
     ├── outputs                  Directory to save output (Modelled cases, restraints, alignment file, log file, etc.)
     └── PDBs                     PDB files downloaded from IMGT
           ├── Bad                Problematic PDB files deleted from the databse
           ├── IMGT_retrieved     
           ├── pMHCI              
           └── pMHCII             
```

## Issues

If you have questions or find a bug, please report the issue in the [Github issue channel](https://github.com/DarioMarzella/PANDORA/issues).
