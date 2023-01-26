#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  db.py
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
"""handles input and output to the database in a multi-threaded,
thread-safe environment, through a simple API"""
from __future__ import print_function
import sys
import json
import os
import time
import shutil


def eprint(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info[0] == 2:
    eprint("Please run with Python 3 as Python 2 is End-of-Life.")
    exit(2)


def commit(db, name):
    """Commit DB to disk"""
    with open(name, "w+") as file:
        json.dump(db, file, indent=2)


def read(name):
    """Read DB into RAM"""
    with open(name, "r") as file:
        return json.load(file)


def recover(name):
    """Recover DB from corruption"""
    if not os.path.isfile(f"{name}.bak"):
        raise FileNotFoundError(f"Cannot find recovery file: {name}.bak")
    shutil.copy2(f"{name}.bak", name)


def backup(name):
    """Make a backup of the database"""
    if not os.path.isfile(name):
        raise FileNotFoundError(f"Cannot find recovery file: {name}")
    shutil.copy2(name, f"{name}.bak")


def main(pipe, freq, db_name):
    """DB management thread"""
    print("DB Running!")
    done = {"DONE": True}
    if not os.path.isfile(db_name):
        if not os.path.isfile(f"{db_name}.bak"):
            commit({}, db_name)
        else:
            recover(db_name)
    db = read(db_name)
    sleep_count = 0
    pipe.send({"STATUS": "READY"})
    time.sleep(0.1)
    modified = False
    while True:
        if not pipe.poll():
            if ((sleep_count > 1000) and modified):
                print("Backing up!")
                backup(db_name)
                sleep_count = 0
                modified = False
            else:
                sleep_count += 1
            time.sleep(freq * 2)
            continue
        cmd = pipe.recv()
        sleep_count = 0
        if "ADD" in cmd.keys():
            # add new entry to DB
            db[cmd["ADD"]['Installation Report Code']] = cmd["ADD"]
            print(f"ADDED REPORT: {cmd['ADD']['Installation Report Code']}")
            pipe.send(done)
            commit(db, db_name)
            modified = True
        elif "RECV" in cmd.keys():
            # pull data from DB
            output = None
            if "code" in cmd["RECV"]:
                try:
                    output = db[cmd["RECV"]["code"]]
                except KeyError:
                    eprint(f"Installation {cmd['RECV']['code']} requested but not found.")
            elif "in_report" in cmd["RECV"]:
                output = []
                for each in db:
                    if cmd["RECV"]["in_report"] in each.items():
                        output.append(each)
            elif "all" in cmd["RECV"]:
                output = db
            pipe.send({"DATA": output})
            modified = True
        elif "DEL" in cmd.keys():
            # delete data from DB
            if cmd["DEL"] in db:
                print(f"DELETED REPORT: {cmd['DEL']}")
                del db[cmd["DEL"]]
                pipe.send(done)
                modified = True
            else:
                eprint(f"REPORT REQUESTED TO BE DELETED BUT NOT FOUND: {cmd['DEL']}")
                pipe.send({"DONE": None})
        elif "CHECK" in cmd.keys():
            # check status of DB and DB thread
            score = 0
            if os.path.isfile(f"{db_name}.bak"):
                score += 1
            else:
                backup(db_name)
            if os.path.isfile(db_name):
                score += 1
            else:
                commit(db, db_name)
                backup(db_name)
            try:
                if json.dumps(db_name):
                    score += 1
            except:
                pass
            if score == 3:
                pipe.send({"STATUS": "GOOD"})
        elif "COMMIT" in cmd.keys():
            commit(db, db_name)
            pipe.send(done)
            modified = True
        elif "BACKUP" in cmd.keys():
            backup(db_name)
            pipe.send(done)
            modified = False
        elif "RECOVER" in cmd.keys():
            recover(db_name)
            pipe.send(done)
            modified = False
        elif "READ" in cmd.keys():
            db = read(db_name)
            pipe.send(done)
        else:
            pipe.send({"ERROR": "Command not understood"})
        time.sleep(freq)

