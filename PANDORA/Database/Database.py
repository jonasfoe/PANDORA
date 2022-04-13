import PANDORA
import pickle
from PANDORA.PMHC import PMHC
from PANDORA.Database import Database_functions
import os
import subprocess

class Database:
    #todo Integrate Anchor calculation with Rafaellas code to do all the anchor calcs while initiating the db
    def __init__(self):
        self.MHCI_data = {}
        self.MHCII_data = {}
        self.ref_MHCI_sequences = {}
        self.__IDs_list_MHCI = []
        self.__IDs_list_MHCII = []

    def download_data(self, data_dir = PANDORA.PANDORA_data, download = True):
        """ Download all MHC structures and get a two lists that contains all MHCI and MHCII IDs respectively"""

        if download:
            print('Downloading structures ...')
            Database_functions.download_unzip_imgt_structures(data_dir = data_dir, del_inn_files=True, del_kabat_files=True)
        self.__IDs_list_MHCI = Database_functions.download_ids_imgt('MH1', data_dir = data_dir, out_tsv='all_MHI_IDs.tsv')
        self.__IDs_list_MHCII = Database_functions.download_ids_imgt('MH2', data_dir = data_dir, out_tsv='all_MHII_IDs.tsv')


    def __clean_MHCI_file(self, pdb_id, data_dir):
        """ Clean all MHCI structures"""
        return Database_functions.parse_pMHCI_pdb(pdb_id,
                                                   indir = data_dir + '/PDBs/IMGT_retrieved/IMGT3DFlatFiles',
                                                   outdir = data_dir + '/PDBs/pMHCI',
                                                   bad_dir = data_dir + '/PDBs/Bad/pMHCI')

    def __clean_MHCII_file(self, pdb_id, data_dir):
        """ Clean all MHCII structures. Returns a list of bad PDBs"""
        return Database_functions.parse_pMHCII_pdb(pdb_id,
                                                   indir = data_dir + '/PDBs/IMGT_retrieved/IMGT3DFlatFiles',
                                                   outdir = data_dir + '/PDBs/pMHCII',
                                                   bad_dir = data_dir + '/PDBs/Bad/pMHCII')
    
    def update_ref_sequences(self):
        """Downloads and parse HLA and other MHC sequences to compile reference fastas.
        Returns a dictionary that can be used to select the desired reference sequence"""
        self.ref_MHCI_sequences = Database_functions.generate_mhcseq_database()
        
    def construct_database(self, save, data_dir = PANDORA.PANDORA_data, 
                           MHCI=True, MHCII=True, download=True,
                           update_ref_sequences=True):
        ''' Construct the database. Download, clean and add all structures

        Args:
            save (str/bool): Filename of database, can be False if you don't want to save the database
            data_dir (str): Path of data directory. Defaults to PANDORA.PANDORA_data.
            MHCI (bool): Parse data for MHCI. Defaults to True.
            MHCII (bool): Parse data for MHCII. Defaults to True.
            download (bool): If True, download the structures data from IMGT. Defaults to True.
            update_ref_sequences (bool): If True, downloads and parse reference sequence strcutres. Defaults to True

        Returns: Database object

        '''
        # Download the data
        self.download_data(download = download, data_dir = data_dir)

        # Construct the MHCI database
        if MHCI:
            # Parse all MHCI files
            for id in self.__IDs_list_MHCI:
                try:
                    templ = self.__clean_MHCI_file(pdb_id = id, data_dir = data_dir)
                    if templ != None:
                        self.MHCI_data[id] = templ
                except:
                    pass

        # Construct the MHCII database
        if MHCII:
            # Parse all MHCII files
            for id in self.__IDs_list_MHCII:
                try:
                    templ = self.__clean_MHCII_file(pdb_id = id, data_dir = data_dir)
                    if templ != None:
                        self.MHCII_data[id] = templ
                except:
                    print('something went wrong parsing %s' %id)
    
        databases_data_dir = PANDORA.PANDORA_data+ '/csv_pkl_files/'
        #Construct blast database for blast-based sequence-based template selection
        # self.construct_blast_db(outpath=PANDORA.PANDORA_data+ '/csv_pkl_files/templates_blast_db',
        #                         db_name='templates_blast_db')
        
        #Download and parse HLA and MHC sequences reference data
        if update_ref_sequences:
            self.update_ref_sequences()
        
        #Construct blast database for retriving mhc allele
        # self.construct_blast_db(outpath=PANDORA.PANDORA_data+ '/csv_pkl_files/refseq_blast_db',
        #                         db_name='refseq_blast_db')

        self.construct_both_blast_db(databases_data_dir)            

        if save:
            self.save(save)
        
        print('Database correctly generated')

    def add_structure(self, id, allele_type, peptide = '', MHC_class = 'I', chain_seq = [], anchors = [], pdb_path = False, pdb = False):
        ''' Add a single structure to the database

        Args:
            id: (str) PDB identifier
            allele_type: (lst) list of MHC alleles (or allele)
            peptide: (str) peptide sequence
            MHC_class: (str) either 'I' or 'II' denoting MHC class I and MHC class II respectively
            chain_seq: (lst) list of chain sequence(s) for the M and N (Alpha and Beta) chain respectively
            anchors: (lst) list of integers specifying which residue(s) of the peptide should be fixed as an anchor
                        during the modelling. MHC class I typically has 2 anchors, while MHC class II typically has 4.
            pdb_path: (str) path to pdb file
            pdb: (Bio.PDB) Biopython PBD object

        '''

        if not id:
            if not pdb_path or not pdb:
                raise ValueError('Structure id or path of .pdb files was not given. Enter value for id and pdb_path')
        # Add to MHCI data
        if MHC_class == 'I':
            self.MHCI_data[id] = PMHC.Template(id, allele_type, peptide, MHC_class, chain_seq, anchors, pdb_path, pdb)
        # Add to MHCII data
        if MHC_class == 'II':
            self.MHCII_data[id] = PMHC.Template(id, allele_type, peptide, MHC_class, chain_seq, anchors, pdb_path, pdb)
            
            
    def write_db_into_fasta(self, outfile):
        """
        Writes structure db into a fasta file (to be later used to build a blast database)
    
        Args:
            MHC_class (str): I or II.
            outfile (str): output file path.
    
        Returns:
            None.
    
        """
        
        sequences = []
        for template in self.MHCI_data.values():
            header, seq = Database_functions.get_sequence_for_fasta(
                                        template, MHC_class='I', chain='M')
            sequences.append((header, seq))
            
        for template in self.MHCII_data.values():
            header, seq = Database_functions.get_sequence_for_fasta(
                                        template, MHC_class='II', chain='M')
            sequences.append((header, seq))
            
            header, seq = Database_functions.get_sequence_for_fasta(
                                        template, MHC_class='II', chain='N')
            sequences.append((header, seq))
        
        self.all_sequences = sequences
        
        with open(outfile, 'w') as outfasta:
            for sequence in sequences:
                header = sequence[0]
                seq = sequence[1]
                outfasta.write('> %s\n' %header)
                outfasta.write('\n'.join(seq[j:j+60] for j in range(0, len(seq), 60)) + '\n')
                
            

    def construct_blast_db(self, infile, outpath, db_name):
        """
        Construc blast database for seq based template selection

        Args:
            outpath (str, optional): Data dir folder. Defaults to PANDORA.PANDORA_data+ '/csv_pkl_files/'.
            db_name (str, optional): Name of the db folder and fasta file. Defaults to 'MHC_blast_db'.
        Returns:
            None.

        """
        # if not os.path.isdir(outpath):
        #     subprocess.check_call('mkdir %s' %outpath, shell=True)
        
        # out_fasta = outpath+'/'+db_name+'.fasta'
        # self.write_db_into_fasta(outfile=out_fasta)
        
        subprocess.check_call((' ').join(['makeblastdb','-dbtype','prot',
                                          '-in', infile,'-out', 
                                          outpath+'/'+db_name]), shell=True)
        
    def construct_both_blast_db(self, data_dir=PANDORA.PANDORA_data+ '/csv_pkl_files/'):
        
        #Define db name and path
        db_name='templates_blast_db'
        outpath=data_dir+ db_name
        out_fasta = outpath+'/'+db_name+'.fasta'
        
        #Create db directory
        if not os.path.isdir(outpath):
            subprocess.check_call('mkdir %s' %outpath, shell=True)
        
        #Create .fasta for the db
        self.write_db_into_fasta(outfile=out_fasta)
        
        #Construct blast database for blast-based sequence-based template selection
        self.construct_blast_db(infile = out_fasta,
                                outpath=outpath,
                                db_name=db_name)
        
        #Define db name and path
        db_name='refseq_blast_db'
        outpath=data_dir+ db_name
        out_fasta = outpath+'/'+db_name+'.fasta'
        
        #Create db directory
        if not os.path.isdir(outpath):
            subprocess.check_call('mkdir %s' %outpath, shell=True)
        
        #Create .fasta for the db
        command='cat %sHuman_MHC_data.fasta %sNonHuman_MHC_data.fasta > %s' %(data_dir, 
                                                                              data_dir, 
                                                                              out_fasta)
        subprocess.check_call(command, shell=True)
        
        #Construct blast database for retriving mhc allele
        self.construct_blast_db(infile=out_fasta,
                                outpath=outpath,
                                db_name=db_name)
        
        

    def remove_structure(self, id =''):
        ''' Removes a structure (by id) from the database

        Args:
            id: (str) PDB ID

        '''

        # Remove structure from database
        self.MHCI_data.pop(id, None)
        self.MHCII_data.pop(id, None)
    
    def repath(self, new_folder_path, save):
        """
        Necessary if the absolut path to the templates structures is different
        from the one used while generating the database.
        It changes the template.pdb_path for each template object in the database
        and returns the modified database.

        Args:
            new_folder_path (str): New path to the 'PDBs' directory contaning template structures.
            save (str/bool): If False, doesn't save the modified database. If str, saves the modified database to the specified file path.'

        Returns:
            None.
            
        Example:
            >>> MyDatabase.repath('/home/Users/MyUserName/PANDORA/PDBs/', './MyHome_Database.pkl')

        """
        
        if type(new_folder_path) != str:
            raise Exception('Non-string argument detected. Please provide a valid path as argument.')
        
        if self.MHCI_data != {}:
            for id in self.MHCI_data:
                from_pMHCI_path = os.path.join(*os.path.normpath(self.MHCI_data[id].pdb_path).split('/')[-2:])
                self.MHCI_data[id].pdb_path = os.path.join(new_folder_path, from_pMHCI_path)
        
        if self.MHCII_data != {}:
            for id in self.MHCII_data:
                from_pMHCII_path = os.path.join(*os.path.normpath(self.MHCII_data[id].pdb_path).split('/')[-2:])
                self.MHCII_data[id].pdb_path = os.path.join(new_folder_path, from_pMHCII_path)
                
        if save:
            self.save(save)

    def save(self, fn = 'db.pkl'):
        """Save the database as a pickle file

        :param fn: (str) pathname of file
        """
        with open(fn, "wb") as pkl_file:
            pickle.dump(self, pkl_file)

def load(file_name):
    """Loads a pre-generated database
    

    Args:
        file_name (str): Dabase file name/path.

    Returns:
        Database.Database: Database object.
    
    Example:
        >>> db = Database.load('MyDatabase.pkl')

    """
    with open(file_name, 'rb') as inpkl:
        db = pickle.load(inpkl)
    return db

