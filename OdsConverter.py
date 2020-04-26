#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#**************************************************************************
#   Copyright (C) 2018, Paul Lutus                                        *
#                                                                         *
#   This program is free software; you can redistribute it and/or modify  *
#   it under the terms of the GNU General Public License as published by  *
#   the Free Software Foundation; either version 2 of the License, or     *
#   (at your option) any later version.                                   *
#                                                                         *
#   This program is distributed in the hope that it will be useful,       *
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#   GNU General Public License for more details.                          *
#                                                                         *
#   You should have received a copy of the GNU General Public License     *
#   along with this program; if not, write to the                         *
#   Free Software Foundation, Inc.,                                       *
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#**************************************************************************

import re
import sys
import os
import ast
import time
import struct
import signal
import zipfile

class OdsToArray():

  def extract_simple(self,data,tag):
    return re.findall('(?s)<%s[^/|>]*?>(.*?)</%s>' % (tag,tag),str(data))

  def extract_complex(self,data,tag):
    output = []
    # must capture open and closed tags, both with repeat specifiers
    array = re.findall('(?s)(<%s[^/>]*?/>)|(<%s[^/>]*?>.*?)</%s>' % (tag,tag,tag),data)
    for tup in array:
      for datum in tup:
        n = 1
        if re.search('table:number-columns-repeated',datum):
          # get column-repeat value
          sn = re.sub('.*table:number-columns-repeated=\"(\d+)\".*','\\1',datum)
          n = int(sn)
        if re.search('/>',datum):
          # repeat empty columns
          if(n > 1):
            n = min(n,self.record_sz - len(output))
          for i in range(n):
            output.append('')
        else:
          # now strip out the residual table tag
          datum = re.sub('<table.*?>','',datum)
          if(len(datum) > 0):
            # repeat data columns
            for i in range(n):
              output.append(datum)
    return output

  def extract_record(self,row):
    output = []
    n = 0
    fields = self.extract_complex(row,'table:table-cell')
    for field in fields:
      content = self.extract_simple(field,'text:p')
      if(len(content) > 0):
        n += 1
        output.append(content[0])
      else:
        output.append('')
    if(n > 0):
      self.record_sz = max(len(output),self.record_sz)
      return output
    else:
      return None

  def array_from_path(self,path):
    zf = zipfile.ZipFile(path,'r')
    with zf.open('content.xml') as f:
      data = f.read()
    zf.close()
    array = []
    self.record_sz = 0
    sheets = self.extract_simple(data,'office:spreadsheet')
    for sheet in sheets:
      tables = self.extract_simple(sheet,'table:table')
      for table in tables:
        rows = self.extract_simple(table,'table:table-row')
        for row in rows:
          record = self.extract_record(row)
          if(record and len(record) > 0):
            array.append(record)
    return array
