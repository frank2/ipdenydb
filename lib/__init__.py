#!/usr/bin/env python

import argparse
import json
import os
import sys

import psycopg2

country_table = '''CREATE TABLE ipdenydb_countries
(
    id SERIAL,
    shortform VARCHAR(2) NOT NULL,
    longform TEXT NOT NULL
);'''

block_table = '''CREATE_TABLE ipdenydb_blocks
(
    id SERIAL,
    country_id INT NOT NULL,
    block CIDR NOT NULL,
    FOREIGN KEY (country_id) REFERENCES ipdenydb_countries (id)
);'''

if __name__ == '__main__':
    pass
