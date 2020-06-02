# -*- coding: utf-8 -*-

import csv
import os
import pickle

best_rmsds = {}
IDs = {}

filename_start = 'BL00'
filename_end = '0001.pdb'
with open('../../benchmark/PANDORA_benchmark_dataset.tsv', 'r') as idfile:
    r = csv.reader(idfile, delimiter='\t')
    for i, row in enumerate(r):
        query = 'query_'+str(i)
        IDs[query]=row[0]
    
    
for fol in os.listdir('./'):
    if os.path.isdir('./'+fol):
        print('Working on '+ fol)
        os.chdir('./'+fol)
        brk_flag = False
        if os.path.isfile('./final_scores.tsv'):
            query = fol[5:]
            target_id = IDs[query]
            final_scores = {}
                
            
            os.popen('cp ../../../data/PDBs/%s_MP.pdb ./' %target_id).read()
            
            os.popen('pdb_reres -1 %s_MP.pdb > reres_%s.pdb' %(target_id, target_id)).read()
            os.popen('bash ../../../tools/map_2_pdb.sh %s.BL00010001.pdb reres_%s_MP.pdb > ref.pdb' %(query, target_id)).read()
            os.popen('python ../../../tools/pdb_fast_lzone_mhc.py ref.pdb').read()
            
            with open('file.list', 'w') as out:
                for f in os.listdir('./'):
                    if f.startswith(query+'.'+filename_start) and f.endswith(filename_end):
                        out.write('matched_'+ f + '\n')
                        os.popen('bash ../../../tools/map_2_pdb.sh ref.pdb %s >  matched_%s' %(f,f)).read()
            
            os.popen('../../../tools/CA_backbone_l-rmsd-calc.csh ref file.list').read()
            os.popen('../../../tools/CA_l-rmsd-calc.csh ref file.list').read()
            os.popen('../../../tools/CA_backbone_CB_l-rmsd-calc.csh ref file.list').read()
            
            with open('./final_scores.tsv', 'r') as infile:
                r = csv.reader(infile, delimiter='\t')
                for i, row in enumerate(r):
                    if i == 0:
                        header = row[:-1]
                    else:
                        final_scores['matched_'+row[0]] = [float(row[1]), float(row[2])]#, float(row[3])]
            
            with open('./BB-l-RMSD.dat') as cafile:
                r = csv.reader(cafile, delimiter=' ')
                header.append('BB_l-RMSD')
                for row in r:
                    final_scores[row[0]].append(float(row[1]))
                    
            with open('./CA-l-RMSD.dat') as cafile:
                r = csv.reader(cafile, delimiter=' ')
                header.append('CA_l-RMSD')
                for row in r:
                    final_scores[row[0]].append(float(row[1]))
            
            with open('./BB-CB-l-RMSD.dat') as cafile:
                r = csv.reader(cafile, delimiter=' ')
                header.append('BB_CB_l-RMSD')
                for row in r:
                    try:
                        final_scores[row[0]].append(float(row[1]))
                    except:
                        pass
                
                    
            with open('./all_rmsds_and_final_scores.tsv', 'wt') as outfile:
                tw = csv.writer(outfile, delimiter='\t')
                tw.writerow(header)
                for key in final_scores:
                    try:
                        tw.writerow([key, final_scores[key][0], final_scores[key][1], final_scores[key][2],
                                      final_scores[key][3], final_scores[key][4]])
                    except:
                        tw.writerow([key, final_scores[key][0], final_scores[key][1], final_scores[key][2],
                                      final_scores[key][3], 'N/A'])
            
            molsort = sorted(final_scores.items(), key=lambda x:x[1][0])
            bb_bestmol = sum(x[1][2] for x in molsort[0:5])/5.0
            ca_bestmol = sum(x[1][3] for x in molsort[0:5])/5.0
            try:
                ca_bb_cb_bestmol = sum(x[1][4] for x in molsort[0:5])/5.0
            except:
                ca_bb_cb_bestmol = 'N/A'
            
            dopesort = sorted(final_scores.items(), key=lambda x:x[1][1])
            bb_bestdope = sum(x[1][2] for x in dopesort[0:5])/5.0
            ca_bestdope = sum(x[1][3] for x in dopesort[0:5])/5.0
            try:
                ca_bb_cb_bestdope = sum(x[1][4] for x in dopesort[0:5])/5.0
            except:
                ca_bb_cb_bestdope = 'N/A'
            
            best_rmsds[target_id] = [ca_bestmol, bb_bestmol, ca_bb_cb_bestmol, ca_bestdope, bb_bestdope, ca_bb_cb_bestdope]
        os.chdir('../')

dictfile = open("./all_best_RMSDs.pkl", "wb")
pickle.dump(best_rmsds, dictfile)
dictfile.close()

with open('./all_best_RMSDs.tsv', 'wt') as finalfile:
    tw = csv.writer(finalfile, delimiter='\t')
    tw.writerow(['Target ID', 'Top 5 molpdf CA RMDS','Top 5 molpdf BB RMDS',
             'Top 5 molpdf BB_CB RMDS', 'Top 5 DOPE CA RMDS',
             'Top 5 DOPE BB RMDS', 'Top 5 DOPE BB_CB RMDS'])
    for key in best_rmsds:
        tw.writerow([key, best_rmsds[key][0], best_rmsds[key][1], best_rmsds[key][2],
                         best_rmsds[key][3], best_rmsds[key][4], best_rmsds[key][5]])

    