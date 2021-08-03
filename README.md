# PANDORA
(Peptide ANchored mODelling fRAmework)

### Contents

- [Overview](#Overview)
- [Installation](#Installation)
- [Quick Tutorial](#Tutorial)
- [License](./LICENSE)
- [Issues](#Issues)

## Overview

PANDORA is a MODELLER-based, anchor restrained modelling pipeline for peptide-MHC structures.

PANDORA contains multiple functions to pre-process data and it's able to exploit different crucial domain knowledge provided by the user to guide its modelling.

## Installation

To install PANDORA and all the required dependencies, ```pip3``` and conda are required.
Also, being based on MODELLER, Pandora needs a functioning MODELLER installation. Please request your MODELLER license at: https://salilab.org/modeller/registration.html
To create all the required directories and install all dependencies:
1. set:
> alias KEY_MODELLER='XXXX'
where 'XXXX' is your MODELLER license key
2. run:
> python install.py


### Dependencies

Python 3
BioPython
Modeller 9.23 or later
pdb_tols
muscle
pdb2sql (only for RMSD calculation)


## Tutorial

```
from PANDORA.PMHC import PMHC
from PANDORA.Pandora import Pandora
from PANDORA.Database import Database

db = Database.Database()
db.construct_database()

target = PMHC.Target('1A1M',
    db.MHCI_data['1A1M'].allele_type,
    db.MHCI_data['1A1M'].peptide,
    M_chain_seq = db.MHCI_data['1A1M'].M_chain_seq,
    anchors = db.MHCI_data['1A1M'].anchors)

mod = Pandora.Pandora(target, db)
mod.model(n_models=20, stdev=0.1, seq_based_templ_selection=True, benchmark=False)
```

## Issues

If you have questions or find a bug, please report the issue in the [Github issue channel](https://github.com/DarioMarzella/PANDORA/issues).
