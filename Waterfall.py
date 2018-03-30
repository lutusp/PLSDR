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
import random

from PyQt5 import Qt
from PyQt5 import QtCore,QtGui
from PyQt5.QtGui import QColor,QImage,QPainter
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRect,QEvent

class WaterfallWidget(QWidget):
  def __init__(self,main,config,parent_widget):
    QWidget.__init__(self)
    self.main = main
    self.config = config
    self.parent_widget = parent_widget 
    parent_widget.addWidget(self)
    self.installEventFilter(self)
    self.setMouseTracking(True)
    self.dw = 0
    self.dh = 0
    self.line = 0
    self.bias = self.main.config['waterfall_bias']
    self.drawing = False
    self.setup1()
    self.setup2()
    
  def eventFilter(self, object, evt):
    if evt.type() == QEvent.Wheel:
      self.bias += (-4,4)[evt.angleDelta().y() > 0]
    return False
  
  def setup1(self):
    self.colors = []
    for n in range(256):
      h = self.ntrp(n,0,256,240,60)
      cn = self.ntrp(n,0,256,80,255)
      self.colors.append(QColor.fromHsv(h,255.0,cn))
      
  def setup2(self):
    dw = self.dw
    dh = self.dh
    self.acquire_essential()
    if dw != self.dw or dh != self.dh:
      self.image = QImage(self.dw,self.dh,QImage.Format_RGB32)
      p = QPainter(self.image)
      p.fillRect(0, 0, self.width(), self.height(),QtGui.QColor(0,0,0))
      
  def acquire_essential(self):
    self.dh = self.height()
    self.dw = self.width()
  
  def ntrp(self,x,xa,xb,ya,yb):
    return (x-xa)*(yb-ya)/(xb-xa) + ya
      
  def accept_data_line(self,array):
    if not self.drawing and self.isVisible():
      self.line = (self.line - 1) % self.dh
      self.drawing = True
      qp = QPainter(self.image)
      
      la = len(array)
      ox = None
      for x,y in enumerate(array):
        x = self.ntrp(x,0,la,0,self.dw)
        y = int(self.ntrp(y*4+self.bias,self.config['dbscale_lo'],self.config['dbscale_hi'],0,255))
        y = (y,0)[y < 0]
        y = (y,255)[y > 255]
        if ox != None:
          qp.setPen(self.colors[y])
          qp.drawLine(ox,self.line,x,self.line)
        ox = x
      self.update()
    
  def paintEvent(self,event):
    if self.isVisible():
      self.drawing = True
      self.setup2()
      qp = QtGui.QPainter(self)
      ha = self.line
      hb = self.dh - ha
      
      fa = QRect(0,ha,self.dw,hb)
      fb = QRect(0,0,self.dw,ha)
      
      ta = QRect(0,0,self.dw,hb)
      tb = QRect(0,hb,self.dw,ha)
      
      qp.drawImage(ta,self.image,fa)
      qp.drawImage(tb,self.image,fb)
      self.drawing = False
    
    