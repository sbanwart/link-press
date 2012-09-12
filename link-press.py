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

try:
    dbConn = sqlite3.connect(db_path)
    cur = dbConn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'links'")
    data = cur.fetchone()

    if not data:
        print "Building database tables"
        cur.execute("CREATE TABLE links(id INTEGER PRIMARY KEY, url TEXT, title TEXT, attribute_link_id INTEGER)")
        cur.execute("CREATE TABLE tags(id INTEGER PRIMARY KEY, name TEXT)")
        cur.execute("CREATE TABLE attribute_links(id INTEGER PRIMARY KEY, url TEXT, name TEXT, title TEXT)")
        dbConn.commit()
    else:
        print "Database ready"

except sqlite3.Error, err:
    if dbConn:
        dbConn.rollback()

    print "Error during database check: %s" % err.args[0]
    sys.exit(1)

finally:
    if dbConn:
        dbConn.close()
