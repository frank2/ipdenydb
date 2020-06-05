#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'ipdenydb'
    ,version = '1.0.0'
    ,author = 'frank2'
    ,author_email = 'frank2@dc949.org'
    ,description = 'A database for IPDeny'
    ,license = 'GPLv3'
    ,keywords = 'ipv4 ipv6 network'
    ,url = 'https://github.com/frank2/ipdenydb'
    ,package_dir = {'ipdenydb': 'lib'}
    ,packages = ['ipdenydb']
    ,include_package_data = True
    ,package_data = {'ipdenydb': ['*.json']}
    ,install_requires = ['martinellis', 'psycopg2']
    ,long_description = '''A database interface for IPDeny's IP block data.'''
    ,classifiers = [
        'Development Status :: 3 - Alpha'
        ,'Topic :: Internet'
        ,'Topic :: Software Development :: Libraries'
        ,'License :: OSI Approved :: GNU General Public License v3 (GPLv3)']
)
