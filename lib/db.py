#!/usr/bin/env python

import json
import os
import sys

import psycopg2

__all__ = ['Database']

class Database(object):
    def __init__(self, **kwargs):
        config_file = os.path.join(sys.prefix, 'etc/ipdenydb.json')
        fp = open(config_file)
        self.config = json.load(fp)
        fp.close()

        self.handle = None
        self.cursor = None

    def connect(self):
        if not self.handle is None:
            return
        
        self.handle = psycopg2.connect(host=self.config['host']
                                       ,port=self.config['port']
                                       ,dbname=self.config['database']
                                       ,user=self.config['username']
                                       ,password=self.config['password'])

    def disconnect(self):
        if not self.cursor is None:
            self.close()
            
        if not self.handle is None:
            self.handle.close()

        self.handle = None

    def open(self):
        if not self.cursor is None:
            return

        if self.handle is None:
            self.connect()

        self.cursor = self.handle.cursor()

    def close(self):
        if not self.cursor is None:
            self.cursor.close()
            
        self.cursor = None

    def query(self, query, *args, **kwargs):
        self.open()

        if len(kwargs) > 0:
            self.cursor.execute(query, vars=kwargs)
        else:
            self.cursor.execute(query, vars=args)

    def commit(self):
        if self.handle is None:
            raise RuntimeError('no connection available')

        self.handle.commit()
        
    def fetchone(self):
        if self.cursor is None:
            raise RuntimeError('no cursor available')

        return self.cursor.fetchone()

    def fetchmany(self, size):
        if self.cursor is None:
            raise RuntimeError('no cursor available')

        return self.cursor.fetchmany(size)

    def fetchall(self):
        if self.cursor is None:
            raise RuntimeError('no cursor available')

        return self.cursor.fetchall()
