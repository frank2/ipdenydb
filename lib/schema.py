#!/usr/bin/env python

import os
import sys

from martinellis import Address, CIDR

from ipdenydb.db import Database

__all__ = ['Countries', 'Country', 'Blocks', 'Block']

class Countries(object):
    TABLE = '''CREATE TABLE ipdenydb_countries
(
    id SERIAL PRIMARY KEY,
    shortform VARCHAR(2) NOT NULL,
    longform TEXT NOT NULL
)'''

    def countries(self):
        db = Database()
        db.query('SELECT id, shortform, longform FROM ipdenydb_countries')
        results = db.fetchall()
        db.disconnect()

        countries = list()

        for row in results:
            country_id, shortform, longform = row
            countries.append(Country(id=country_id, shortform=shortform, longform=longform))

        return countries

    def by_id(self, country_id):
        db = Database()
        db.query('SELECT id, shortform, longform FROM ipdenydb_countries WHERE id = %s', country_id)
        results = db.fetchone()
        db.disconnect()

        if results is None:
            raise ValueError('{} not found'.format(country_id))
        
        country_id, shortform, longform = results
        
        return Country(id=country_id, shortform=shortform, longform=longform)
    
    def by_shortform(self, shortform):
        db = Database()
        db.query('SELECT id, shortform, longform FROM ipdenydb_countries WHERE shortform = %s', shortform)
        results = db.fetchone()
        db.disconnect()

        if results is None:
            raise ValueError('{} not found'.format(shortform))
        
        country_id, shortform, longform = results
        
        return Country(id=country_id, shortform=shortform, longform=longform)

class Country(object):
    ID = None
    SHORTFORM = None
    LONGFORM = None

    def __init__(self, **kwargs):
        self.id = kwargs.setdefault('id', self.ID)
        self.shortform = kwargs.setdefault('shortform', self.SHORTFORM)
        self.longform = kwargs.setdefault('longform', self.LONGFORM)

        if self.id is None:
            raise ValueError('id cannot be None')

        if self.shortform is None:
            raise ValueError('shortform cannot be None')

        if self.longform is None:
            raise ValueError('longform cannot be None')

    def blocks(self, ipv4=False, ipv6=False):
        if not ipv4 and not ipv6:
            raise ValueError('IPv4 or IPv6 blocks must be selected')
        
        query = 'SELECT b.id, b.block FROM ipdenydb_countries AS c, ipdenydb_blocks AS b WHERE b.country_id = c.id AND c.id = %s'
        
        if ipv4 and not ipv6:
            query = '{} AND family(b.block) = 4'.format(query)
        elif ipv6 and not ipv4:
            query = '{} AND family(b.block) = 6'.format(query)

        db = Database()
        db.query(query, self.id)
        results = db.fetchall()
        db.disconnect()
        blocks = list()

        for row in results:
            block_id, block_data = row
            block_obj = Block(id=block_id, country=self, block=block_data)
            blocks.append(block_obj)

        return blocks

class Blocks(object):
    TABLE = '''CREATE TABLE ipdenydb_blocks
(
    id SERIAL PRIMARY KEY,
    country_id INT NOT NULL,
    block CIDR NOT NULL,
    FOREIGN KEY (country_id) REFERENCES ipdenydb_countries (id)
)'''

    def by_ip(self, ip_addr):
        db = Database()

        if isinstance(ip_addr, str):
            ip_addr = Address.blind_assertion(ip_addr)

        ip_addr = str(ip_addr) # convert it back into a string

        db.query('SELECT id, country_id, block FROM ipdenydb_blocks WHERE block >> %s', ip_addr)
        result = db.fetchone()
        db.disconnect()

        if result is None:
            return

        block_id, country_id, block = result
        return Block(id=block_id, country_id=country_id, block=block)
    
class Block(object):
    ID = None
    COUNTRY_ID = None
    BLOCK = None

    def __init__(self, **kwargs):
        self.id = kwargs.setdefault('id', self.ID)
        self.country_id = kwargs.setdefault('country_id', self.COUNTRY_ID)
        self.country = kwargs.setdefault('country', None)
        self.block = kwargs.setdefault('block', self.BLOCK)

        if not self.country is None:
            if not isinstance(self.country, Country):
                raise ValueError('country must be a Country object')
            else:
                self.country_id = self.country.id

        if self.id is None:
            raise ValueError('id cannot be None')

        if self.country_id is None:
            raise ValueError('country_id cannot be None')

        if self.block is None:
            raise ValueError('block cannot be None')

        if self.country is None:
            countries = Countries()
            self.country = countries.by_id(self.country_id)

    @property
    def cidr(self):
        return CIDR.blind_assertion(self.block)
