link-press
==========

A Python script for taking a set of links and metadata and creating a WordPress linkblog post. This is my first Python program and I'm fairly certain the code is a mess. Hopefully as I learn more about Python this program will get better.

Requirements
------------

* Python 2.7.3
* python-wordpress-xmlrpc 1.5.2
* SQLite3

This was built on Fedora 17 x86_64, but should run on any Linux system with the proper libraries.

Roadmap
-------

* Add the ability to configure the publishing date so that the script can be run from a cron job.
* Add support for sending Pushover notifications. (http://pushover.net)

License
-------

link-press is released under the GPLv3+ license:
* http://gnu.org/licenses/gpl.html
