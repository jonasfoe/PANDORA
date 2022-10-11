# -*- coding: utf-8 -*-
from os.path import exists
import os
import json
from pathlib import Path


from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

def create_database_folders(installation_folder):
    dirs = [
            f'{installation_folder}/Databases', 
            f'{installation_folder}/Databases/default',
            f'{installation_folder}/Databases/default/mhcseqs', 
            f'{installation_folder}/Databases/default/PDBs',
            f'{installation_folder}/Databases/default/PDBs/pMHCI', 
            f'{installation_folder}/Databases/default/PDBs/pMHCII',
            f'{installation_folder}/Databases/default/PDBs/Bad', 
            f'{installation_folder}/Databases/default/PDBs/Bad/pMHCI',
            f'{installation_folder}/Databases/default/PDBs/Bad/pMHCII', 
            f'{installation_folder}/Databases/default/PDBs/IMGT_retrieved',
            f'{installation_folder}/Databases/default/outputs',
            f'{installation_folder}/test/test_data',
            f'{installation_folder}/test/test_data/PDBs/Bad',
            f'{installation_folder}/test/test_data/PDBs/Bad/pMHCI',
            f'{installation_folder}/test/test_data/PDBs/Bad/pMHCII', 
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
user_folder_path = Path(__file__).parents[0]
#data_folder = f'{user_folder_path}/Databases/default'

# Create the folders for the default database and testing
create_database_folders(user_folder_path)