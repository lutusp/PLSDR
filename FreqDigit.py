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

class FreqDigit(QWidget):
  def __init__(self,s,parent,lbl):
    QWidget.__init__(self)
    self.parent = parent
    self.zero = False
    self.mouseover = False
    self.lbl = lbl
    try:
      self.value = int(s)
    except:
      self.value = 0
    self.lbl.installEventFilter(self)
  
  def eventFilter(self, source, evt):
    t = evt.type()
    if t == QEvent.Wheel:
      self.mouse_scroll_event(evt)
      return True
    elif t == QEvent.ContextMenu:
      self.parent.erase_digits_to_right(self)
      self.reset_color()
      return True
    return False
    
  def event_box(self):
    return self.eventbox
    
  def set_value(self,n):
    self.value = n % 10
    self.lbl.setText("%d" % self.value)
    self.lbl.setToolTip("Right-click to clear lesser digits")
    self.reset_color()
  def mouse_enter(self,evt,data):  
    self.mouseover = True
    self.reset_color()
  def mouse_exit(self,evt,data):
    self.mouseover = False
    self.reset_color()
  def reset_color(self):
    if self.zero:
      self.lbl.setProperty('accessibleName' , 'FreqDigitDark')
    else:
      self.lbl.setProperty('accessibleName' , 'FreqDigit')
    self.lbl.setStyle(self.lbl.style())
    
  def mouse_scroll_event(self,evt):
    if evt.angleDelta().y() > 0:
      self.value += 1
    else:
      self.value -= 1
    self.parent.process_mouse_frequency_change()
    self.reset_color()

