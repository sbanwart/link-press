#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# link-press.py
#
# Copyright © 2012 Scott Banwart <sbanwart@rogue-technology.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
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
        cur.execute("CREATE TABLE links(id INTEGER PRIMARY KEY, url TEXT, name TEXT, category, attribute_link_id INTEGER)")
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

    cur.execute("SELECT id FROM links WHERE url = ?", [args.url])
    data = cur.fetchone()
    if not data:
        attribute_link_id = -1
        if args.attribute_url:
            cur.execute("SELECT id FROM attribute_links WHERE url = ?", [args.attribute_url])
            data = cur.fetchone()
            if not data:
                values = [args.attribute_url, args.attribute_name, args.attribute_title]
                cur.execute("INSERT INTO attribute_links (url, name, title) VALUES (?, ?, ?)", values)
                cur.execute("SELECT last_insert_rowid()")
                data = cur.fetchone()
                attribute_link_id = data[0]
            else:
                attribute_link_id = data[0]
            dbConn.commit()

        if attribute_link_id > 0:
            values = [args.url, args.name, args.category, attribute_link_id]
            cur.execute("INSERT INTO links (url, name, category, attribute_link_id) VALUES (?, ?, ?, ?)", values)
        else:
            values = [args.url, args.name, args.category]
            cur.execute("INSERT INTO links (url, name, category) VALUES (?, ?, ?)", values)
        dbConn.commit()

        tags = args.tags.split(",")
        for tag in tags:
            cur.execute("SELECT id FROM tags WHERE name = ?", [tag])
            data = cur.fetchone()
            if not data:
                cur.execute("INSERT INTO tags (name) VALUES (?)", [tag])
                dbConn.commit()
    else:
        print "Link already exists in the database"
except sqlite3.Error, err:
    if dbConn:
        dbConn.rollback()

    print "Error during database check: %s" % err.args[0]
    sys.exit(1)

finally:
    if dbConn:
        dbConn.close()
