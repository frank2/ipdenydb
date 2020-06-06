#!/usr/bin/env python

import os
import sys

from ipdenydb.db import Database

__all__ = ['Countries', 'Blocks']

class Countries(object):
    TABLE = '''CREATE TABLE ipdenydb_countries
(
    id SERIAL PRIMARY KEY,
    shortform VARCHAR(2) NOT NULL,
    longform TEXT NOT NULL
)'''

class Blocks(object):
    TABLE = '''CREATE TABLE ipdenydb_blocks
(
    id SERIAL PRIMARY KEY,
    country_id INT NOT NULL,
    block CIDR NOT NULL,
    FOREIGN KEY (country_id) REFERENCES ipdenydb_countries (id)
)'''
