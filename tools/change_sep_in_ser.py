import sys
import os

indir = sys.argv[1]

for pdbfile in os.listdir(indir):
    outfile_name = indir + pdbfile + '.temp'
    outfile = open(outfile_name, 'w')
    for line in open(indir + pdbfile, 'r'):
        s = line.split(' ')
        l = [x for x in s if x != '']
        if len(l) >= 4:
            if ('SEP' in l[3] or 'SEP' in l[2]) and l[2] not in ['P', 'O1P', 'O2P', 'O3P', 'HA', 'HB2', 'HB3']:
                outfile.write(line.replace('HETATM', 'ATOM  ').replace('SEP', 'SER'))
            elif ('SEP' in l[3] or 'SEP' in l[2]) and l[2] in ['P', 'O1P', 'O2P', 'O3P', 'HA', 'HB2', 'HB3']:
                pass
            elif ('F2F' in l[3] or 'F2F' in l[2]) and l[2] not in ['F1', 'F2']:
                outfile.write(line.replace('HETATM', 'ATOM  ').replace('F2F', 'PHE'))
            elif ('F2F' in l[3] or 'F2F' in l[2]) and l[2] in ['F1', 'F2']:
                pass
            else:
                outfile.write(line)
        else:
            outfile.write(line)
    outfile.close()
    
    os.system('mv %s %s' %(outfile_name, indir + pdbfile))
