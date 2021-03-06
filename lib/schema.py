#!/usr/bin/env python

import os
import sys

from martinellis import Address as _Address
from martinellis import CIDR

from ipdenydb.db import Database

__all__ = ['Countries', 'Country', 'Blocks', 'Block', 'Addresses', 'Address']

class Countries(object):
    TABLE = '''CREATE TABLE ipdenydb_countries
(
    id SERIAL PRIMARY KEY,
    shortform VARCHAR(2) NOT NULL,
    longform TEXT NOT NULL
)'''

    @classmethod
    def countries(cls):
        db = Database()
        db.query('SELECT id, shortform, longform FROM ipdenydb_countries')
        results = db.fetchall()

        countries = list()

        for row in results:
            country_id, shortform, longform = row
            countries.append(Country(id=country_id, shortform=shortform, longform=longform))

        return countries

    @classmethod
    def by_id(cls, country_id):
        db = Database()
        db.query('SELECT id, shortform, longform FROM ipdenydb_countries WHERE id = %s', country_id)
        results = db.fetchone()

        if results is None:
            raise ValueError('{} not found'.format(country_id))
        
        country_id, shortform, longform = results
        
        return Country(id=country_id, shortform=shortform, longform=longform)

    @classmethod
    def by_shortform(cls, shortform):
        db = Database()
        db.query('SELECT id, shortform, longform FROM ipdenydb_countries WHERE shortform = %s', shortform)
        results = db.fetchone()

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
        blocks = list()

        for row in results:
            block_id, block_data = row
            block_obj = Block(id=block_id, country=self, block=block_data)
            blocks.append(block_obj)

        return blocks

    def random_block(self, ipv4=False, ipv6=False):
        if not ipv4 and not ipv6:
            raise ValueError('IPv4 or IPv6 blocks must be selected')
        
        query = 'SELECT b.id, b.block FROM ipdenydb_countries AS c, ipdenydb_blocks AS b WHERE b.country_id = c.id AND c.id = %s'
        
        if ipv4 and not ipv6:
            query = '{} AND family(b.block) = 4'.format(query)
        elif ipv6 and not ipv4:
            query = '{} AND family(b.block) = 6'.format(query)

        query = '{} ORDER BY random() LIMIT 1'.format(query)

        db = Database()
        db.query(query, self.id)
        result = db.fetchone()

        if result is None:
            raise RuntimeError('no results found')

        block_id, block = result
        block = Block(id=block_id, country=self, block=block)

        return block

class Blocks(object):
    TABLE = '''CREATE TABLE ipdenydb_blocks
(
    id SERIAL PRIMARY KEY,
    country_id INT NOT NULL,
    block CIDR NOT NULL,
    FOREIGN KEY (country_id) REFERENCES ipdenydb_countries (id)
)'''

    @classmethod
    def by_ip(cls, ip_addr):
        db = Database()

        db.query('SELECT id, country_id, block FROM ipdenydb_blocks WHERE block >> %s', str(ip_addr))
        result = db.fetchone()

        if result is None:
            return

        block_id, country_id, block = result
        return Block(id=block_id, country_id=country_id, block=block)

    @classmethod
    def by_id(cls, block_id):
        db = Database()

        db.query('SELECT id, country_id, block FROM ipdenydb_blocks WHERE id = %s', block_id)
        result = db.fetchone()

        if result is None:
            raise ValueError('no such block id {}'.format(block_id))

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
            self.country = Countries.by_id(self.country_id)

    @property
    def cidr(self):
        return CIDR.blind_assertion(self.block)

class Addresses(object):
    TABLE = '''CREATE TABLE ipdenydb_addresses
(
    id SERIAL PRIMARY KEY,
    block_id INT NOT NULL,
    address INET NOT NULL,
    FOREIGN KEY (block_id) REFERENCES ipdenydb_blocks (id)
)'''

    @classmethod
    def get_or_add(cls, address):
        db = Database()
        db.query('SELECT id, block_id, address FROM ipdenydb_addresses WHERE address = %s', str(address))
        result = db.fetchone()

        if result is None:
            block = Blocks.by_ip(address)

            if block is None:
                raise RuntimeError('address has no parent block')

            db.query('INSERT INTO ipdenydb_addresses (block_id, address) VALUES (%s, %s) RETURNING id', block.id, str(address))
            new_id = db.fetchone()[0]
            result = (new_id, block.id, str(address))

        addr_id, block_id, address = result
        return Address(id=addr_id, block_id=block_id, address=address)

class Address(object):
    ID = None
    BLOCK_ID = None
    ADDRESS = None
    
    def __init__(self, **kwargs):
        self.id = kwargs.setdefault('id', self.ID)
        self.block_id = kwargs.setdefault('block_id', self.BLOCK_ID)
        self.block = kwargs.setdefault('block', None)
        self.address = kwargs.setdefault('address', self.ADDRESS)

        if not self.block is None:
            if not isinstance(self.block, Block):
                raise ValueError('block must be a Block object')
            else:
                self.block_id = self.block.id

        if self.id is None:
            raise ValueError('id cannot be None')

        if self.block_id is None:
            raise ValueError('block_id cannot be None')

        if self.address is None:
            raise ValueError('address cannot be None')

        if self.block is None:
            self.block = Blocks.by_id(self.block_id)

    @property
    def family(self):
        return _Address.blind_assertion(self.address)
