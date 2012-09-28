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

    
def add_link(args):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

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
                conn.commit()

            if attribute_link_id > 0:
                values = [args.url, args.name, args.category, attribute_link_id]
                cur.execute("INSERT INTO links (url, name, category, attribute_link_id) VALUES (?, ?, ?, ?)", values)
            else:
                values = [args.url, args.name, args.category]
                cur.execute("INSERT INTO links (url, name, category) VALUES (?, ?, ?)", values)
            conn.commit()

            tags = args.tags.split(",")
            for tag in tags:
                cur.execute("SELECT id FROM tags WHERE name = ?", [tag])
                data = cur.fetchone()
                if not data:
                    cur.execute("INSERT INTO tags (name) VALUES (?)", [tag])
                    conn.commit()
        else:
            print "Link already exists in the database"
    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when adding a link: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

def post_links(args):
    post_body = build_post_body()

    tag_list = build_tag_list()

    print post_body

    print tag_list
        
def build_post_body():
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT id, url, name, title FROM attribute_links")
        attribute_links = cur.fetchall()

        marker = ""
        attribute_dict = {}
        for link in attribute_links:
            marker += "*"
            attribute_data = [link[1], link[2], link[3], marker]
            attribute_dict[link[0]] = attribute_data

        cur.execute("SELECT DISTINCT category FROM links")
        categories = cur.fetchall()

        post_body = ""
        for category in categories:
            post_body += "<p><strong>%s</strong></p>\n" % category
            post_body += "<ul>\n"

            cur.execute("SELECT url, name, attribute_link_id FROM links WHERE category = ?", category)
            links = cur.fetchall()

            for link in links:
                attribute_id = link[2]
                if attribute_id:
                    post_body += "<li><a title=\"%s\" href=\"%s\">%s</a></li> <span style=\"color: #0000ff;\">%s</span>\n" % (link[1], link[0], link[1], attribute_dict[attribute_id][3])
                else:
                    post_body += "<li><a title=\"%s\" href=\"%s\">%s</a></li>\n" % (link[1], link[0], link[1])

            post_body += "</ul>\n"

        for key in attribute_dict:
            post_body += "<p><span style=\"color: #0000ff;\">%s</span> Courtesy of <a title=\"%s\" href=\"%s\">%s</a>.</p>\n" % (attribute_dict[key][3], attribute_dict[key][2], attribute_dict[key][0], attribute_dict[key][1])

        return post_body

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when posting links: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

def build_tag_list():
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT name FROM tags")
        tags = cur.fetchall()

        tag_list = ""
        for tag in tags:
            tag_list += "%s," % (tag)

        return tag_list

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when posting links: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()


def init_db():
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'links'")
        data = cur.fetchone()

        if not data:
            cur.execute("CREATE TABLE links(id INTEGER PRIMARY KEY, url TEXT, name TEXT, category, attribute_link_id INTEGER)")
            cur.execute("CREATE TABLE tags(id INTEGER PRIMARY KEY, name TEXT)")
            cur.execute("CREATE TABLE attribute_links(id INTEGER PRIMARY KEY, url TEXT, name TEXT, title TEXT)")
            conn.commit()

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error during database check: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

parser = argparse.ArgumentParser(description = 'Create a link blog entry and post it to WordPress')
subparsers = parser.add_subparsers()

parser_add = subparsers.add_parser('add')
parser_add.add_argument('url')
parser_add.add_argument('name')
parser_add.add_argument('category')
parser_add.add_argument('tags')
parser_add.add_argument('--attribute_url', '-u')
parser_add.add_argument('--attribute_title', '-t')
parser_add.add_argument('--attribute_name', '-n')
parser_add.set_defaults(func = add_link)

parser_post = subparsers.add_parser('post')
parser_post.set_defaults(func = post_links)

args = parser.parse_args()

init_db()

args.func(args)
