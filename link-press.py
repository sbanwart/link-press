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
import argparse
import sqlite3
import wordpress_xmlrpc as wp
import wordpress_xmlrpc.methods.posts as wp_posts

version = '0.8.3'
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

        cur.execute("SELECT id FROM links WHERE url = ?", [args.url.decode('utf8')])
        data = cur.fetchone()
        if not data:
            attribute_link_id = -1
            if args.attribute_url:
                cur.execute("SELECT id FROM attribute_links WHERE url = ?", [args.attribute_url.decode('utf8')])
                data = cur.fetchone()
                if not data:
                    values = [args.attribute_url.decode('utf8'), args.attribute_name.decode('utf8'), args.attribute_title.decode('utf8')]
                    cur.execute("INSERT INTO attribute_links (url, name, title) VALUES (?, ?, ?)", values)
                    cur.execute("SELECT last_insert_rowid()")
                    data = cur.fetchone()
                    attribute_link_id = data[0]
                else:
                    attribute_link_id = data[0]
                conn.commit()

            if attribute_link_id > 0:
                values = [args.url.decode('utf8'), args.name.decode('utf8'), args.category.decode('utf8'), attribute_link_id]
                cur.execute("INSERT INTO links (url, name, category, attribute_link_id) VALUES (?, ?, ?, ?)", values)
            else:
                values = [args.url.decode('utf8'), args.name.decode('utf8'), args.category.decode('utf8')]
                cur.execute("INSERT INTO links (url, name, category) VALUES (?, ?, ?)", values)
            conn.commit()

            tags = args.tags.decode('utf8').split(",")
            for tag in tags:
                cur.execute("SELECT id FROM tags WHERE name = ?", [tag])
                data = cur.fetchone()
                if not data:
                    cur.execute("INSERT INTO tags (name) VALUES (?)", [tag])
                    conn.commit()

            print "Link added to database."
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
    post_title = build_post_title()
    
    post_body = build_post_body()

    tag_list = build_tag_list()

    date_scheduled = ""
    if args.posting_date:
        date_scheduled = args.posting_date

    post = create_wp_post(post_title, post_body, tag_list, date_scheduled)

    client = create_wp_client()
    post_id = client.call(wp_posts.NewPost(post, False))

    update_title_counter()

    print "Blog post #%s successfully sent to WordPress." % (post_id)

def create_wp_client():
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT wp_uri, wp_username, wp_password FROM configuration")
        config = cur.fetchone()

        wp_uri = config[0]
        wp_username = config[1]
        wp_password = config[2]

        client = wp.Client(wp_uri, wp_username, wp_password)

        return client

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when getting configuration: %s" % err.args[0]
        sys.exit(1)
    
    finally:
        if conn:
            conn.close()

def create_wp_post(post_title, post_body, tag_list, date_scheduled):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT wp_category FROM configuration")
        config = cur.fetchone()

        wp_category = config[0]

        post = wp.WordPressPost()
        post.title = post_title
        post.description = post_body
        post.categories = [wp_category]
        post.tags = tag_list

        if date_scheduled:
            post.date_created = date_scheduled
       
        return post

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when getting configuration: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

def build_post_title():
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT title, title_counter FROM configuration")
        config = cur.fetchone()

        title = "%s %s" % (config[0], config[1])

        return title

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when getting configuration: %s" % err.args[0]
        sys.exit(1)
    
    finally:
        if conn:
            conn.close()
        
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
        categories.sort()

        post_body = ""
        for category in categories:
            post_body += "<p><strong>%s</strong></p>\n" % category
            post_body += "<ul>\n"

            cur.execute("SELECT url, name, attribute_link_id FROM links WHERE category = ?", category)
            links = cur.fetchall()

            for link in links:
                attribute_id = link[2]
                if attribute_id:
                    post_body += "<li><a title=\"%s\" href=\"%s\">%s</a><span style=\"color: #0000ff;\"> %s</span></li>\n" % (link[1], link[0], link[1], attribute_dict[attribute_id][3])
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

        tag_list = []
        for tag in tags:
            tag_list.append(tag[0])

        return tag_list

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when posting links: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

def update_title_counter():
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT title_counter FROM configuration")
        counter = cur.fetchone()

        cur.execute("UPDATE configuration SET title_counter = ?", [counter[0] + 1])
        conn.commit()

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when updating title counter: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

def clear(args):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("DELETE FROM links")
        cur.execute("DELETE FROM tags")
        cur.execute("DELETE FROM attribute_links")
        conn.commit()

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error when updating title counter: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

def update_configuration(args):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        if args.title_counter:
            cur.execute("UPDATE configuration SET title_counter = ?", [args.title_counter])

        if args.title:
            cur.execute("UPDATE configuration SET title = ?", [args.title])

        if args.wp_uri:
            cur.execute("UPDATE configuration SET wp_uri = ?", [args.wp_uri])

        if args.wp_username:
            cur.execute("UPDATE configuration SET wp_username = ?", [args.wp_username])

        if args.wp_password:
            cur.execute("UPDATE configuration SET wp_password = ?", [args.wp_password])

        if args.wp_category:
            cur.execute("UPDATE configuration SET wp_category = ?", [args.wp_category])

        if args.wp_author:
            cur.execute("UPDATE configuration SET wp_author = ?", [args.wp_author])

        conn.commit()

    except sqlite3.Error, err:
        if conn:
            conn.rollback()

        print "Error during configuration update: %s" % err.args[0]
        sys.exit(1)

    finally:
        if conn:
            conn.close()

def print_version(args):
    print """link-press %s
Copyright (C) 2012 Scott Banwart.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.\n""" % (version)

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
            cur.execute("CREATE TABLE configuration(title_counter INTEGER, title TEXT, wp_uri TEXT, wp_username TEXT, wp_password TEXT, wp_category TEXT)")
            cur.execute("INSERT INTO configuration (title_counter) VALUES (1)")
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
parser_post.add_argument('--posting_date', '-d')
parser_post.set_defaults(func = post_links)

parser_clear = subparsers.add_parser('clear')
parser_clear.set_defaults(func = clear)

parser_config = subparsers.add_parser('config')
parser_config.add_argument('--title_counter', '-c')
parser_config.add_argument('--title', '-t')
parser_config.add_argument('--wp_uri', '-u')
parser_config.add_argument('--wp_username', '-n')
parser_config.add_argument('--wp_password', '-p')
parser_config.add_argument('--wp_category', '-g')
parser_config.add_argument('--wp_author', '-a')
parser_config.set_defaults(func = update_configuration)

parser_version = subparsers.add_parser('version')
parser_version.set_defaults(func = print_version)

args = parser.parse_args()

init_db()

args.func(args)
