import os
import PANDORA
from PANDORA import Contacts
from PANDORA import Align
from PANDORA import Database
from PANDORA import Database_functions
from PANDORA import Template
from PANDORA import Pandora
from PANDORA import Target
from PANDORA import Model
from PANDORA import Wrapper

working_dir = os.path.dirname(os.path.realpath(__file__))

def test_PMHC_target():
    # Create target object
    target = Target('1A1O',
                         allele_type=['HLA-B*5301', 'HLA-B*5301'],
                         peptide='KPIVQYDNF',
                         M_chain_seq = 'GSHSMRYFYTAMSRPGRGEPRFIAVGYVDDTQFVRFDSDAASPRTEPRPPWIEQEGPEYWDRNTQIFKTNTQTYRE'
                                       'NLRIALRYYNQSEAGSHIIQRMYGCDLGPDGRLLRGHDQSAYDGKDYIALNEDLSSWTAADTAAQITQRKWEAARV'
                                       'AEQLRAYLEGLCVEWLRRYLENGKETLQRADPPKTHVTHHPVSDHEATLRCWALGFYPAEITLTWQRDGEDQTQDT'
                                       'ELVETRPAGDRTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWEP',
                         anchors = [2, 9])
    # test if the inital model is empty, MHC class, the peptide chain, the allele and anchors
    pass_test = False
    if (target.initial_model == False and 
        target.MHC_class == 'I' and 
        target.peptide == 'KPIVQYDNF' and
        target.anchors == [2, 9]):
        
        pass_test = True

    assert pass_test


def test_PMHC_template():
    # Create template object
    template = Template('1A1O',
                         allele_type=['HLA-B*5301', 'HLA-B*5301'])
    # check calculated anchors, M_chain, peptide, allele and pdb chains
    pass_test = False
    if (template.anchors == [2,9] and 
        template.M_chain_seq != '' and 
        template.peptide == 'KPIVQYDNF' and
        template.allele_type == ['HLA-B*53:01', 'HLA-B*53:01'] and
        [i.id for i in template.pdb.get_chains()] == ['M', 'P']):
            pass_test = True

    assert pass_test


def test_fail_PMHC():
    # Try to fail initiating a template object
    pass_test = False
    try:
        Template('id', ['allele'])
    except:
        pass_test = True

    assert pass_test


def test_contacts():
    # Calculate atom contacts
    c = Contacts.Contacts(PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCI/1A1O.pdb')
    # check length of output, chains of the pdb and the pdb path
    pass_test = False
    if len(c.chain_contacts[0]) == 9 and [i.id for i in c.PDB.get_chains()] == ['M', 'P'] and c.pdb_path != '':
        pass_test = True

    assert pass_test



def test_align():
    # initiate target and template object
    template = Template('1A1O',
                         allele_type=['HLA-B*5301', 'HLA-B*5301'],
                         pdb_path=PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCI/1A1O.pdb',
                             anchors = [2, 9])
    target = Target('2X4R',
                         allele_type=['test'],
                         peptide='NLVPMVATV',
                         M_chain_seq = 'GSHSMRYFFTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDGETRKVKAHSQTHRV'
                                       'DLGTLRGYYNQSEAGSHTVQRMYGCDVGSDWRFLRGYHQYAYDGKDYIALKEDLRSWTAADMAAQTTKHKWEAAHV'
                                       'AEQLRAYLEGTCVEWLRRYLENGKETLQRTDAPKTHMTHHAVSDHEATLRCWALSFYPAEITLTWQRDGEDQTQDT'
                                       'ELVETRPAGDGTFQKWAAVVVPSGQEQRYTCHVQHEGLPKPLTLRWE',
                         anchors = [2, 9],
                         output_dir=PANDORA.PANDORA_path + '/../test/')
    # align target and template
    a = Align.Align(target, template)
    # check keys of aligned output and output .ali file path
    pass_test = False
    if a.aligned_seqs_and_pept['1A1O P'] == 'KPIVQYDNF' and '2X4R M' in a.aligned_seqs_and_pept:
        if os.path.basename(a.alignment_file) == '2X4R.ali':
            pass_test = True
    # Remove output dir
    os.system('rm -r %s1A1O_2X4R' %(PANDORA.PANDORA_path + '/../test/'))

    assert pass_test


def test_clean_MHCI_structure():
    x = Database_functions.parse_pMHCI_pdb('1A1O',
                       indir=PANDORA.PANDORA_path + '/../test/test_data/PDBs/IMGT_retrieved/IMGT3DFlatFiles',
                       outdir=PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCI',
                       bad_dir=PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCI/Bad',
                       remove_biopython_object=False)

    assert x.peptide == 'KPIVQYDNF' and [i.id for i in x.pdb.get_chains()] == ['M', 'P']


def test_clean_MHCII_structure():
    x = Database_functions.parse_pMHCII_pdb('2NNA',
                       indir=PANDORA.PANDORA_path + '/../test/test_data/PDBs/IMGT_retrieved/IMGT3DFlatFiles',
                       outdir=PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCII',
                       bad_dir=PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCII/Bad',
                       remove_biopython_object=False)


    assert x.peptide == 'SGEGSFQPSQENP' and [i.id for i in x.pdb.get_chains()] == ['M', 'N', 'P']


def test_construct_database():
    #test_data = PANDORA.PANDORA_path + '/../test/test_data/'
    #bad1, bad2 = test_data + 'PDBs/Bad/pMHCI/6C6A.pdb', test_data + 'PDBs/Bad/pMHCII/1K8I.pdb'
    log1, log2 = PANDORA.PANDORA_data + '/PDBs/Bad/log_MHCI.csv', PANDORA.PANDORA_data + '/PDBs/Bad/log_MHCII.csv'

    # Construct database object
    db = Database.Database()
    db.construct_database(save=False, download=False)

    # test the creation of bad files, log files and the information inside of the database object
    pass_test = False
    log_flag = False
    templates_flag = False
    if os.path.exists(log2):
        log_flag = True
        if '1A1O' in db.MHCI_data and '4Z7U' in db.MHCII_data:
            templates_flag = True
            if db.MHCII_data['2NNA'].peptide == 'SGEGSFQPSQENP' and db.MHCI_data['2X4R'].peptide == 'NLVPMVATV':
                pass_test = True

    # remove bad files
    os.system('rm %s %s' %(log1, log2))

    assert log_flag
    assert templates_flag 
    assert pass_test

def test_load_db():
    db = Database.load()#PANDORA.PANDORA_path + '/../test/test_data/Test_Pandora_MHCI_and_MHCII_data.pkl')
    # test if items in the database are correct
    pass_test = False
    if '1A1O' in db.MHCI_data and '4Z7U' in db.MHCII_data:
        if db.MHCII_data['2NNA'].peptide == 'SGEGSFQPSQENP' and db.MHCI_data['2X4R'].peptide == 'NLVPMVATV':
            pass_test = True

    assert pass_test

def test_template_select_MHCI():
    db = Database.load()#PANDORA.PANDORA_path + '/../test/test_data/Test_Pandora_MHCI_and_MHCII_data.pkl')
    # Create target object
    target = Target('1A1O',
                         allele_type=db.MHCI_data['1A1O'].allele_type,
                         peptide=db.MHCI_data['1A1O'].peptide,
                         M_chain_seq=db.MHCI_data['1A1O'].M_chain_seq,
                         anchors=db.MHCI_data['1A1O'].anchors,
                         output_dir = os.path.dirname(PANDORA.PANDORA_path) + '/test')

    # Perform modelling
    mod = Pandora.Pandora(target, db)
    mod.find_template(benchmark=True)

    assert mod.template.id == '2X4R' and mod.template.peptide == 'NLVPMVATV'

def test_template_select_MHCII():
    # Load database
    db = Database.load()#PANDORA.PANDORA_path + '/../test/test_data/Test_Pandora_MHCI_and_MHCII_data.pkl')
    # Create target object
    target = Target('2NNA',
                         allele_type=db.MHCII_data['2NNA'].allele_type,
                         peptide=db.MHCII_data['2NNA'].peptide,
                         MHC_class= 'II',
                         M_chain_seq=db.MHCII_data['2NNA'].M_chain_seq,
                         N_chain_seq=db.MHCII_data['2NNA'].N_chain_seq,
                         anchors=db.MHCII_data['2NNA'].anchors,
                         output_dir = os.path.dirname(PANDORA.PANDORA_path) + '/test')

    # Perform modelling
    mod = Pandora.Pandora(target, db)
    mod.find_template(benchmark=True)

    assert mod.template.id == '4Z7U' and mod.template.peptide == 'PSGEGSFQPSQENPQ'

def test_pandora_MHCI_modelling():
    # Load database
    db = Database.load()#PANDORA.PANDORA_path + '/../test/test_data/Test_Pandora_MHCI_and_MHCII_data.pkl')
    # Create target object
    target = Target('1A1O',
                         allele_type=db.MHCI_data['1A1O'].allele_type,
                         peptide=db.MHCI_data['1A1O'].peptide,
                         M_chain_seq=db.MHCI_data['1A1O'].M_chain_seq,
                         anchors=db.MHCI_data['1A1O'].anchors,
                         output_dir = os.path.dirname(PANDORA.PANDORA_path) + '/test/test_output/')

    # Perform modelling
    mod = Pandora.Pandora(target, db)
    mod.model(n_loop_models=1, stdev=0.1, benchmark=True, loop_refinement='very_fast')

    # Check if mod.template is initiated and if the initial model is created. Then checks molpdf of output.
    pass_test = False
    if mod.template.id == '2X4R' and [c.id for c in mod.target.initial_model.get_chains()] == ['M', 'P']:
        if float(mod.results[0].molpdf) < 2000 and float(mod.results[0].molpdf) > 0:
            pass_test = True
    # remove output file
    os.system('rm -r %s' % (target.output_dir))

    assert pass_test

def test_wrapper_MHCI():
    # Load database
    db = Database.load()#PANDORA.PANDORA_path + '/../test/test_data/Test_Pandora_MHCI_and_MHCII_data.pkl')
    # Define data_file
    data_file =  PANDORA.PANDORA_path + '/../test/test_data/test_MHCI_wrapper_data.tsv'
    #Define output directory
    output_dir = os.path.dirname(PANDORA.PANDORA_path) + '/test/test_output/'
    # Create targets
    wrap = Wrapper.Wrapper(data_file, db, MHC_class='I', header=False, 
                        delimiter='\t', IDs_col=0, peptides_col=1, 
                        allele_name_col=3, anchors_col=2, M_chain_col=4,
                        num_cores=1, n_loop_models=1, 
                        benchmark=False, collective_output_dir=output_dir)
    
    # Check if the jobs went as expected
    errors = []
    #targets_flag = False
    try:
        if len(wrap.targets) == 2 and wrap.targets['1A9B']['peptide_sequence'] == 'LPPLDITPY':
            if wrap.targets['2X4O']['peptide_sequence'] == 'KLTPLCVTL':
                #targets_flag = True
                pass
            else:
                errors.append('target_error')
        else:
            errors.append('target_error')
    except KeyError:
        raise Exception('KeyError in targets_flag')

    
    #TODO: Add check model exist flag
    #TODO: Add check molpdf flag

    assert not errors, "errors occured:\n{}".format("\n".join(errors))

def test_pandora_MHCII_modelling():
    # Load database
    db = Database.load()#PANDORA.PANDORA_path + '/../test/test_data/Test_Pandora_MHCI_and_MHCII_data.pkl')
    # Create target object
    target = Target('2NNA',
                         allele_type=db.MHCII_data['2NNA'].allele_type,
                         peptide=db.MHCII_data['2NNA'].peptide,
                         MHC_class= 'II',
                         M_chain_seq=db.MHCII_data['2NNA'].M_chain_seq,
                         N_chain_seq=db.MHCII_data['2NNA'].N_chain_seq,
                         anchors=db.MHCII_data['2NNA'].anchors,
                         output_dir = os.path.dirname(PANDORA.PANDORA_path) + '/test/test_output/')

    # Perform modelling
    mod = Pandora.Pandora(target, db)
    mod.model(n_loop_models=1, stdev=0.2, benchmark=True, loop_refinement='very_fast')
    # Check if mod.template is initiated and if the initial model is created. Then checks molpdf of output.
    pass_test = False
    if mod.template.id == '4Z7U' and [c.id for c in mod.target.initial_model.get_chains()] == ['M','N', 'P']:
        if float(mod.results[0].molpdf) < 1000 and float(mod.results[0].molpdf) > -1000:
            pass_test = True
    # remove output file
    os.system('rm -r %s' % (target.output_dir))
    assert pass_test

def test_rmsd():
    # Load database
    db = Database.load()#PANDORA.PANDORA_path + '/../test/test_data/Test_Pandora_MHCI_and_MHCII_data.pkl')
    # Create target object
    target = Target('1A1O',
                         allele_type=db.MHCI_data['1A1O'].allele_type,
                         peptide=db.MHCI_data['1A1O'].peptide,
                         M_chain_seq=db.MHCI_data['1A1O'].M_chain_seq,
                         anchors=db.MHCI_data['1A1O'].anchors,
                         output_dir=PANDORA.PANDORA_path + '/../test')

    # Initiate Model object
    m = Model.Model(target, model_path=PANDORA.PANDORA_path + '/../test/test_data/1A1O.BL00010001.pdb')
    # Calculate L-RMSD and Core L-RMSD
    m.calc_LRMSD(PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCI/1A1O.pdb')
    m.calc_Core_LRMSD(PANDORA.PANDORA_path + '/../test/test_data/PDBs/pMHCI/1A1O.pdb')
    # Check if the rmsds are between 0.5 and 2 (I gave some slack for the cases that modeller gets lucky.
    pass_test = m.lrmsd > 1 and m.lrmsd < 1.5 and m.core_lrmsd > 1 and m.core_lrmsd < 1.5

    assert pass_test
