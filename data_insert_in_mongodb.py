#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import json
import pprint
from datetime import datetime

JSON_TO_INSERT = 'data/map.osm.json'
DB_CONNECTION = 'localhost:32768'
DB_NAME = 'udacity_datascience_for_business'


def get_db():
  from pymongo import MongoClient
  client = MongoClient(DB_CONNECTION)
  db = client[DB_NAME]
  return db


def main():
  db = get_db()
  insertError = []
#  print (db.collection_names(include_system_collections=False))
  datastore = None
  with open(JSON_TO_INSERT, 'r') as f:
    datastore = json.load(f)

  if datastore is not None:
    for d in datastore:
      try:
        if d is not None:
          db['node'].insert(d)
      except Exception as e:
        insertError.append(d)

  file_out = "{0}-error-to-insert-json.log".format(JSON_TO_INSERT)
  with codecs.open(file_out, "w") as fo:
    fo.write(str(insertError))


pprint.pprint('Inicio do Processo ' + str(datetime.now()))
main()
pprint.pprint('Fim Processo ' + str(datetime.now()))
