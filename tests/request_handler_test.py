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
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

# We're going to use D-Bus to communicate with external processes.
# Should make things clean, efficient, and cohesive


def eprint(*args, **kwargs):
    """Make it easier for us to print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


if sys.version_info[0] == 2:
    eprint("Please run with Python 3 as Python 2 is End-of-Life.")
    exit(2)


bus = dbus.SessionBus()
rh = bus.get_object("org.draugeros.Request_Handler", '/org/draugeros/Request_Handler')
rh_int = dbus.Interface(rh, dbus_interface="org.draugeros.Request_Handler")

print(rh_int.get_report_by_id("0"))
