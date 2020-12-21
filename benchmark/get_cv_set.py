import pickle
import csv

IDD_file = open('data/csv_pkl_files/IDs_and_bad_IDs_dict.pkl', 'rb')
IDD = pickle.load(IDD_file)
bad_IDs = pickle.load(IDD_file)
IDD_file.close()



with open('benchmark/PANDORA_benchmark_dataset.tsv', 'wt') as outfile:
    tsv_writer = csv.writer(outfile, delimiter='\t')
    tsv_writer.writerow(['TARGET_ID', 'PEPT_SEQ', 'ALLELE'])
    for ID in IDD:
        tsv_writer.writerow((ID, IDD[ID]['pept_seq'], (';').join(IDD[ID]['allele'])))
