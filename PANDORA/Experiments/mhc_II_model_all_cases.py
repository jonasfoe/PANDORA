import PANDORA
from PANDORA.PMHC.Model import to_csv
from PANDORA.Database import Database
from PANDORA.Wrapper import Wrapper
import os
import pickle
import multiprocessing

database_path = 'PANDORA/pandora_database'
output_dir = 'PANDORA_files/data/outputs/mhc_II_benchmark'
results_file = 'modelling_summary.csv'

if __name__ == "__main__":


    # 1. Load pandora database if possible, alternatively, construct it from scratch
    if os.path.isfile(database_path):
        print('Loading Database')
        db = Database.load(database_path)
    else:
        print('Constructing Database. This might take a while ...')
        db = Database.Database()
        db.construct_database(save='pandora_database')

    all_targets_ids = list(db.MHCII_data.keys())

    # 2. Make the wrapper input file for PANDORA
    with open('mhc_ii_benchmark.tsv', 'w') as f:
        for k in list(db.MHCII_data.keys()):
            # peptide, allele, achors, M_chain, N_chain, id
            f.write(f"{db.MHCII_data[k].peptide}\t"
                    f"{';'.join(db.MHCII_data[k].allele_type)}\t"
                    f"{';'.join([str(i) for i in db.MHCII_data[k].anchors])}\t"
                    f"{db.MHCII_data[k].M_chain_seq}\t"
                    f"{db.MHCII_data[k].N_chain_seq}\t"
                    f"{db.MHCII_data[k].id}\n")

    # 3. Inititate wrapper
    wrap = Wrapper.Wrapper()
    wrap.create_targets('mhc_ii_benchmark.tsv', db, MHC_class='II',
                        peptides_col=0, allele_col=1, anchors_col=2,
                        M_chain_col=3, N_chain_col=4, IDs_col=5,
                        benchmark=True )

    # 4. Run all cases
    wrap.run_pandora(num_cores=multiprocessing.cpu_count(), benchmark=True, output_dir=output_dir, pickle_out=True)

    # 5. Calulate the L-RMSD of all cases
    cases = [i for i in os.listdir(f'{PANDORA.PANDORA_path}/../{output_dir}') if os.path.isdir(f'{PANDORA.PANDORA_path}/../{output_dir}/{i}')]

    for case in cases:
        target_id = case.split('_')[0]

        try:

            # Load results pickle
            with open(f'{PANDORA.PANDORA_path}/../{output_dir}/{case}/results_{case}.pkl', 'rb') as handle:
                results = pickle.load(handle)

            for res in results:
                res.output_dir = f'{PANDORA.PANDORA_path}/../{output_dir}/{case}'

                try:
                    res.calc_LRMSD(db.MHCII_data[target_id].pdb_path)
                except:
                    print('Something went wrong calculating the l-rmsd')
                try:
                    res.calc_Core_LRMSD(db.MHCII_data[target_id].pdb_path)
                except:
                    print('Something went wrong calculating the core l-rmsd')
                try:
                    res.calc_flanking_LRMSD(db.MHCII_data[target_id].pdb_path)
                except:
                    print('Something went wrong calculating the flanking l-rmsd')

                # Write results to file
                to_csv(f"{PANDORA.PANDORA_path}/../{output_dir}/{results_file}", res, db)

        except:
            print(f"Something went wrong with opening {case}")

