#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  request_handler.py
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
"""handles requests for data from the DB."""
from __future__ import print_function
import sys
import time
import json
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import GLib

# We're going to use D-Bus to communicate with external processes.
# Should make things clean, efficient, and cohesive


def eprint(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info[0] == 2:
    eprint("Please run with Python 3 as Python 2 is End-of-Life.")
    exit(2)


class signal_handlers(dbus.service.Object):
    """Signal Handlers for DBus"""
    def __init__(self, bus_obj, bus_loc, pipe, response_time):
        """Make pipe available to whole class"""
        super().__init__(bus_obj, bus_loc)
        self.pipe = pipe
        try:
            self.resp_time = float(response_time)
        except ValueError:
            self.resp_time = 0.1

    @dbus.service.method("org.draugeros.Request_Handler", in_signature='s', out_signature='s')
    def get_report_by_id(self, report_id: str) -> str:
        """Retrieve Installation report from DB"""
        print(f"Requesting data on report: {report_id}")
        try:
            self.pipe.send({'RECV': {"code": str(report_id)}})
        except ValueError:
            return '{"DATA": "ERROR: ValueError"}'
        while True:
            if self.pipe.poll():
                return json.dumps(self.pipe.recv())
            #  print("Waiting on reply...")
            time.sleep(self.resp_time)

    @dbus.service.method("org.draugeros.Request_Handler", in_signature='s', out_signature='s')
    def get_report_by_contents(self, search_string: str) -> str:
        """Retrive installation reports from DB that match certain data"""
        try:
            search_term = json.loads(search_string)
        except:
            return "{'DATA': 'ERROR: Need JSON formatted string'}"
        accepted_keys = ["system-installer Version", "OS", "CPU INFO", "PCIe / GPU INFO",
                         "RAM / SWAP INFO", "DISK SETUP", "INSTALLATION LOG", "CUSTOM MESSAGE", "MODE"]
        for each in search_term:
            if each not in accepted_keys:
                return f"{'DATA': 'ERROR: key {each} not recognized.'}"
        print(f"Requesting data on reports containing:\n{ json.dumps(search_term, indent=2) }")
        self.pipe.send({"RECV": {"in_report": search_term}})
        while True:
             if self.pipe.poll():
                 return json.dumps(self.pipe.recv())
             #  print("Waiting on reply...")
             time.sleep(self.resp_time)


def main(pipe, response_time):
    """Start up DBus listeners"""
    #try:
    DBusGMainLoop(set_as_default=True)

    bus = dbus.SessionBus()
    name = dbus.service.BusName("org.draugeros.Request_Handler", bus)
    object = signal_handlers(bus, '/org/draugeros/Request_Handler',
                                 pipe, response_time)

    mainloop = GLib.MainLoop()
    mainloop.run()
    #except:
     #   eprint("An error has occured on the receiver thread.")
      #  pass
