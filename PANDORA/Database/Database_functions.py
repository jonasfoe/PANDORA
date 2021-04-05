import os
import urllib.request
import urllib.parse
from copy import deepcopy
from Bio.PDB import PDBParser
from Bio.PDB import PDBIO
from Bio.PDB import parse_pdb_header
import gzip
import shutil
import PANDORA
from PANDORA.Contacts import Contacts
from Bio import SeqIO
from PANDORA.PMHC import PMHC
from Bio.PDB import NeighborSearch
from Bio.SeqUtils import seq1
from Bio.PDB import Chain
from string import ascii_uppercase


def download_unzip_imgt_structures(data_dir = PANDORA.PANDORA_data, del_inn_files = True, del_kabat_files = True):
    ''' Downloads the complete structural dataset

    Args:
        data_dir: (string) path of data directory
        del_inn_files: (bool) if True (default) deletes all inn files
        del_kabat_files: (bool) if True (default) deletes all kabat files

    '''

    # Changing working directory
    os.chdir(data_dir + '/PDBs/IMGT_retrieved/')
    # Downloading IMGT dataset
    os.system('wget http://www.imgt.org/download/3Dstructure-DB/IMGT3DFlatFiles.tgz')
    # Uncompressing
    os.system('gunzip IMGT3DFlatFiles.tgz')
    os.system('tar -xvf IMGT3DFlatFiles.tar')

    try:
        os.system('rm IMGT3DFlatFiles.tgz')
    except:
        pass
    os.system('rm IMGT3DFlatFiles.tar')
    # Removing non-PDB files
    if del_inn_files:
        os.system('rm IMGT3DFlatFiles/*.inn.gz')
    if del_kabat_files:
        os.system('rm IMGT3DFlatFiles/*.prot.gz')
    #os.chdir('../../../../')


def download_ids_imgt(ReceptorType, data_dir = PANDORA.PANDORA_data, out_tsv = False):
    ''' Querys IMGT with the ReceptorType for PDBs.

    Args:
        ReceptorType: (string) Receptor query for IMGT: 'MH1' or 'MH2'
        data_dir: (bool/string) if not False, produces a tsv file names as out_tsv
        out_tsv: (bool/string) if not False, produces a tsv file names as out_tsv

    Returns: (list) Returns the list of IDs provided by IMGT.

    '''

    #out_tsv = 'pMHCI_IDs_alleles_from_IMGT.tsv'
    params = { 'ReceptorType' : ReceptorType,
             'type-entry': 'PDB'}

    url = "http://www.imgt.org/3Dstructure-DB/cgi/3Dquery.cgi"

    data = urllib.parse.urlencode(params)
    data = data.encode('ascii') # data should be bytes
    req = urllib.request.Request(url, data)

    with urllib.request.urlopen(req) as response:
        text = response.read().decode('utf-8')
        text = text.splitlines()

    IDs_list = []
    IDs_list = [x for x in text if 'href' in x and 'pdbcode' in x]
    IDs_list = [x.split('"') for x in IDs_list]
    IDs_list = [x[3][-4:] for x in IDs_list]

    if out_tsv:
        outfile = open(data_dir + '/csv_pkl_files/' + out_tsv, 'w')
        outfile.write(ReceptorType + ' IMGT IDs\n')
        for ID in IDs_list:
            outfile.write(ID + '\n')
        outfile.close()

    return IDs_list


def get_chainid_alleles_MHCI(pdbf):
    '''    Takes as input an IMGT preprocessed PDB file of p:MHC I.
           Returns a dictionary containing alleles andrelative identity scores for each
           G-domain in the given pdb from the REMARK.

    Args:
        pdbf: (string) path to IMGT pdb file

    Returns: (dict) MHCI alleles

    '''

    # test: multiple chains 3GJG, multiple alleles 1AO7
    ### Parsing file and extracting remarks
    with open(pdbf) as infile:
        remarks = []
        for line in infile:
            if line.startswith('REMARK 410'):
                row = [x for x in line.rstrip().split(' ') if x != '']
                del row[:2]
                remarks.append(row)
    remarks = [x for x in remarks if x != []]

    ### Dividing each remark section into a chains dictionary
    chains = {}
    flag = False
    for row in remarks:
        if row[0] == 'Chain' and row[1] == 'ID' and len(row) == 4:
            chainID = row[2][-1]
            chains[chainID] = []
            chains[chainID].append(row)
            flag = True
        elif flag == True:
            chains[chainID].append(row)

    ### Extracting MHC I Alpha chains
    mhc_a = {}  # MHC I Alpha
    for chain in chains:
        try:
            if chains[chain][1][3] == 'I-ALPHA':
                mhc_a[chain] = chains[chain]
        except:
            pass

    ### Extracting alleles info
    mhc_a_alleles = {}
    for chain in mhc_a:
        G_dom_alleles = {'G-ALPHA1': [], 'G-ALPHA2': []}
        key = False
        for row in mhc_a[chain]:
            if row[0] == 'G-DOMAIN':
                try:
                    if row[3] == 'description' and row[4] == 'G-ALPHA1':
                        key = 'G-ALPHA1'
                    elif row[3] == 'description' and row[4] == 'G-ALPHA2':
                        key = 'G-ALPHA2'
                    elif key:
                        if row[2] == 'gene' and row[3] == 'and' and row[4] == 'allele':
                            G_dom_alleles[key] += row[5:]
                        else:
                            key = False
                except IndexError:
                    pass
        mhc_a_alleles[chain] = deepcopy(G_dom_alleles)

    mhc_a_alleles_percs = {}
    for chain in mhc_a_alleles:
        mhc_a_alleles_percs[chain] = {}
        for key in mhc_a_alleles[chain]:
            mhc_a_alleles_percs[chain][key] = {}
            ### Allele info are always given with four elements: Gender, Spieces, Allele, Percentage
            for block in range(int(len(mhc_a_alleles[chain][key]) / 4)):
                allele = mhc_a_alleles[chain][key][2 + (4 * block)]
                perc = float(
                    mhc_a_alleles[chain][key][3 + (4 * block)].replace('(', '').replace('%)', '').replace(',', ''))
                mhc_a_alleles_percs[chain][key][allele] = perc

    return mhc_a_alleles_percs


def get_chainid_alleles_MHCII(pdbf):
    ''' Takes as input an IMGT preprocessed PDB file of p:MHC II.
        Returns a dictionary containing alleles andrelative identity scores for each
        G-domain in the given pdb from the REMARK.

    Args:
        pdbf: (string) path to IMGT pdb file

    Returns: (dict) MHCI alleles

    '''
    # test: multiple chains 3GJG, multiple alleles 1AO7
    ### Parsing file and extracting remarks
    with open(pdbf) as infile:
        remarks = []
        for line in infile:
            if line.startswith('REMARK 410'):
                row = [x for x in line.rstrip().split(' ') if x != '']
                del row[:2]
                remarks.append(row)
    remarks = [x for x in remarks if x != []]

    ### Dividing each remark section into a chains dictionary
    chains = {}
    flag = False
    for row in remarks:
        if row[0] == 'Chain' and row[1] == 'ID' and len(row) == 4:
            chainID = row[2][-1]
            chains[chainID] = []
            chains[chainID].append(row)
            flag = True
        elif flag == True:
            chains[chainID].append(row)

    ### Extracting MHC II Alpha and Beta chains
    mhc_a = {}  # MHC II Alpha
    mhc_b = {}  # MHC II Beta
    for chain in chains:
        try:
            if chains[chain][1][3] == 'II-ALPHA':
                mhc_a[chain] = chains[chain]
            elif chains[chain][1][3] == 'II-BETA':  # or chains[chain][1][3] == 'II-BETA':
                mhc_b[chain] = chains[chain]
        except:
            pass

    ### Extracting alleles info
    mhc_a_alleles = {x: [] for x in mhc_a}
    mhc_b_alleles = {x: [] for x in mhc_b}

    for chain in mhc_a:
        key = False
        for row in mhc_a[chain]:
            if row[0] == 'G-DOMAIN':
                try:
                    if row[3] == 'description' and row[4] == 'G-ALPHA':
                        key = 'G-ALPHA'
                    elif key:
                        if row[2] == 'gene' and row[3] == 'and' and row[4] == 'allele':
                            mhc_a_alleles[chain] += row[5:]
                        else:
                            key = False
                except IndexError:
                    pass

    for chain in mhc_b:
        key = False
        for row in mhc_b[chain]:
            if row[0] == 'G-DOMAIN':
                try:
                    if row[3] == 'description' and row[4] == 'G-BETA':
                        key = 'G-BETA'
                    elif key:
                        if row[2] == 'gene' and row[3] == 'and' and row[4] == 'allele':
                            mhc_b_alleles[chain] += row[5:]
                        else:
                            key = False
                except IndexError:
                    pass

    return {'Alpha': mhc_a_alleles, 'Beta': mhc_b_alleles}


def get_resolution(pdbf):
    ''' Returns the resolution in Angstrom from the given pdb

    Args:
        pdbf (str): path to the pdb file

    Returns:
        resolution (float): resolution of the model, in Angstrom

    '''
    header = parse_pdb_header(pdbf)
    resolution = header['resolution']
    return resolution


def change_sep_in_ser(pdb_file):
    '''

    Args:
        pdb_file:

    Returns:

    '''

    with open(pdb_file) as f:
        infile = []
        for line in f:
            infile.append(line)

    with open(pdb_file, 'w') as f:
        for line in infile:
            # pss
            l = [x for x in line.split(' ') if x != '']
            if line.startswith('ATOM') or line.startswith('HETATM'):
                if ('SEP' in l[3] or 'SEP' in l[2]) and l[2] not in ['P', 'O1P', 'O2P', 'O3P', 'HA', 'HB2',
                                                                     'HB3']:  # Lines to keep
                    f.write(line.replace('HETATM', 'ATOM  ').replace('SEP', 'SER'))
                elif ('SEP' in l[3] or 'SEP' in l[2]) and l[2] in ['P', 'O1P', 'O2P', 'O3P', 'HA', 'HB2',
                                                                   'HB3']:  # Lines to delete
                    pass
                elif ('F2F' in l[3] or 'F2F' in l[2]) and l[2] not in ['F1', 'F2']:
                    f.write(line.replace('HETATM', 'ATOM  ').replace('F2F', 'PHE'))
                elif ('F2F' in l[3] or 'F2F' in l[2]) and l[2] in ['F1', 'F2']:
                    pass
                elif ('CSO' in l[3] or 'CSO' in l[2]) and l[2] not in ['OD']:  # Lines to keep
                    f.write(line.replace('HETATM', 'ATOM  ').replace('CSO', 'CYS'))
                elif ('CSO' in l[3] or 'CSO' in l[2]) and l[2] in ['OD']:  # Lines to delete
                    pass
                else:
                    f.write(line)
            else:
                f.write(line)


def replace_chain_names(chains, pdb, replacement_chains=['M', 'N', 'P']):
    ''' Replace chain names by another chain name in a bio.pdb object

    Args:
        chains: (list) chains to replace
        pdb: bio.pdb object
        replacement_chains: (list) replacement names (in order of chains to replace)

    Returns: bio.pdb object with changed chain names

    '''
    # First give them a greek letter, so names that are already present are taken care of.
    intermediate_chains = ['𝜶','𝜷','𝜸','𝜹','𝜺','𝜻','𝜼','𝜽','𝜾','𝜿','𝝀','𝝁','𝝂','𝝃','𝝄','𝝇','𝝈','𝝊','𝝋','𝝌','𝝎']
    for i in chains:
        for chain in pdb.get_chains():
            if chain.id == i:
                chain.id = intermediate_chains[chains.index(i)]

    # for i in chains:
    for chain in pdb.get_chains():
        if chain.id == intermediate_chains[intermediate_chains.index(chain.id)]:
            chain.id = replacement_chains[intermediate_chains.index(chain.id)]

    return pdb


def renumber(pdb):
    ''' Renumbers the pdb. Each chain starts at 1

    Args:
        pdb: Bio.PDb object

    Returns: Bio.PDb object with renumbered residues

    '''

    for chain in pdb.get_chains():
        nr = 1
        for res in chain:
            res.id = ('X', nr, res.id[2])
            nr += 1
    for chain in pdb.get_chains():
        for res in chain:
            res.id = (' ', res.id[1], ' ')

    return pdb


def write_pdb(pdb, out_path, get_header_from=False):
    ''' Write bio.pdb object to file, can use the header of the original pdb (bio.pdb cant remember file headers)

    Args:
        pdb: bio.pdb object
        out_path: (string) output path of pdb file
        get_header_from: (string) get the header from another pdb file

    Returns:

    '''

    def get_head_and_remarks(pdb_file):
        ''' Get the head and remarks of an IMGT pdb file

        Args:
            pdb_file: (string) path to original pdb file

        Returns: (list) list of lines

        '''
        # Take all lines of the pdb file up until the "ATOM" part
        with open(pdb_file) as infile:
            header = []
            for line in infile:
                if line.startswith('ATOM'):
                    break
                header.append(line[:-1])

        return header

    def line_prepender(filename, line):
        ''' Add a line in front of a file

        Args:
            filename: (string) filepath
            line: (string) line to prepend

        '''

        with open(filename, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line.rstrip('\r\n') + '\n' + content)

    # If the original pdb file path is given, use that header and paste it before the ATOM lines
    if get_header_from:
        header = get_head_and_remarks(get_header_from)  # get the header

    # Write pdb
    io = PDBIO()
    io.set_structure(pdb)
    io.save(out_path)

    if get_header_from: # Write the original header to pdb file
        for line in header[::-1]:
            line_prepender(out_path, line)


def unzip_pdb(ID, indir, outdir):
    ''' Unzips a pdb, move it to another directory and return the filepath

    Args:
        ID: (string) pdb id
        indir:  (string) location of pdb.gz files
        outdir:  (string) output location

    Returns: (string) path to unzipped pdb file

    '''

    ## unzip pdb and move to outdir
    try:
        with gzip.open('%s/IMGT-%s.pdb.gz' % (indir, ID), 'rb') as f_in:
            # Check if the file is empty
            if f_in.seek(0, whence=2) == 0:
                raise Exception('File is empty')

        with gzip.open('%s/IMGT-%s.pdb.gz' % (indir, ID), 'rb') as f_in:
            with open('%s/%s.pdb' % (outdir, ID), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except FileNotFoundError:
        print('ERROR TYPE #1: File not found. %s' % ID)
    return '%s/%s.pdb' % (outdir, ID)


def find_peptide_chain(pdb, min_len=6, max_len=26):
    ''' Find the pdb chain that is most likely the peptide based on its size

    Args:
        pdb: Bio.PDB object
        min: (int) minimal peptide length to consider
        max: (int) maximal peptide length to consider

    Returns: (str): Most likely chain that is the peptide

    '''

    # Find most likely peptide chain: first chain to be 7 < len(chain) < 25
    pept_chain = []
    for chain in pdb.get_chains():
        if len(chain) > min_len and len(chain) < max_len:
            # print(chain.id)# Is this chain between 7 and 25?
            heteroatoms = False
            for res in chain:
                # print(res.id)
                if res.id[0] != " " and res.id[0] != 'W':  # Check if a res in this chain is a heteroatom
                    print('\tHeteroatoms in peptide chain')
                    heteroatoms = True
                    break
            if heteroatoms == False:  # If all residues are oke, add this to the list of peptide chains
                pept_chain.append(chain.id)

    pept_chain = pept_chain[0]  # Take the first pept chain. If there are multiple, they are probably duplicates

    return pept_chain


def remove_irregular_chains(pdb, chains_to_keep):
    ''' Removes all chains that you don't specify to keep

    Args:
        pdb: Bio.PDB object
        chains_to_keep: list of strings: ['A', 'C']

    Returns: Bio.PDB object

    '''
    for _ in range(len([c for c in pdb.get_chains()])):
        for i in pdb.get_chains():
            for model in pdb:
                for chain in model:
                    if chain.id not in chains_to_keep or chain.id in [' ','','  ','_'] + list(range(1,20)):
                        model.detach_child(chain.id)

    return pdb


def remove_duplicated_chains(pdb):
    ''' In very rare cases, PDBParser duplicates the same chain multiple times. If that happens, this function removes
        all duplicates

    Args:
        pdb: Bio.PDB object

    Returns: Bio.PDB object

    '''
    # If there are multipel models, remove them so the pdb contains only one: pdb[0]
    if len([model.id for model in pdb]) > 1:
        # Remove all extra models that are not pdb[0]
        for _ in range(len([i.id for i in pdb])):
            for model in pdb:
                if model.id > 0:
                    pdb.detach_child(model.id)

    # Find all unique chains
    chains_to_keep = sorted(list(set([i.id for i in pdb.get_chains()])))
    # Check if there are duplicates. If true, remove them
    if len(chains_to_keep) != len([i for i in pdb.get_chains()]):

        # A list of placeholder names
        intermediate_chains = ['𝜶','𝜷','𝜸','𝜹','𝜺','𝜻','𝜼','𝜽','𝜾','𝜿','𝝀','𝝁','𝝂','𝝃','𝝄','𝝇','𝝈','𝝊','𝝋','𝝌','𝝎']

        # Function to find a key by its value in a dict
        def getkey(dic, val):
           for key, value in dic.items():
              if val == value:
                 return key

        # Find out when a duplicated chain occurs
        chain_id_seen = {}
        cnt = 0
        for chain in pdb.get_chains():
            cnt += 1
            if chain.id not in chain_id_seen:
                chain_id_seen[cnt] = chain.id

        # Rename all unique (non duplicated) chains to a greek placeholder
        cnt = 0
        for chain in pdb.get_chains():
            cnt += 1
            if chain.id in chains_to_keep and cnt == getkey(chain_id_seen,chain.id):
                chain.id = intermediate_chains[cnt-1]
        # Remove all chains that are not greek placeholders aka the duplicates
        for _ in range(len([c for c in pdb.get_chains()])):
            for model in pdb:
                for chain in model:
                    if chain.id not in intermediate_chains:
                        model.detach_child(chain.id)

        # change the chain names back to the original names
        for chain in pdb.get_chains():
            chain.id = chains_to_keep[intermediate_chains.index(chain.id)]

    return pdb


def find_chains_MHCI(pdb, pept_chain, all_MHC_chains):
    ''' Find the MHCI chains

    Args:
        pdb (Bio.PDB.PDBParser): Bio.PDB object of a peptide-MHCI structure
        pept_chain (str): chain ID of the peptide 
        all_MHC_chains (list): list of all MHC alpha chains in the pdb file

    Returns: list of chains

    '''

    # Find contacts between peptide chain and other chains
    cont = Contacts.Contacts(pdb).chain_contacts
    c = [i for i in cont if i[1] == pept_chain or i[5] == pept_chain]
    # Make a list of all chains that contact the peptide chain
    chain_cont = [i for i in sum([[i[1],i[5]] for i in c], []) if i != pept_chain]
    # Make sure only MHC chains are present in the list
    chain_cont = [i for i in chain_cont if i in all_MHC_chains]
    # Make sure the chain is longer than 120 residues. This prevents selecting e.g. two peptides in the binding groove
    chain_cont = [i for i in chain_cont if i in [c.id for c in pdb.get_chains() if len(c) > 120]]

    # Find the two chains that have the most contacts with the peptide. This should also filter out TCR chains
    if len(set(chain_cont)) >= 1:
        bound_MHC_chains = sorted([ss for ss in set(chain_cont)], key=chain_cont.count, reverse=True)[0]
        bound_MHC_chains = [bound_MHC_chains, pept_chain]
    else:
        print('Found >1 MHC I chains')
        raise Exception

    return bound_MHC_chains


def find_chains_MHCII(pdb, pept_chain):
    ''' Find the MHCI chains

    Args:
        pdb: Bio.PDB object

    Returns: list of chains

    '''
    # todo this works for imgt, need to check if M and N are selected
    # Find contacts between peptide chain and other chains
    cont = Contacts.Contacts(pdb).chain_contacts
    c = [i for i in cont if i[1] == pept_chain or i[5] == pept_chain]
    # Make a list of all chains that contact the peptide chain
    chain_cont = [i for i in sum([[i[1],i[5]] for i in c], []) if i != pept_chain]
    # Make sure the chain is longer than 120 residues. This prevents selecting e.g. two peptides in the binding groove
    chain_cont = [i for i in chain_cont if i in [c.id for c in pdb.get_chains() if len(c) > 120]]

    # Find the two chains that have the most contacts with the peptide. This should also filter out TCR chains
    if len(set(chain_cont)) >= 2:
        MHC_chains = sorted([ss for ss in set(chain_cont)], key=chain_cont.count, reverse=True)[:2]
        MHC_chains = sorted(MHC_chains)
        MHC_chains = MHC_chains + [pept_chain]
    else:
        print('Found >2 MHC I chains')
        raise Exception

    return MHC_chains


def seqs_from_pdb(pdb_file, MHC_chains):
    ''' Use SeqIO to get the amino acid sequences from a PDB file.

    Args:
        pdb_file: (string) path to PDB file
        MHC_chains: (list) names of the M (, N) and P chains

    Returns: (list) AA sequence for the M (, N) and P chain respectively

    '''

    chain_seqs = {record.id: record.seq for record in SeqIO.parse(pdb_file, 'pdb-seqres')}
    seqs = []
    for c in MHC_chains:
        chain = [i for i in chain_seqs.keys()][0].split(':')[0] + ':' + c
        seqs.append(str(chain_seqs[chain]))

    return seqs


def check_missing_pept_residues(pdb, chain='P'):
    ''' Checks for missing residues in a chain by calculating N_{res_i-1}-Ca_{res_i} distance. This distance never
        exceeds ~2.5, so if the N_{res_i-1}-Ca_{res_i} distance > 3 --> residues are missing.

    Args:
        pdb: Bio.PDB object.
        chain: (string) name of the chain that is tested for missing residues.

    Returns: bool. True if residues are missing from the chain

    '''
    # Calculate the distances between every N of residue x and CA of residue x-1.
    N_CA_dist = []
    # Cutoff threshold. If this distance is exceeded, there is a residue gap
    threshold = 3
    # Check for missing chain residues
    prev_atom = [i for i in pdb[0][chain].get_atoms()][0]
    for res in pdb[0][chain]:
        for atom in res:
            if atom.id == 'N':
                N_CA_dist.append(atom - prev_atom)

            if atom.id == 'CA':
                prev_atom = atom

    # If the distance is greater than 3, there is a distance gap because there is a residue missing.
    return any([i > threshold for i in N_CA_dist])


def check_pMHC(pdb):
    ''' Tests parsed pMHC structures: chain numbering, naming and length

    Args:
        pdb: Bio.PDB object

    Returns: Bool

    '''
    requirements = [False, False, False, True]
    chains = [i.id for i in pdb.get_chains()]
    chain_len = {i.id:len(i) for i in pdb.get_chains()}

    # 1. Check chain names and the number of chains
    if len(chains) == 2:
        if 'M' in chains and 'P' in chains and not 'N' in chains:
            requirements[0] = True
    elif len(chains) == 3:
        if 'M' in chains and 'N' in chains and 'P' in chains:
            requirements[0] = True

    # 2. Check M,N chain length
    if len(chains) == 2:
        if chain_len['M'] > 120:
            requirements[1] = True
    elif len(chains) == 3:
        if chain_len['M'] > 120 and chain_len['N'] > 120:
            requirements[1] = True

    # 3. Check peptide length
    if chain_len['P'] > 6 and chain_len['P'] < 26:
        requirements[2] = True

    # 4. Check numbering. Does every chain start at 1 and end at its chain length?
    for c in pdb.get_chains():
        res = [r.id for r in c]
        if not res[0][1] == 1:
            requirements[3] = False
        if not res[-1][1] == len(c):
            requirements[3] = False

    # If all tests are TRUE, the p:MHC structure is successfully passed
    if all(requirements):
        return True
    else:
        return False


def check_non_canonical_res(chain):
    ''' Check if there are non-canonical residues in the chain of a Bio.PDB chain object

    Args:
        chain: Bio.PDB chain object

    Returns: bool, true if there are non canonical residues in the chain

    '''
    letters = ["ALA", "CYS", "ASP", "GLU", "PHE", "GLY", "HIS", "ILE", "LYS", "LEU", "MET", "ASN", "PRO", "GLN", "ARG",
               "SER", "THR", "VAL", "TRP", "TYR"]

    return any([r.resname not in letters for r in chain if r.resname])


def check_hetatoms_in_binding_groove(pdb, MHC_chains):
    ''' Checks if there are heteroatoms in the binding groove between MHC and the peptide. Heteroatoms near the
        peptide on the outside of the binding groove are allowed. This takes ~ 0.008 seconds.

    Args:
        pdb: Bio.PDB object
        MHC_chains: (list) list of MHC chains for the M and P chains respectively

    Returns: bool, true if there are problematic heteroatoms in the binding groove

    '''

    letters = ["ALA", "CYS", "ASP", "GLU", "PHE", "GLY", "HIS", "ILE", "LYS", "LEU", "MET", "ASN", "PRO", "GLN", "ARG",
               "SER", "THR", "VAL", "TRP", "TYR", 'HOH']

    # Based on the number of MHC_chains, the structure is MHCI or II.
    # Define the chain names and the center MHC residue from which distances are calculated.
    if len(MHC_chains) == 2:
        MHC = MHC_chains[0]
        MHC_res = [8]
        search_dist = 18
    if len(MHC_chains) == 3:
        MHC = MHC_chains[1]
        MHC_res = [12, 29]
        search_dist = 18

    P = MHC_chains[-1]

    # Take the CA of a central residue (res 8) in MHCI
    MHC_ch_atoms = [a for a in pdb[0][MHC].get_atoms() if a.id == 'CA' and a.get_parent().id[1] in MHC_res]
    # Take all CA atoms of the peptide chain
    pept_atoms = [a for a in pdb[0][P].get_atoms() if a.id == 'CA']

    potential_junk = []
    for chain in pdb.get_chains():
        for res in chain:
            # If the chain has non-amino acids -> add the atoms to the list.
            if res.resname not in letters:
                for atom in res:
                    potential_junk.append(atom)

    # calculate distances
    atom_dist = NeighborSearch(atom_list=MHC_ch_atoms + potential_junk + pept_atoms).search_all(search_dist)

    # format the distances
    cont = []
    for pair in atom_dist:
        cont.append((pair[1].get_parent().resname, pair[1].get_parent().get_parent().id,
                    pair[1].get_parent().id[1], pair[1].get_id(),pair[0].get_parent().resname,
                    pair[0].get_parent().get_parent().id,pair[0].get_parent().id[1],
                    pair[0].get_id(),pair[0] - pair[1]))
    # remove intra-chain contacts
    cont = [i for i in cont if i[1] != i[5]]
    cont = cont + [(i[4], i[5], i[6], i[7], i[0], i[1], i[2], i[3], i[8]) for i in cont if i[1] == P or i[5] == P]
    cont = list(dict.fromkeys(cont))

    # Find the min distance between the peptide and the central MHC residue
    pept_MHC_dist = min((x[-1], x) for x in [i for i in cont if i[1] == P and i[5] == MHC])

    # remove junk-junk distances
    cont = [i for i in cont if i[5] in [MHC, P]]

    # Find all unique pieces of junk
    junk = list(set([(i[0],i[1],i[2]) for i in cont if i[1] not in [MHC, P]]))

    for piece in junk:
        # For every piece of junk find the min junk-MHC and min junk-peptide distances.
        try:
            # Get the distances for this specific piece of junk
            piece_of_junk_cont = []
            for i in cont:
                if (i[0], i[1], i[2]) == piece:
                    piece_of_junk_cont.append(i)
            # Calculate min junk-MHC and min junk-peptide distances.
            junk_MHC_dist = min((x[-1], x) for x in [i for i in piece_of_junk_cont if i[5] == MHC])
            # max distance between junk and pept
            junk_pept_dist = min((x[-1], x) for x in [i for i in piece_of_junk_cont if i[5] == P])

            # Find out of the piece of junk is inside the binding groove
            if junk_pept_dist[0] < 6:
                # Check if the distance between junk and peptide is smaller than the distance between pept and MHC.
                # If the junk is in between the peptide and MHC, this will be true, but also if the junk is on the outside
                if junk_pept_dist[0] < pept_MHC_dist[0]:
                    # Check if the distance between MHC and junk is smaller than the distance between pept and MHC.
                    # If the junk is in between the peptide and MHC, this will be true
                    if junk_MHC_dist[0] < pept_MHC_dist[0]:
                        return True

        except:
            pass

    return False


def log(ID, error, logfile, verbose=True):
    ''' Keeps track of what goes wrong while parsing

    Args:
        ID: (string) PDB ID
        error: (string) error to append to log file
        logfile: (string) path to logfile
        verbose: (Bool) print error?
    '''

    # Create log file
    if not os.path.exists(logfile):
        with open(logfile, 'w') as f:
            f.write('ID,error\n')

    if verbose:
        print('\t' + error)
    with open(logfile, 'a') as f:
        f.write('%s,%s\n' % (ID, error))


# pdb_id = '1ES0'
# indir = PANDORA.PANDORA_data + '/PDBs/IMGT_retrieved/IMGT3DFlatFiles'
# outdir = PANDORA.PANDORA_data + '/PDBs/pMHCII'
# bad_dir = PANDORA.PANDORA_data + '/PDBs/Bad/pMHCII'
#
# # pdb_file = outdir + '/' + pdb_id + '.pdb'
#
# pdb_file = unzip_pdb(pdb_id, indir, outdir)
# change_sep_in_ser(pdb_file)
# pdb = PDBParser(QUIET=True).get_structure('MHCI', pdb_file)
# # Remove waters and duplicated chains, then renumber
# pdb = remove_duplicated_chains(pdb)
# pdb = renumber(pdb)

# REMARK 410 [   PEPTIDE (1-27) [D1]

def find_merged_pept_chains(pdb_file):
    ''' Checks if the peptide is merged to another chain (have the same chain ID). If True, return a dict telling
        wich chain the peptide is merged to and which residues belong to the peptide. It takes this info from the header

    Args:
        pdb_file: (str): Path to pdb file

    Returns: (dict): {chain_ID:(1:n)}

    '''

    # Get the remarks from the pdb file
    with open(pdb_file) as infile:
        remarks = []
        for line in infile:
            if line.startswith('REMARK 410'):
                row = [x for x in line.rstrip().split(' ') if x != '']
                del row[:2]
                remarks.append(row)
    remarks = [x for x in remarks if x != []]

    ### Dividing each remark section into a chains dictionary
    chains = {}
    flag = False
    for row in remarks:
        if row[0] == 'Chain' and row[1] == 'ID' and len(row) == 4:
            chainID = row[2][-1]
            chains[chainID] = []
            chains[chainID].append(row)
            flag = True
        elif flag == True:
            chains[chainID].append(row)

    pept_chains = {}
    for i in chains:
        for line in chains[i]:
            if 'PEPTIDE(' in ''.join(line) or '[PEPTIDE' in ''.join(line) :
                # add the resnr of the peptideto the dict, with the chain as key
                pept_chains[i] = tuple([int(i) for i in ''.join(line).split('(')[1].split(')')[0].split('-')])

    if pept_chains == {}:
        return False
    return pept_chains



def un_merge_pept_chain(pdb, pdb_file):
    ''' Cut a peptide from a MHC chain if they are merged into the same chain

    Args:
        pdb: (Bio.PDB): Bio.PDB pdb object
        pdb_file: (str): Path to PDB file

    Returns: (Bio.PDB): Bio.PDB pdb object with the peptide as a separate chain

    '''

    pept_chain = find_merged_pept_chains(pdb_file)

    if pept_chain:
        # print('Found merged peptide chain')
        for cn in pept_chain:
            # cn = 'B'
            # Make a list of the residue in the peptide
            pept_res = [res for res in pdb[0][cn] if res.id[1] in range(pept_chain[cn][0], pept_chain[cn][1] + 1)]
            pept_res_keep = pept_res

            # Sometimes there is a gap between the peptide and the end of the peptide-MHC adapter. By calculating the
            # distance between residues, such a gap can be detected. If there is a gap, then take all residues up to
            # that gap. (All residues, incl those after the gap, will be deleted from the original chain later)

            # Calculate the distances between every N of residue x and CA of residue x-1.
            # See 'check_missing_pept_residues()'
            N_CA_dist = []
            # Check for missing chain residues
            prev_atom = [a for a in pept_res[0].get_atoms()][0]
            for res in pept_res:
                for atom in res:
                    if atom.id == 'N':
                        N_CA_dist.append(atom - prev_atom)
                    if atom.id == 'CA':
                        prev_atom = atom
            # Take all the residues until the gap, if there is a gap
            if any(i > 3 for i in N_CA_dist):
                pept_res_keep = pept_res[:next(x for x, val in enumerate(N_CA_dist) if val > 3)]


            # Make a new empty chain using a letter that is not a chain in the pdb yet.
            new_chain_name = [x for x in ascii_uppercase if x not in [i.id for i in pdb.get_chains()]][0]
            new_chain = Chain.Chain(new_chain_name)
            pdb[0].add(new_chain)

            # Add residues to the new chain
            for res in pept_res_keep:
                pdb[0][new_chain_name].add(res)

            # Remove residues from the old chain
            for res in pept_res:
                pdb[0][cn].detach_child(res.id)

            # Also add the parent to the new residues (othewise the Contacts class will complain)
            for res in pdb[0][new_chain_name]:
                res.parent = pdb[0][new_chain_name]

        # Renumber the pdb, because some residues got removed, the numbering is now wrong
        pdb = renumber(pdb)

    return pdb




def parse_pMHCI_pdb(pdb_id,
                     indir = PANDORA.PANDORA_data + '/PDBs/IMGT_retrieved/IMGT3DFlatFiles',
                     outdir = PANDORA.PANDORA_data + '/PDBs/pMHCI',
                     bad_dir = PANDORA.PANDORA_data + '/PDBs/Bad/pMHCI'):
    ''' Clean all MHCI pdb files that have been downloaded from IMGT

    Args:
        pdb_id: (string) id of pdb file
        indir: (string) path of the input dir (where the .gz files are)
        outdir: (string) path of the output dir (where the unzipped .pdb files go)
        bad_dir: (string) path of the output dir (where the unsuitable .pdb files go)

    Returns: Template object

    '''
    logfile = os.path.dirname(bad_dir) + '/log_MHCI.csv'

    # Check if file exists
    if os.path.isfile('%s/IMGT-%s.pdb.gz' % (indir, pdb_id)):
        print('Parsing %s' % pdb_id)
        try:
            # Unzip file (also check if the file is not empty) and save the path of this file
            pdb_file = unzip_pdb(pdb_id, indir, outdir)
            change_sep_in_ser(pdb_file)
            pdb = PDBParser(QUIET=True).get_structure('MHCI', pdb_file)
            # Remove waters and duplicated chains, then renumber
            pdb = remove_duplicated_chains(pdb)
            pdb = renumber(pdb)

            try:            #Check if the peptide is merged to the MHC, cut it loose and put it in a new chain
                pdb = un_merge_pept_chain(pdb, pdb_file)
            except:
                log(pdb_id, 'Could not cut peptide from MHC chain', logfile)
                raise Exception

            try:                # Find the peptide chain
                pept_chain = find_peptide_chain(pdb)
            except:
                log(pdb_id, 'Could not find a suitable peptide chain', logfile)
                raise Exception

            alleles = get_chainid_alleles_MHCI(pdb_file)
            try:                 # Find out which chains are the Alpha and Peptide chain
                MHC_chains = find_chains_MHCI(pdb, pept_chain, list(alleles.keys()))
            except:
                log(pdb_id, 'Could not locate Alpha chain', logfile)
                raise Exception

            if check_missing_pept_residues(pdb, chain=pept_chain):
                log(pdb_id, 'Peptide chain is missing residues', logfile)
                raise Exception

            if check_non_canonical_res(pdb[0][pept_chain]):
                log(pdb_id, 'Non canonical residues in the peptide chain', logfile)
                raise Exception

            if check_hetatoms_in_binding_groove(pdb, MHC_chains):
                log(pdb_id, 'Heteroatoms in binding groove between the peptide and MHC', logfile)
                raise Exception

            try:                 # Reformat chains
                pdb = remove_irregular_chains(pdb, MHC_chains)  # Remove all other chains from the PBD that we dont need
                pdb = replace_chain_names(MHC_chains, pdb,['M', 'P'])  # Rename chains to M,P # Renumber from 1
            except:
                log(pdb_id, 'Could not reformat structure', logfile)
                raise Exception

            try:  # get the chain sequences from the pdb file
                # seqs = seqs_from_pdb(pdb_file, MHC_chains)
                #seqs = [seq1(''.join([res.resname for res in chain])) for chain in pdb.get_chains()]
                seqs = {chain.id : seq1(''.join([res.resname for res in chain])) for chain in pdb.get_chains()}
            except:
                log(pdb_id, 'Could not fetch chain sequences from pdb file', logfile)
                raise Exception

            if not check_pMHC(pdb):
                log(pdb_id, 'Structure did not pass the test.', logfile)
                raise Exception

            # Finally, write the cleaned pdb to the output dir. Keep the header of the original file.
            write_pdb(pdb, '%s/%s.pdb' % (outdir, pdb_id), pdb_file)

            try:
                # Get allele per each chain
                #al = get_chainid_alleles_MHCI(pdb_file)
                try:
                    alpha = [[k for k, v in i.items()] for i in [alleles['A'][i] for i in [i for i in alleles['A'].keys()]]]
                except KeyError:
                    try:
                        c = MHC_chains[0]
                        alpha = [[k for k, v in i.items()] for i in [alleles[c][i] for i in [i for i in alleles[c].keys()]]]
                    except KeyError:
                        c = [i for i in alleles.keys()][0]
                        alpha = [[k for k, v in i.items()] for i in [alleles[c][i] for i in [i for i in alleles[c].keys()]]]

                a_allele = sum(alpha, [])
            except:
                log(pdb_id, 'Could not find allele type', logfile)
                raise Exception

            # Get structure resolution
            resolution = get_resolution(pdb_file)
            # Create MHC_structure object
            templ = PMHC.Template(pdb_id, allele_type=a_allele, M_chain_seq=seqs['M'], peptide=seqs['P'],  pdb_path=pdb_file, resolution=resolution)

            return templ

        except:  # If something goes wrong, append the ID to the bad_ids list
            os.system('mv %s/%s.pdb %s/%s.pdb' % (outdir, pdb_id, bad_dir, pdb_id))

# lst = ['1ES0','1FNE','1FNG','1HDM','1I3R','1IEA','1IEB','1K8I','1KT2','1KTD','1LNU','2BC4','2IAD','3C5Z','3C60','3C6L','3CUP','3LQZ','3PL6','3RDT','3T0E','3WEX','4AH2','4GRL','4MAY','4P23','4P46','4P4K','4P4R','4P57','4P5K','4P5M','4P5T','4X5X','5DMK','5V4M','5V4N','6BGA','6BLQ','6BLX','6DFW','6DFX','6MFF','6MFG','6MKD','6MKR','6MNM','6MNN','6MNO']
# parse_pMHCII_pdb('6DFX')
# pdb_id = '1ES0'
#
# for i in lst:
#     parse_pMHCII_pdb(i)


def parse_pMHCII_pdb(pdb_id,
                      indir=PANDORA.PANDORA_data + '/PDBs/IMGT_retrieved/IMGT3DFlatFiles',
                      outdir = PANDORA.PANDORA_data + '/PDBs/pMHCII',
                      bad_dir = PANDORA.PANDORA_data + '/PDBs/Bad/pMHCII'):
    ''' Clean all MHCII pdb files that have been downloaded from IMGT

    Args:
        pdb_id: (string) id of pdb file
        indir: (string) path of the input dir (where the .gz files are)
        outdir: (string) path of the output dir (where the unzipped .pdb files go)
        bad_dir: (string) path of the output dir (where the unsuitable .pdb files go)

    Returns: Template object

    '''
    # set paths for in and out directories
    logfile = os.path.dirname(bad_dir) + '/log_MHCII.csv'

    if os.path.isfile('%s/IMGT-%s.pdb.gz' % (indir, pdb_id)):
        print('Parsing %s' % pdb_id)
        try:
            # Unzip file (also check if the file is not empty) and save the path of this file
            pdb_file = unzip_pdb(pdb_id, indir, outdir)
            change_sep_in_ser(pdb_file)
            pdb = PDBParser(QUIET=True).get_structure('MHCII', pdb_file)
            # Remove waters and duplicated chains, then renumber
            pdb = remove_duplicated_chains(pdb)
            pdb = renumber(pdb)

            try:            #Check if the peptide is merged to the MHC, cut it loose and put it in a new chain
                pdb = un_merge_pept_chain(pdb, pdb_file)
            except:
                log(pdb_id, 'Could not cut peptide from MHC chain', logfile)
                raise Exception

            # [i for i in pdb.get_chains()]

            try:                # Find the peptide chain
                pept_chain = find_peptide_chain(pdb)
            except:
                log(pdb_id, 'Could not find a suitable peptide chain', logfile)
                raise Exception

            try:                 # Find out which chains are the Alpha and Peptide chain
                MHC_chains = find_chains_MHCII(pdb, pept_chain)
            except:
                log(pdb_id, 'Could not locate Alpha chain', logfile)
                raise Exception

            if check_missing_pept_residues(pdb, chain=pept_chain):
                log(pdb_id, 'Peptide chain is missing residues', logfile)
                raise Exception

            if check_non_canonical_res(pdb[0][pept_chain]):
                log(pdb_id, 'Non canonical residues in the peptide chain', logfile)
                raise Exception

            if check_hetatoms_in_binding_groove(pdb, MHC_chains):
                log(pdb_id, 'Heteroatoms in binding groove between the peptide and MHC', logfile)
                raise Exception

            try:                 # Reformat chains
                pdb = remove_irregular_chains(pdb, MHC_chains)  # Remove all other chains from the PBD that we dont need
                pdb = replace_chain_names(MHC_chains, pdb, ['M', 'N', 'P'])   # Rename chains to M,N,P
            except:
                log(pdb_id, 'Could not reformat structure', logfile)
                raise Exception

            try:  # get the chain sequences from the pdb file
                # seqs = seqs_from_pdb(pdb_file, MHC_chains)
                seqs = [seq1(''.join([res.resname for res in chain])) for chain in pdb.get_chains()]
            except:
                log(pdb_id, 'Could not fetch chain sequences from pdb file', logfile)
                raise Exception


            if not check_pMHC(pdb): #test if the pdb is parsed correctly
                log(pdb_id, 'Structure did not pass the test.', logfile)
                raise Exception

            # Finally, write the cleaned pdb to the output dir. Keep the header of the original file.
            write_pdb(pdb, '%s/%s.pdb' % (outdir, pdb_id), pdb_file)

            # Get allele per each chain
            try:
                al = get_chainid_alleles_MHCII(pdb_file)
                try:
                    alpha = sum([al['Alpha'][i] for i in [i for i in al['Alpha'].keys()]], [])
                except KeyError:
                    try:
                        alpha = sum([al[MHC_chains[0]][i] for i in [i for i in al[MHC_chains[0]].keys()]], [])
                    except KeyError:
                        alpha = sum([al['A'][i] for i in [i for i in al['A'].keys()]], [])

                try:
                    beta = sum([al['Beta'][i] for i in [i for i in al['Beta'].keys()]], [])
                except KeyError:
                    try:
                        beta = sum([al[MHC_chains[1]][i] for i in [i for i in al[MHC_chains[1]].keys()]], [])
                    except KeyError:
                        beta = sum([al['B'][i] for i in [i for i in al['B'].keys()]], [])
                a_allele = list(set([alpha[i - 1] for i in range(3, int(len(alpha)), 4)]))
                b_allele = list(set([beta[i - 1] for i in range(3, int(len(beta)), 4)]))
            except:
                log(pdb_id, 'Could not find allele type', logfile)
                raise Exception

            # Get structure resolution
            resolution = get_resolution(pdb_file)

            # Create MHC_structure object
            templ = PMHC.Template(pdb_id, allele_type=a_allele + b_allele, M_chain_seq=seqs[0], N_chain_seq=seqs[1],
                                  peptide=seqs[2], MHC_class='II', pdb_path=pdb_file, resolution=resolution)

            return templ

        except:  # If something goes wrong, append the ID to the bad_ids list
            os.system('mv %s/%s.pdb %s/%s.pdb' % (outdir, pdb_id, bad_dir, pdb_id))
