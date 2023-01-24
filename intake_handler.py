#!/usr/bin/env python3
import os
import json

# This file will read in installation reports, attempt to clean up any formatting, check for SQL injections
# and random binary data, then pass it along to the database handler which will add it to the database
