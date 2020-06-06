#!/usr/bin/env python

import argparse
import re
import sys

import requests

from ipdenydb.db import Database
from ipdenydb.schema import Countries, Blocks

if __name__ == '__main__':
    def install():
        db = Database()
        db.query(Countries.TABLE)
        db.query(Blocks.TABLE)
        db.commit()

        r = requests.get('https://ipdeny.com/ipblocks')
        countries = re.findall('<tr><td><p>(?P<longform>.*?) \((?P<shortform>[A-Z]{2})\)'
                               ,r.text)

        for c in countries:
            db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', *c)

        db.commit()
        update()
        
    def update():
        pass

    parser = argparse.ArgumentParser(description='Commandline tool for ipdenydb')
    parser.add_argument('-i', '--install'
                        ,action='store_true'
                        ,help='Install the tables and initialize the database.')
    parser.add_argument('-u', '--update'
                        ,action='store_true'
                        ,help='Update the database.')
    args = parser.parse_args(sys.argv[1:])

    if args.install:
        install()
    elif args.update:
        update()
    else:
        parser.print_help()
