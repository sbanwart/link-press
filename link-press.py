#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os
import os.path

user_home = os.path.expanduser("~")
data_dir = ".link-press"
dbname = "link-press.db"

data_path = os.path.join(user_home, data_dir)

if not os.path.isdir(data_path):
    os.makedirs(data_path)

db_path = os.path.join(data_path, dbname)

dbConn = sqlite3.connect(db_path)
cur = dbConn.cursor()
cur.execute("SELECT SQLITE_VERSION()")

data = cur.fetchone()

print "SQLite version: %s" % data

dbConn.close()
