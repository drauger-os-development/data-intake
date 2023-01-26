#!/bin/bash
# -*- coding: utf-8 -*-
#
#  setup.sh
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
set -Ee
set -o pipefail
echo "Installing Dependencies . . ."
sudo apt install --assume-yes $(<requirements_apt.txt)
# Install if not yet installed, update otherwise
username=$(whoami)
echo "Configuring your system . . ."
sudo cp -v data-intake.service /etc/systemd/system/data-intake.service
sudo sed -i "s:<path to>:$PWD:g" /etc/systemd/system/data-intake.service
sudo sed -i "s:<username>:$username:g" /etc/systemd/system/data-intake.service

echo "Enabling site and restarting Nginx . . ."
sudo systemctl enable data-intake
sudo systemctl start data-intake
git log | grep "^commit " | head -n1 | awk '{print $2}' > .git_commit_number
echo "Data Intake and Processing has been set up!"
