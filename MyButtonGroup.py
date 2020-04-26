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
import numpy as np

from PyQt5 import Qt
from PyQt5 import QtCore,QtGui
from PyQt5.QtWidgets import QWidget


class ButtonGroup(QWidget):
  def __init__(self,config,obj,function,config_name,buttonlist):
    QWidget.__init__(self)
    self.config = config
    self.obj = obj
    self.function = function
    self.config_name = config_name
    self.buttonlist = buttonlist
    self.inhibit = False
    self.obj.buttonClicked.connect(self.button_pressed)

  def process_value(self,value = None):
    if value == None:
      self.value = self.config[self.config_name]  
    else:
      self.config[self.config_name] = value  
      self.value = value
    self.inhibit = True
    self.buttonlist[self.value].setChecked(True)
    self.inhibit = False
      
  def get_value(self,value = None):
    self.process_value(value)
    return self.value
      
  def set_value(self,value = None):
    self.process_value(value)
    self.function(self.value)
    
  def button_pressed(self,button):
    self.value = self.buttonlist.index(button)
    self.process_value(self.value)
    self.function(self.value)

    
      
    
    
  