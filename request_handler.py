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
import db
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

# We're going to use D-Bus to communicate with external processes.
# Should make things clean, efficient, and cohesive


def __eprint__(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info[0] == 2:
    __eprint__("Please run with Python 3 as Python 2 is End-of-Life.")
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

    @dbus.service.method("org.draugeros.Request_Handler", in_signature='d', out_signature='s')
    def retrive_report(self, report_id: float) -> str:
        """Retrieve Installation report from DB"""
        try:
            pipe.send({'recv': float(report_id)})
        except ValueError:
            return '{"data": "ERROR: ValueError"}'
        while True:
            if self.pipe.poll():
                return f"{'data': { self.pipe.recv() }}"
            time.sleep(self.resp_time)


def Main(pipe, response_time):
    """Start up DBus listeners"""
    try:
        DBusGMainLoop(set_as_default=True)

        bus = dbus.SessionBus()
        name = dbus.service.BusName("org.draugeros.Request_Handler", bus)
        object = signal_handlers(bus, '/org/draugeros/Request_Handler',
                                 pipe, response_time)

        mainloop = GLib.MainLoop()
        mainloop.run()
    except:
        pass
