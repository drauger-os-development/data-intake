#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  intake_handler.py
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
"""read in installation reports, attempt to clean up any formatting, check for SQL injections
and random binary data, then pass it along to the database handler which will add it to the database
"""
from __future__ import print_function
import sys
import os
import json
import time


def eprint(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info[0] == 2:
    eprint("Please run with Python 3 as Python 2 is End-of-Life.")
    exit(2)


def main(pipe, loop_freq, intake_dir):
    """Handle intake of installation reports"""
    while True:
        reports = os.listdir(intake_dir)
        for each in reports:
            try:
                with open(intake_dir + "/" + each, "r") as file:
                    report = json.load(file)
            except:
                eprint(f"Could not load report {each}. Discarding...")
                os.remove(intake_dir + "/" + each)
            with open(intake_dir + "/" + each, "r") as file:
                data = json.load(file)
            pipe.send({"ADD": data})
            count = 0
            while True:
                if not pipe.poll():
                    time.sleep(2)
                    continue
                resp = pipe.recv()
                if ((resp == {"DONE": True}) and (count < 3)):
                    break
                else:
                    if count == 3:
                        pipe.send({"RECOVER": None})
                    elif count == 4:
                        pipe.send({"READ": None})
                        pipe.send({"ADD": data})
                        count = 0
                    elif count < 3:
                        pipe.send({"ADD": data})
                    count += 1
            os.remove(intake_dir + "/" + each)
        time.sleep(loop_freq)
