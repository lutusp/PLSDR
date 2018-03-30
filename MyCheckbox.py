#!/usr/bin/env python
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

class Checkbox(QWidget):
  def __init__(self,main,obj,function,config_name):
    QWidget.__init__(self)
    self.main = main
    self.obj = obj
    self.function = function
    self.config_name = config_name
    self.state = False
    self.obj.clicked.connect(self.set_value)
    
  def process_state(self,state):
    if state == None:
      state = self.main.config[self.config_name]  
    else:
      self.main.config[self.config_name] = state
    self.obj.setChecked(state)
    self.state = state
      
  def get_value(self,state = None):
    self.process_state(state)
    return self.state
  
  def get_value_as_letter(self):
    return ('N','Y')[self.state]
        
  def set_value(self,state = None):
    self.process_state(state)
    self.function(self.state)
    
    
    