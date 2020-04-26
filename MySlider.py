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
import time
import struct
import signal
import numpy as np

from PyQt5 import Qt
from PyQt5 import QtCore,QtGui
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QEvent

class Slider(QWidget):
  def __init__(self,config,obj,function,config_name,a,b,maxv = 200):
    QWidget.__init__(self)
    self.config = config
    self.obj = obj
    self.function = function
    self.config_name = config_name
    self.a = a
    self.b = b
    self.maxv = maxv
    self.obj.setRange(0,self.maxv)
    self.result = 0
    self.gain_name = None
    self.obj.installEventFilter(self)
    self.obj.valueChanged.connect(self.set_value)
  
  def visible(self,value):
    self.obj.setVisible(value)
    
  def set_range(self,a,b):
    self.a = a
    self.b = b
  
  def set_gain_name(self,name):
    self.gain_name = name
      
  def eventFilter(self, source, evt):
    t = evt.type()
    if t == QEvent.Wheel:
      v = (-5,5)[evt.angleDelta().y() > 0]
      pos = self.obj.value() + v
      pos = self.limit_range(pos)
      self.obj.setValue(pos)
      self.config[self.config_name] = pos
      return True
    return False
  
  def limit_range(self,v):
    v = (v,0)[v < 0]
    return (v,self.maxv)[v > self.maxv]
        
  def process_pos(self,pos):
    if pos == None:
      pos = self.config[self.config_name]
    pos = self.limit_range(pos)
    self.config[self.config_name] = pos
    self.obj.setValue(pos)
    self.result = self.ntrp(pos,0.0,self.maxv,self.a,self.b)
    self.obj.setToolTip("%.2f (adjust with mouse wheel)" % self.result)
      
  def get_value(self,pos = None):
    self.process_pos(pos)
    return self.result
      
  def set_value(self,pos = None):
    self.process_pos(pos)
    #print("new slider value: %.2f" % self.result)
    self.function(self.result,self.gain_name)
    
  def ntrp(self,x,xa,xb,ya,yb):
    return (x-xa) * (yb-ya) / (xb-xa) + ya
    
    