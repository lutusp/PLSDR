#!/usr/bin/env python
# -*- coding: utf-8 -*-

# **************************************************************************
#   Copyright (C) 2019, Adam Hajduk                                        *
#                                                                          *
#   This program is free software; you can redistribute it and/or modify   *
#   it under the terms of the GNU General Public License as published by   *
#   the Free Software Foundation; either version 2 of the License, or      *
#   (at your option) any later version.                                    *
#                                                                          *
#   This program is distributed in the hope that it will be useful,        *
#   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
#   GNU General Public License for more details.                           *
#                                                                          *
#   You should have received a copy of the GNU General Public License      *
#   along with this program; if not, write to the                          *
#   Free Software Foundation, Inc.,                                        *
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.              *
# **************************************************************************

import xml.etree.ElementTree as ET
import csv
import sys

if len(sys.argv) != 3:
    print('Script converting band plane setup data from SDR# format into format used by PLSDR')
    print('Usage: %s input.xml output.csv' % sys.argv[0])
    exit(0)

tree = ET.parse(sys.argv[1])
f = open(sys.argv[2], 'w')

root = tree.getroot()
csvwriter = csv.writer(f)
head = ['Name','Mode','Freq MHz','Comment']
csvwriter.writerow(head)

for entry in root.findall('RangeEntry'):
    row = []
    name = entry.get('minFrequency')
    row.append(name)
    mode = entry.get('mode')
    strMode = ''
    if mode != None:
        strMode = str(mode).lower()
    row.append(strMode)
    minFreq = entry.get('minFrequency')
    row.append(float(minFreq) / 1000000.0)
    comment = entry.text
    row.append(comment.replace(",", " -"))
    csvwriter.writerow(row)
f.close()
