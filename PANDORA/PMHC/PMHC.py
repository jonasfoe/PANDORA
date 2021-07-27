
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1
from PANDORA.Contacts import Contacts
from PANDORA.Database import Database_functions
from PANDORA.Pandora import Modelling_functions
from PANDORA.PMHC import Anchors
from abc import ABC, abstractmethod

class PMHC(ABC):

    def __init__(self, id, allele_type, peptide = '', MHC_class = 'I', M_chain_seq = '', N_chain_seq = '', anchors = [],
                 helix=False, sheet=False):
        ''' pMHC class. Acts as a parent class to Template and Target

        Args:
            id: (string) PDB identifier
            allele_type: (list) list of MHC alleles (or allele)
            peptide: (string) peptide sequence
            MHC_class: (string) either 'I' or 'II' denoting MHC class I and MHC class II respectively
            M_chain_seq: (string) M chain sequence for the Alpha chain
            N_chain_seq: (string) N chain sequence for the Beta chain
            anchors:  (list) list of integers specifying which residue(s) of the peptide should be fixed as an anchor
                        during the modelling. MHC class I typically has 2 anchors, while MHC class II typically has 4.
        '''
        super().__init__()
        self.id = id
        self.MHC_class = MHC_class
        self.peptide = peptide
        self.M_chain_seq = M_chain_seq
        self.N_chain_seq = N_chain_seq
        self.allele_type = allele_type
        self.anchors = anchors
        self.helix = helix
        self.sheet = sheet


        @abstractmethod
        def info(self):
            pass

        @abstractmethod
        def calc_contacts(self):
            pass

        @abstractmethod
        def calc_anchor_contacts(self):
            pass


class Template(PMHC):

    def __init__(self, id, allele_type, peptide='', MHC_class='I', M_chain_seq='', N_chain_seq='', anchors=[], helix=False, sheet=False, pdb_path=False, pdb=False, resolution=None):
        ''' Template structure class. This class holds all information of a template structure that is used for
            homology modelling. This class needs a id, allele and the path to a pdb file to work. (sequence info of
            the chains and peptide can be fetched from the pdb)

        Args:
            id: (string) PDB identifier
            allele_type: (list) list of MHC alleles (or allele)
            peptide: (string) peptide sequence
            MHC_class:  (string) either 'I' or 'II' denoting MHC class I and MHC class II respectively
            M_chain_seq: (string) M chain sequence for the Alpha chain
            N_chain_seq: (string) N chain sequence for the Beta chain
            anchors: (list) list of integers specifying which residue(s) of the peptide should be fixed as an anchor
                        during the modelling. MHC class I typically has 2 anchors, while MHC class II typically has 4.
            pdb_path: (string) path to pdb file
            pdb: (Bio.PDB) Biopython PBD object
            resolution: (float) Structure resolution in Angstrom
        '''
        super().__init__(id, allele_type, peptide, MHC_class, M_chain_seq, N_chain_seq, anchors, helix, sheet)
        self.pdb_path = pdb_path
        self.pdb = pdb
        self.contacts = False
        self.resolution = resolution


        if not pdb_path and not pdb:
            raise Exception('Provide a PDB structure to the Template object first')

        if pdb_path and not pdb: # If the path to a pdb file or a Bio.PDB object is given, parse the pdb
            self.parse_pdb()

        if anchors == []:
            self.calc_anchors()

    def parse_pdb(self):
        '''Loads pdb from path, updates self.pdb field and self.chain_seq/self.peptide if they were empty'''

        if self.pdb_path and not self.pdb: #if there is a path to a pdb provided and there is not already a self.pdb...
            parser = PDBParser(QUIET=True)  # Create a parser object, used to read pdb files
            self.pdb = parser.get_structure('MHC', self.pdb_path) #Create Bio.PDB object
            self.resolution = Database_functions.get_resolution(self.pdb_path) #Get resolution from pdb file

        # If the chains or peptide are not given by the user, fetch them from the pdb
        # Get the chain sequences
        chain_seqs = [seq1(''.join([res.resname for res in chain])) for chain in self.pdb.get_chains()]
        # Update chain and peptide fields if emtpy
        if self.MHC_class == 'I':
            if self.M_chain_seq == '':
                self.M_chain_seq = chain_seqs[0]
            if not self.peptide:
                self.peptide = chain_seqs[-1]
        if self.MHC_class == 'II':
            if self.M_chain_seq == '' and self.N_chain_seq == '':
                self.M_chain_seq = chain_seqs[0]
                self.N_chain_seq = chain_seqs[1]
            if not self.peptide:
                self.peptide = chain_seqs[-1]

    def info(self):
        """ Print the basic info of this structure

        """
        print('This is a %s structure.' %(type(self).__name__))
        print('ID: %s' %self.id)
        print('Type: MHC class %s' %self.MHC_class)
        print('Alleles: %s' % self.allele_type)
        if self.M_chain_seq != '':
            print('Alpha chain length: %s' %len(self.M_chain_seq))
        if self.N_chain_seq != '' and self.MHC_class == 'II':
            print('Beta chain length: %s' %len(self.N_chain_seq))
        print('Peptide length: %s' %len(self.peptide))
        if self.M_chain_seq != '':
            print('Alpha chain: %s' % self.M_chain_seq)
        if self.N_chain_seq != '':
            print('Beta chain: %s' % self.N_chain_seq)

        print('Peptide: %s' % self.peptide)
        print('Anchors: %s' %self.anchors)

        if self.sheet:
            print('Beta-sheet: %s' % self.sheet)
        if self.helix:
            print('Alpha-helix: %s' % self.helix)
        if self.pdb_path:
            print('Path to PDB file: %s' %self.pdb_path)
        if not self.pdb:
            print('PDB structure: no PDB structure provided')
        else:
            print('PDB structure:')
            for (k, v) in self.pdb.header.items():
                print('\t'+k + ':', v)

    def calc_contacts(self):
        if self.pdb:
            self.contacts = Contacts.Contacts(self.pdb)
        else:
            raise Exception('Provide a PDB structure to the Template object first')

    def calc_anchors(self):
        if self.MHC_class == 'I':
            self.anchors = Anchors.pMHCI_anchors(self.pdb)
        if self.MHC_class == 'II':
            self.anchors = Anchors.pMHCII_anchors(self.pdb)

    def calc_anchor_contacts(self):
        if self.pdb and self.anchors:
            self.anchor_contacts = Contacts.Contacts(self.pdb, anchors=self.anchors).anchor_contacts
        else:
            raise Exception('Provide an initial model (.ini PDB) and anchor positions to the Target object first')




class Target(PMHC):

    def __init__(self, id, allele_type, peptide, MHC_class = 'I', M_chain_seq = '', N_chain_seq = '', anchors = [],
                 helix=False, sheet=False, templates = False):
        ''' Target structure class. This class needs an ID (preferably a PDB ID), allele and pepide information.

        Args:
            id: (string) PDB identifier
            peptide: (string) peptide sequence
            allele_type: (list) list of MHC alleles (or allele)
            MHC_class: (string) either 'I' or 'II' denoting MHC class I and MHC class II respectively
            M_chain_seq: (string) M chain sequence for the Alpha chain
            N_chain_seq: (string) N chain sequence for the Beta chain
            anchors: (list) list of integers specifying which residue(s) of the peptide should be fixed as an anchor
                        during the modelling. MHC class I typically has 2 anchors, while MHC class II typically has 4.
            templates: Template object. The user can specify that PANDORA uses a certain structure as template.
        '''

        super().__init__(id, allele_type, peptide, MHC_class, M_chain_seq, N_chain_seq, anchors, helix, sheet)
        self.templates = templates
        self.initial_model = False
        self.contacts = False
        self.anchor_contacts = False

        # If the user does provide sequence info, make sure both the M and N chain are provided
        if MHC_class == 'II' and M_chain_seq != '' and N_chain_seq == '':
            raise Exception('Provide both the M and N chain sequences for MHC class II targets or none at all')
        if MHC_class == 'II' and N_chain_seq != '' and M_chain_seq == '':
            raise Exception('Provide both the M and N chain sequences for MHC class II targets or none at all')
        
        # If anchors are not provided, predict them from the peptide length. If netMHCpan is not installed, promt the
        # user to install it with netMHCpan_install.py
        if MHC_class =='I' and anchors == []:
            print('WARNING: no anchor positions provided. Pandora will predict them using netMHCpan')

            netMHCpan_dir = [i for i in os.listdir(PANDORA.PANDORA_path + '/../') if
                             i.startswith('netMHCpan') and os.path.isdir(i)]
            if os.path.isfile(PANDORA.PANDORA_path + '/../' + netMHCpan_dir[0] + '/netMHCpan'):
                # predict the anchors
                self.anchors = Modelling_functions.predict_anchors_netMHCpan(self.peptide, self.allele_type)

            else:
                print("Need netMHCpan to predict anchor positions. Please install by running 'netMHCpan_install.py'.")


        if MHC_class =='II' and anchors == []:
            print('WARNING: no anchor positions provided. Pandora will predict them using netMHCIIpan')

            netMHCIIpan_dir = [i for i in os.listdir(PANDORA.PANDORA_path + '/../') if
                             i.startswith('netMHCIIpan') and os.path.isdir(i)]
            if os.path.isfile(PANDORA.PANDORA_path + '/../' + netMHCIIpan_dir[0] + '/netMHCIIpan'):
                # predict the anchors
                self.anchors = Modelling_functions.predict_anchors_netMHCIIpan(self.peptide, self.allele_type)
            else:
                print("Need netMHCIIpan to predict anchor positions. Please install by running 'netMHCpan_install.py'.")


    def info(self):
        """ Print the basic info of this structure

        """
        print('This is a %s structure.' % (type(self).__name__))
        print('ID: %s' % self.id)
        print('Type: MHC class %s' % self.MHC_class)
        print('Alleles: %s' % self.allele_type)
        if self.M_chain_seq != '':
            print('Alpha chain length: %s' %len(self.M_chain_seq))
        if self.N_chain_seq != '' and self.MHC_class == 'II':
            print('Beta chain length: %s' %len(self.N_chain_seq))
        print('Peptide length: %s' %len(self.peptide))
        if self.M_chain_seq != '':
            print('Alpha chain: %s' % self.M_chain_seq)
        if self.N_chain_seq != '':
            print('Beta chain: %s' % self.N_chain_seq)
        print('Peptide: %s' % self.peptide)
        print('Anchors: %s' % self.anchors)
        if self.sheet:
            print('Beta-sheet: %s' % self.sheet)
        if self.helix:
            print('Alpha-helix: %s' % self.helix)
        if self.templates:
            print('Using template %s for homology modelling' %self.templates)
        if self.initial_model:
            print('An initial model has been provided.')

    def calc_contacts(self):
        if self.initial_model:
            self.contacts = Contacts.Contacts(self.initial_model)
        else:
            raise Exception('Provide a PDB structure to the Template object first')

    def calc_anchor_contacts(self):
        if self.initial_model and self.anchors:
            self.anchor_contacts = Contacts.Contacts(self.initial_model, anchors=self.anchors).anchor_contacts
        else:
            raise Exception('Provide an initial model (.ini PDB) and anchor positions to the Target object first')