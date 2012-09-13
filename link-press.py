#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import sqlite3
import argparse

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
        cur.execute("CREATE TABLE links(id INTEGER PRIMARY KEY, url TEXT, title TEXT, attribute_link_id INTEGER)")
        cur.execute("CREATE TABLE tags(id INTEGER PRIMARY KEY, name TEXT)")
        cur.execute("CREATE TABLE attribute_links(id INTEGER PRIMARY KEY, url TEXT, name TEXT, title TEXT)")
        dbConn.commit()
    
    parser = argparse.ArgumentParser(description = 'Create a link blog entry and post it to WordPress')
    parser.add_argument('url')
    parser.add_argument('name')
    parser.add_argument('category')
    parser.add_argument('tags')
    parser.add_argument('--attribute_url', '-u')
    parser.add_argument('--attribute_title', '-t')
    parser.add_argument('--attribute_name', '-n')

    args = parser.parse_args()
except sqlite3.Error, err:
    if dbConn:
        dbConn.rollback()

    print "Error during database check: %s" % err.args[0]
    sys.exit(1)

finally:
    if dbConn:
        dbConn.close()
