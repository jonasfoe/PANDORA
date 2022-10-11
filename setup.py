# -*- coding: utf-8 -*-
from os.path import exists
import os
import json

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

def create_database_folders(data_folder):
    dirs = [
            './Databases', f'./Databases/{data_folder}',
            f'./Databases/{data_folder}/mhcseqs', 
            f'./Databases/{data_folder}/PDBs',
            f'./Databases/{data_folder}/PDBs/pMHCI', 
            f'./Databases/{data_folder}/PDBs/pMHCII',
            f'./Databases/{data_folder}/PDBs/Bad', 
            f'./Databases/{data_folder}/PDBs/Bad/pMHCI',
            f'./Databases/{data_folder}/PDBs/Bad/pMHCII', 
            f'./Databases/{data_folder}/PDBs/IMGT_retrieved',
            f'./Databases/{data_folder}/outputs',
            './test/test_data',
            './test/test_data/PDBs/Bad',
            './test/test_data/PDBs/Bad/pMHCI',
            './test/test_data/PDBs/Bad/pMHCII', 
            ]

    for D in dirs:
        try:
            os.mkdir(D)
        except OSError:
            print('Could not make directory: ' + D)


# To update the package version number, edit PANDORA/__version__.py
version = {}
with open(os.path.join(here, 'PANDORA', '__version__.py')) as f:
    exec(f.read(), version)

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name='PANDORA',
    version=version['__version__'],
    description='Model peptide-MHC I complexes using anchor distance restrains in MODELLER',
    long_description=readme + '\n\n',
    long_description_content_type='text/markdown',
    author='Dario Marzella, Farzaneh Parizi, Li Xue',
    url='https://github.com/X-lab-3D/PANDORA/tree/master',
    project_urls={
        'Source Code': 'https://github.com/X-lab-3D/PANDORA/tree/master',
        'Issue tracker': 'https://github.com/X-lab-3D/PANDORA/issues'
    },
    packages=find_packages(),
    include_package_data=True,
    license="Apache Software License 2.0",
    keywords='PANDORA',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],


    install_requires=[
       'Biopython',
       'pdb_tools',
       'pdb2sql',
       'matplotlib',
       'joblib'
       ],

    extras_require={
        'doc': ['recommonmark', 'sphinx', 'sphinx_rtd_theme'],
        'test': ['pytest', 'pytest-runner', 'pytest-cov',
                 'coverage', 'coveralls', 'pycodestyle']
    }
)

#Check if config.json exists
if exists('config.json'):
    with open('config.json') as f:
        data = json.load(f)
        data_folder = data['data_folder_name']
else:
    data_folder = 'default'

# Create the folders for the default database and testing
create_database_folders(data_folder)