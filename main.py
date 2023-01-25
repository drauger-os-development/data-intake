#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  main.py
#
#  Copyright 2023 Thomas Castleman <contact@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""Explain what this program does here!!!"""
from __future__ import print_function
import sys
import multiprocessing as multiproc
import json
import time
import os

# all our libraries will each fun as their own thread
import db
import request_handler as rh
import intake_handler as ih


def __eprint__(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info[0] == 2:
    __eprint__("Please run with Python 3 as Python 2 is End-of-Life.")
    exit(2)

# get length of argv
ARGC = len(sys.argv)

# Load settings
with open("settings.json", "r") as file:
    SETTINGS = json.load(file)

# handle path shortcuts
for each in SETTINGS:
    if "reports" in each:
        if SETTINGS[each][0] == "~":
            SETTINGS[each] = os.getenv("HOME") + SETTINGS[each][1:]

# set up pipes
db_parent, db_pipe = multiproc.Pipe()
intake_parent, intake_pipe = multiproc.Pipe()
request_parent, request_pipe = multiproc.Pipe()

# setup threads
db_thread = multiproc.Process(target=db.main, args=(db_parent, SETTINGS["response_frequency"],
                                                    SETTINGS["db_name"]))
intake_thread = multiproc.Process(target=ih.main, args=(intake_parent,
                                SETTINGS["intake_frequency"],
                                SETTINGS["accepted_reports"]))
request_thread = multiproc.Process(target=rh.main, args=(request_parent,
                                                         SETTINGS["response_frequency"]))

# start threads
db_thread.start()
intake_thread.start()
request_thread.start()

# coordinate process communication and keep things thread safe
flip_flop = True
time.sleep(0.01)
# make sure DB is ready to go before anything else
while True:
    if db_pipe.poll():
        if db_pipe.recv() == {"STATUS": "READY"}:
            break
    time.sleep(0.1)

while True:
    if flip_flop:
        if db_pipe.poll():
            data = db_pipe.recv()
            if (("DATA" in data.keys()) and (not flip_flop)):
                request_pipe.send(data)
            else:
                intake_pipe.send(data)
        flip_flop = None
    elif flip_flop is None:
	flip_flop = False
        if intake_pipe.poll():
             db_pipe.send(intake_pipe.recv())
    else:
        if request_pipe.poll():
             db_pipe.send(request_pipe.recv())
        flip_flop = True
    time.sleep(SETTINGS["response_frequency"])
