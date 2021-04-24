
import PANDORA
from PANDORA.Pandora import Align
from PANDORA.Pandora import Modelling_functions
import time
import os
from Bio.PDB import PDBParser
from datetime import datetime


class Pandora:

    def __init__(self, target, database=None, template=None, output_dir=PANDORA.PANDORA_data + '/outputs'):
        self.target = target
        self.template = template
        self.database = database
        self.output_dir = output_dir

        if database is None and template is None:
            raise Exception('Provide a Database object so Pandora can find the best suitable template structure for '
                            'modelling. Alternatively, you can specify a user defined Template object.')

    def find_template(self, best_n_templates=1, benchmark=False, verbose=True):
        ''' Find the best template structure given a Target object

        Args:
            seq_based_templ_selection: (bool) Use template selection based on template sequences instead of allele.
            verbose: (bool) Print information

        '''

        if verbose:
            print('\tTarget MHC Class: %s' % self.target.MHC_class)
            print('\tTarget Allele:  %s' % self.target.allele_type)
            print('\tTarget Peptide: %s' % self.target.peptide)
            print('\tTarget Anchors: %s\n' % self.target.anchors)

        if self.template is None: # Only find the best template if the user didn't specify one
            # if verbose and self.target.M_chain_seq != '' and seq_based_templ_selection:
            #     print('\tUsing sequence based template selection')
            if verbose:
                print('\tUsing allele type based template selection')
            # Find the best template. If the target already exists in the database, 
            # also consider the initial loop model as a model
            self.template, self.pept_ali_scores, self.keep_IL = Modelling_functions.find_template(self.target,
                                                                    self.database,
                                                                    best_n_templates=best_n_templates,
                                                                    benchmark=benchmark)
            self.target.templates = [i.id for i in self.template]
            if verbose:
                print('\tSelected template structure: %s' %([i.id for i in self.template]))

        else:
            if verbose:
                print('\tUser defined template structure: %s' %([i.id for i in self.template]))
            # Check if the target structure and template structure are the same.
            self.keep_IL = any(Modelling_functions.check_target_template(self.target, tmpl) for tmpl in self.templates)





        if verbose:
            print('\tTemplate Allele:  %s' %([i.allele_type for i in self.template]))
            print('\tTemplate Peptide: %s' %([i.peptide for i in self.template]))
            print('\tTemplate Anchors: %s\n' %([i.anchors for i in self.template]))

    def prep_output_dir(self, output_dir=PANDORA.PANDORA_data + '/outputs'):
        ''' Create an output directory and move the template pdb there
        '''
        # create an output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # dd/mm/YY H:M:S
        date_time = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        # Create the output dir of the specific case
        self.output_dir = '%s/%s_%s_%s' %(output_dir, self.target.id, '_'.join([i.id for i in self.template]), date_time)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # copy the template structure to the output file
        for t in self.template:
            os.system('cp %s %s/%s.pdb' %(t.pdb_path, self.output_dir, t.id))

    def align(self, verbose=True):
        ''' Create the alignment file for modeller

        Args:
            verbose:  (bool) Print information

        Returns: (dict) dict of alignment of the chains with the chains as keys

        '''
        self.alignment = Align.Align(self.target, self.template, output_dir=self.output_dir)

        # self.alignment = Align.Align2(target = self.target, template=self.template, output_dir=self.output_dir)
        # self.alignment.align_templates()

        if verbose:
            print('\tSuccessfully created alignment file')

    def write_ini_script(self):
        ''' Write the scipt that modeller uses for creating the initial model'''
        os.chdir(os.path.dirname(PANDORA.PANDORA_path))
        Modelling_functions.write_ini_script(self.target, self.template, self.alignment.alignment_file, self.output_dir)

    def create_initial_model(self, python_script = 'cmd_modeller_ini.py', verbose = True):
        ''' Run modeller to create the initial model. Modeller can only output files in its work directory
            (why though?), so the current work directory is changed to the output dir and later changed back the the
            old working dir.


        Args:
            python_script:  (string) path to script that performs the modeller modelling. cmd_modeller_ini.py
            verbose:  (bool) Print information

        Returns: (BIO.PDB object) self.target.initial_model

        '''
        # Change working directory
        os.chdir(self.output_dir)
        # Run Modeller
        os.popen('python %s' %python_script).read()
        # Load initial model into target object
        self.target.initial_model = PDBParser(QUIET=True).get_structure(self.target.id, self.target.id + '.ini')
        # Change working directory back
        os.chdir(os.path.dirname(PANDORA.PANDORA_path))
        if verbose:
            print('\tSuccessfully created the initital model')

    def run_modeller(self, python_script='cmd_modeller.py', benchmark=False, pickle_out=True, verbose=True, keep_IL=False):
        ''' Perform the homology modelling.

        Args:
            python_script: (string) path to script that performs the modeller modelling. cmd_modeller.py
            benchmark: (bool) Perform L-RMSD calculations? only works if the target id is an existing pdb id
            pickle_out: (bool) Save a .pkl with the results
            verbose:  (bool) Print information

        Returns: (list) list of Model objects

        '''

        if verbose:
            print('\tPerforming homology modelling of %s on %s...' %(self.target.id, '_'.join([t.id for t in self.template])))
        t0 = time.time()
        self.results = Modelling_functions.run_modeller(self.output_dir, self.target, python_script=python_script,
                                                        benchmark=benchmark, pickle_out=pickle_out, keep_IL=keep_IL)
        if verbose:
            print('\n\tModelling was successfull and took %s seconds' %(round(time.time() - t0, 2)))

    def anchor_contacts(self, verbose=True):
        ''' Calculate anchor contacts and writes a contacts.list file that modeller uses for restraints.

        Args:
            verbose: (bool) Print information

        '''

        if verbose:
            print('\tCalculating peptide anchor residue constraints...')
        self.target.calc_anchor_contacts()
        #    Write output file
        with open(self.output_dir + '/contacts_' + self.target.id + '.list', 'w') as f:
                for i in self.target.anchor_contacts:
                    f.write('\t'.join('%s' % x for x in i) + '\n')

    def write_modeller_script(self, n_loop_models=20, n_homology_models = 1, n_jobs=None, stdev=0.1, helix=False, sheet=False):
        ''' Write the script that modeller uses for the final homology modelling.

        Args:
            n_models: (int) number of models that Pandora generates
            n_jobs: (int) number of parallel jobs. Is recommended to use as many jobs as the number of models: less will result in
                a slower run, more will not add any benefit but might occupy cores unnecessarily.
            stdev: (float) standard deviation of modelling restraints. Higher = more flexible restraints.

        '''
        Modelling_functions.write_modeller_script(self.target, self.template, self.alignment.alignment_file, 
                                                  self.output_dir, n_loop_models=n_loop_models,
                                                  n_homology_models=n_homology_models, n_jobs=n_jobs, stdev=stdev,
                                                  helix=helix, sheet=sheet)

    def __log(self, target_id, template_id, error, logfile = PANDORA.PANDORA_data + '/outputs/Pandora_log.txt', verbose=True):
        ''' Keeps track of what goes wrong while parsing

        Args:
            target_id: (str): ID of target structure
            template_id: (str): ID of template structure
            error: (str): error to append to log file
            logfile: (str): path to logfile
            verbose: (bool): print error?
        '''

        # Create log file
        if not os.path.exists(logfile):
            with open(logfile, 'w') as f:
                f.write('Target\tTemplate\tError\n')

        if verbose:
            print('\t' + error)
        with open(logfile, 'a') as f:
            f.write('%s\t%s\t%s\n' % (target_id, template_id, error))

    def model(self, output_dir=PANDORA.PANDORA_data + '/outputs', n_loop_models=20, n_homology_models=1,
              best_n_templates=1, n_jobs=None,
              stdev=0.1, benchmark=False, verbose=True, helix=False, sheet=False):
        ''' Wrapper function that combines all modelling steps.

        Args:
            n_models: (int) number of models modeller generates per run
            stdev: (float) standard deviation of modelling restraints. Higher = more flexible restraints.
            seq_based_templ_selection: (bool) Use template selection based on template sequences instead of allele.
            benchmark: (bool) Perform L-RMSD calculations? only works if the target id is an existing pdb id
            verbose: (bool) Print information

        Returns:

        '''

        if verbose:
            print('\nModelling %s...\n' %self.target.id)

        # Make sure we're in the root directory
        os.path.dirname(PANDORA.PANDORA_path)

        # Find the best template structure given the Target
        try:
            self.find_template(best_n_templates=best_n_templates, benchmark=benchmark, verbose=verbose)
        except:
            self.__log(self.target.id, 'None', 'Could not find a template')
            raise Exception

        # Prepare the output directory
        try:
            self.prep_output_dir(output_dir=output_dir)
        except:
            self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Failed creating output directory')
            raise Exception



        # Perform sequence alignment. This is used to superimpose the target on the template structure in later steps
        try:
            self.align(verbose=verbose)
        except:
            self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Failed aligning target and template')
            raise Exception

        # Prepare the scripts that run modeller
        try:
            self.write_ini_script()
        except:
            self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Failed writing .ini script')
            raise Exception

        # Run modeller to create the initial model
        try:
            self.create_initial_model(verbose=verbose)
        except:
            self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Failed creating initial model with modeller')
            raise Exception

        # Calculate anchor restraints
        try:
            self.anchor_contacts(verbose=verbose)
        except:
            self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Failed calculating anchor restraints')
            raise Exception

        # prepare the scripts that run modeller
        try:
            self.write_modeller_script(n_loop_models=n_loop_models, n_homology_models=n_homology_models, n_jobs=n_jobs,
                                       stdev=stdev, helix=helix, sheet=sheet)
        except:
            self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Failed preparing the modeller script')
            raise Exception

        # Do the homology modelling
        try:
            self.run_modeller(benchmark=benchmark, verbose=verbose, keep_IL=self.keep_IL)
        except:
            self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Failed running modeller')
            raise Exception


        if verbose and benchmark:
            try:
                print('\n\tModel\t\t\t\tMolpdf\t\tL-RMSD\t\tcore L-RMSD')
                for m in self.results:
                    try:
                        print('\t%s\t\t%s\t\t%s\t\t%s' % (
                            os.path.basename(m.model_path).replace('.pdb', ''), round(float(m.moldpf), 4),
                            round(float(m.lrmsd), 4), round(float(m.core_lrmsd), 4)))
                    except AttributeError:
                        try:
                            print('\t%s\t\t%s\t\t%s' % (
                                os.path.basename(m.model_path).replace('.pdb', ''), round(float(m.moldpf), 4),
                                round(float(m.lrmsd), 4)))
                        except AttributeError:
                            print('\t%s\t\t%s' % (
                                os.path.basename(m.model_path).replace('.pdb', ''), round(float(m.moldpf), 4)))

                # Get top 5
                median_rmsd, median_core = Modelling_functions.top5_from_results(self.results)
                if median_rmsd:
                    print('\n\tThe median L-RMSD of the top 5 best scoring models: %s' %median_rmsd)
                if median_core:
                    print('\tThe median core L-RMSD of the top 5 best scoring models: %s\n' %median_core)

            except:
                self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Could not calculate L-RMSD')
                raise Exception

        elif verbose and not benchmark:
            print('\n\tModel\t\t\t\tMolpdf')
            for m in self.results:
                print('\t%s\t\t%s' %(os.path.basename(m.model_path).replace('.pdb', ''), round(float(m.moldpf), 4)))

        self.__log(self.target.id, '_'.join([i.id for i in self.template]), 'Successfully modelled %s models' %(n_homology_models*n_loop_models))








