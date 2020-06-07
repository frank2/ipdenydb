#!/usr/bin/env python

import argparse
import os
import re
import sys
import tarfile
import tempfile

import requests

from ipdenydb.db import Database
from ipdenydb.schema import Countries, Blocks

def install():
    db = Database()
        
    print('[*] Creating tables...')
    db.query(Countries.TABLE)
    db.query(Blocks.TABLE)
    db.commit()

    print('[*] Adding countries...')
    r = requests.get('https://ipdeny.com/ipblocks')
    countries = re.findall('<tr><td><p>(?P<longform>.*?) \((?P<shortform>[A-Z]{2})\)'
                           ,r.text)
        
    for c in countries:
        db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', *c)
        print('[.] ... {} ({})'.format(*c))

    print('[*] Adding missing entries...')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'SAINT BARTHELEMY', 'BL')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'GUERNSEY', 'GG')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'SINT MAARTEN', 'SX')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'SAINT MARTIN', 'MF')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'BONAIRE', 'BQ')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'CURACAO', 'CW')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'ASIA-PACIFIC REGION', 'AP')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'SOUTH SUDAN', 'SS')
    db.query('INSERT INTO ipdenydb_countries (longform, shortform) VALUES (%s, %s)', 'EUROPE', 'EU')
        
    db.commit()
    update()

def country_update(family, tarball):
    tarball = tarfile.open(tarball, 'r:gz')
    db = Database()

    for tarinfo in tarball:
        if tarinfo.name == '.' or tarinfo.name == './MD5SUM':
            continue

        shortform = tarinfo.name.split('/')[1]
        shortform = shortform.split('.')[0]
        shortform = shortform.upper()
        countries = Countries()
        country = countries.by_shortform(shortform)

        print('[*] Extracting {}...'.format(shortform))

        fp = tarball.extractfile(tarinfo)
        blockdata = fp.read()
        fp.close()

        blockdata = blockdata.decode('utf8')
        new_blocks = blockdata.split('\n')
        new_blocks.pop() # remove the blank entry
        new_blocks = set(new_blocks)

        print('[*] Diffing {}...'.format(shortform))
        
        db.query('SELECT block FROM ipdenydb_blocks WHERE country_id = %s AND family(block) = %s', country.id, family)
        results = db.fetchall()
        current_blocks = list()

        for row in results:
            current_blocks.append(row[0])

        current_blocks = set(current_blocks)

        added_blocks = new_blocks - current_blocks
        deleted_blocks = current_blocks - new_blocks

        print('[*] {} blocks added, {} blocks removed.'.format(len(added_blocks), len(deleted_blocks)))

        for block in deleted_blocks:
            db.query('DELETE FROM ipdeny_blocks WHERE block=%s', block)

        print('[*] Committing deletions...')
        db.commit()
        
        for block in added_blocks:
            db.query('INSERT INTO ipdenydb_blocks (country_id, block) VALUES (%s, %s)', country.id, block)

        print('[*] Committing additions...')
        db.commit()

        print('[*] {} finished.'.format(shortform))

    db.disconnect()
        
def update():
    print('[*] Grabbing IPv4 tarball...')
    r = requests.get('https://www.ipdeny.com/ipblocks/data/countries/all-zones.tar.gz')

    print('[*] Unpacking IPv4 tarball...')
    tarball_tmp = tempfile.NamedTemporaryFile(delete=False)
    tarball_tmp.write(r.content)
    tarball_tmp.close()

    country_update(4, tarball_tmp.name)
    os.unlink(tarball_tmp.name)
    
    print('[*] Grabbing IPv6 tarball...')
    r = requests.get('https://www.ipdeny.com/ipv6/ipaddresses/blocks/ipv6-all-zones.tar.gz')

    print('[*] Unpacking IPv6 tarball...')
    tarball_tmp = tempfile.NamedTemporaryFile(delete=False)
    tarball_tmp.write(r.content)
    tarball_tmp.close()

    country_update(6, tarball_tmp.name)
    os.unlink(tarball_tmp.name)

    print('[*] Update complete.')
        
if __name__ == '__main__':
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
