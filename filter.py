#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  filter.py
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
"""Filter Reports and ensure system security"""
from __future__ import print_function
import sys
import gnupg
import json
import time
import os
import shutil
import pyclamd as clamav


def eprint(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info[0] == 2:
    eprint("Please run with Python 3 as Python 2 is End-of-Life.")
    exit(2)


def setup_gpg_home(secrets_file):
    gpg = gnupg.GPG(gnupghome=os.getenv("HOME"))
    with open(secrets_file, "r") as file:
       pin = file.read().split("\n")[0]
    return gpg


def main(inbound: str, checked: str, sus: str, freq: float, secrets_file: str):
    """Filter inbound reports to ensure system security and report validity"""
    gpg = setup_gpg_home(secrets_file)
    av = clamav.ClamdAgnostic()
    while True:
        # STEP 1: Check for work
        file_list = os.listdir(inbound)
        if len(file_list) == 0:
            eprint("Nothing to scan. Exiting...")
            # sleep till next loop
            time.sleep(freq)

        # STEP 2: check file extension and name
        # so we at least have something. Check to ensure the file extention is right.
        first_step_file_list = []
        move = []
        for each in file_list:
            if each.split(".")[-1] == "dosir":
                if each.split("-")[0] == "installation_report":
                    first_step_file_list.append(each)
                    continue
            move.append(each)

        # STEP 3: virus scan
        # scan EVERYTHING for viruses. If it throws something, immedietly delete it
        second_step_file_list = []
        for each in first_step_file_list:
            path = inbound + "/" + each
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            results = av.scan_file(path)
            if results is None:
                second_step_file_list.append(each)
            else:
                eprint("WARNING: VIRUS DETECTED!")
                os.remove(path)
                eprint(f"FILE {each} DELETED FOR SAFETY REASONS.")

        checked_move = []
        for each in move:
            path = inbound + "/" + each
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            results = av.scan_file(path)
            if results is None:
                checked_move.append(each)
            else:
                eprint("WARNING: VIRUS DETECTED!")
                os.remove(path)
                eprint(f"FILE {each} DELETED FOR SAFETY REASONS.")

        # STEP 4: check size
        # check everything to ensure it's not over our size limit
        max_size = 5000000 # 5 MB
        third_step_file_list = []
        for each in second_step_file_list:
            if os.path.getsize(inbound + "/" + each) > max_size:
                eprint(f"{each} is greater than `max_size' ({max_size} bytes), despite passing AV and extension check")
                eprint("Removing $each as a precautionary measure...")
                os.remove(inbound + "/" + each)
            else:
                third_step_file_list.append(each)

        move = []
        for each in checked_move:
            if os.path.getsize(inbound + "/" + each) > max_size:
                eprint(f"{each} is greater than `max_size' ({max_size} bytes), despite passing AV and extension check")
                eprint("Removing $each as a precautionary measure...")
                os.remove(inbound + "/" + each)
            else:
                move.append(each)


        # STEP 5: decrypt
        # decrypt using GPG. if decryption failes, move to "suspicious" folder
        try:
            os.mkdir(checked)
        except FileExistsError:
            pass
        try:
            os.mkdir(sus)
        except FileExistsError:
            pass
        for each in third_step_file_list:
            try:
                with open(inbound + "/" + each, "rb") as file:
                    output = gpg.decrypt_file(file, passphrase=pin, output=checked + "/" + each)
            except:
                eprint(f"GPG decrypt failed for $each. Moving to suspicious folder ({sus})")
                eprint(f"Reason: {output.status}")
                shutil.move(inbound + "/" + each, sus + "/" + each)
            os.remove(inbound + "/" + each)

        for each in move:
            shutil.move(inbound + "/" + each, sus + "/" + each)

        # STEP 6: ensure valid JSON
        checked_files = os.listdir(checked)
        for each in checked_files:
            try:
                with open(checked + "/" + each, "r") as file:
                    json.load(file)
            except json.decoder.JSONDecodeError:
                shutil.move(checked + "/" + each, sus + "/" + each)
                eprint(f"{each} had invalid JSON data. Marked as suspicious.")
            except:
                shutil.move(checked + "/" + each, sus + "/" + each)
                eprint(f"{each} encountered an unknown error. Marked as suspicious.")

        # STEP 7: sleep till next loop
        time.sleep(freq)
