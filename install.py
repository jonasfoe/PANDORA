import os

try:
    os.mkdir('./PANDORA_files')
    os.mkdir('./PANDORA_files/data')
    os.mkdir('./PANDORA_files/data/csv_pkl_files')
    os.mkdir('./PANDORA_files/data/PDBs')
    os.mkdir('./PANDORA_files/data/PDBs/pMHCI')
    os.mkdir('./PANDORA_files/data/PDBs/pMHCII')
    os.mkdir('./PANDORA_files/data/PDBs/Bad')
    os.mkdir('./PANDORA_files/data/PDBs/Bad/pMHCI')
    os.mkdir('./PANDORA_files/data/PDBs/Bad/pMHCII')
    os.mkdir('./PANDORA_files/data/PDBs/IMGT_retrieved/')
    os.mkdir('./test/test_data/PDBs/Bad')
    os.mkdir('./test/test_data/PDBs/Bad/pMHCI')
    os.mkdir('./test/test_data/PDBs/Bad/pMHCII')
    os.mkdir('./test/test_data/csv_pkl_files')
except OSError:
    pass



# netMHCII Pan install

wd = os.path.dirname(os.path.abspath(__file__))
# Changing working directory
os.chdir(wd + '/netMHCIIpan-4.0')
# Downloading data folder for netMHCIIpan
os.system('wget https://services.healthtech.dtu.dk/services/NetMHCIIpan-4.0/data.tar.gz')
# Uncompressing
os.system('gunzip data.tar.gz')
os.system('tar -xvf data.tar')
# remove tar file
os.system('rm data.tar')
# Make sure the tmp directory is created
if not os.path.exists('tmp'):
    os.mkdir('tmp')

# Edit paths in the netMHCIIpan script
netMHCIIpan_script = []
with open('netMHCIIpan') as f:
    for line in f:
        netMHCIIpan_script.append(line)
with open('netMHCIIpan', 'w') as f:
    for line in netMHCIIpan_script:
        if 'setenv\tNMHOME' in line:
            f.write('setenv\tNMHOME\t' + wd + '/netMHCIIpan-4.0\n')
            f.write('setenv\tTMPDIR\t' + wd + '/netMHCIIpan-4.0/tmp\n')
        else:
            f.write(line)

# netMHC Pan install

os.chdir(wd + '/netMHCpan-4.1')
# Downloading data folder for netMHCIIpan
os.system('wget https://services.healthtech.dtu.dk/services/NetMHCpan-4.1/data.tar.gz ')
# Uncompressing
os.system('gunzip data.tar.gz')
os.system('tar -xvf data.tar')
# remove tar file
os.system('rm data.tar')
# Make sure the tmp directory is created
if not os.path.exists('tmp'):
    os.mkdir('tmp')

# Edit paths in the netMHCIIpan script
netMHCpan_script = []
with open('netMHCpan') as f:
    for line in f:
        netMHCpan_script.append(line)
with open('netMHCpan', 'w') as f:
    for line in netMHCpan_script:
        if 'setenv\tNMHOME' in line:
            f.write('setenv\tNMHOME\t' + wd + '/netMHCpan-4.1\n')
            f.write('setenv\tTMPDIR\t' + wd + '/netMHCpan-4.1/tmp\n')
        else:
            f.write(line)

# Changing working directory back
os.chdir(wd)

os.popen("alias KEY_MODELLER='XXXX'").read()
os.popen("conda install -y -c salilab modeller").read()
os.popen("conda install -y -c conda-forge biopython").read()
os.popen("conda install -y dill").read()
os.popen("conda install -y -c bioconda muscle").read()
os.popen("pip install pdb-tools").read()
os.popen("pip install pdb2sql").read()

os.popen("pip install -e ./").read()
