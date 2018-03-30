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
import math

from PyQt5 import Qt
from PyQt5 import QtCore,QtGui
from PyQt5.QtCore import QEvent
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor,QImage,QPainter,QFont,QGuiApplication

class FFTDispWidget(QWidget):
  def __init__(self,main,config,parent_widget):
    QWidget.__init__(self)
    self.main = main
    self.config = config
    self.parent_widget = parent_widget
    parent_widget.addWidget(self)
    self.dw = None
    self.dh = None
    self.dwd2 = None
    self.data = None
    self.drawing = False
    self.mousepos = None
    self.mouse_startx = None
    self.mouse_starty = None
    self.mp = None
    self.zoom = None
    self.mousex = 0
    self.mousey = 0
    self.mpa = 0
    self.mpb = 1
    self.ss = 0
    # this smooths out the s-meter reading
    self.integ_constant = 1/5.0
    self.disp_trace_color = QColor(config['disp_trace_color'])
    self.disp_text_color = QColor(config['disp_text_color'])
    self.disp_vline_color = QColor(config['disp_vline_color'])
    self.black_color = QColor(0,0,0)
    self.monospace_font = QFont("monospace")
    self.process_zoom(self.config['fft_zoom'])
    self.installEventFilter(self)
    self.setMouseTracking(True)
    self.acquire_params()
    
  def reset_magnification(self):
    self.config['dbscale_lo'] = -120
    self.config['dbscale_hi'] = 10
    return self.config['dbscale_lo'],self.config['dbscale_hi']
      
  def acquire_essential(self):
    self.dh = self.height()
    self.dw = self.width()
    self.cf = self.config['freq']
    self.dwd2 = self.dw/2
    
  def acquire_params(self):
    self.acquire_essential()
    self.cf = self.config['freq']
    self.bw = self.main.sample_rate_control.get_value()
    self.bwd2 = self.bw/2
  
  def process_zoom(self,z):
    z = (z,.499)[z > .499]
    z = (z,0)[z < 0]
    self.mpa = z
    self.mpb = 1-z
    self.zoom = z
    return z
  
  def eventFilter(self, object, evt):
    lo = self.config['dbscale_lo']
    hi = self.config['dbscale_hi']
    self.acquire_params()
    t = evt.type()
    if 'pos' in dir(evt):
      self.mp = evt.pos()
      self.mousex = float(self.mp.x())
      self.mousey = float(self.mp.y())
      # normalized mouse position
      self.mx = self.ntrp(self.mousex,0.0,self.dw,0.0,1.0)
      self.db = self.ntrp(self.mp.y(),self.dh,0,lo,hi)
    # mouse leaving FFT display area?
    if t == QtCore.QEvent.Leave:
      self.mp = None
    if self.mp != None:
      # if mouse drag in progress
      if self.mouse_startx != None:
        delta = (self.mouse_startx-self.mousex) * self.bw / self.dw
        self.mouse_startx = self.mousex
        f = self.zoom_scale(delta) + self.cf
        self.main.assign_freq(f)
        scale = hi-lo
        delta = (self.mouse_starty-self.mousey) * scale / self.dh
        self.mouse_starty = self.mousey
        hi -= delta
        lo -= delta
      if t == QtCore.QEvent.Wheel:
        wheeldelta = (-1,1)[evt.angleDelta().y() > 0]
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        # if changing vertical axis
        if (modifiers == QtCore.Qt.ControlModifier):
          scale = hi-lo
          # prevent infinite magnification
          if scale > 5 or wheeldelta < 0:
            wd = wheeldelta * .05
            hi -= wd * (hi - self.db)
            lo -= wd * (lo - self.db)
        else:
          # a bit tricky to zoom and unzoom the frequency display
          # without locking up or other undesirable effects
          z = self.main.config['fft_zoom']
          z += .1 * wheeldelta * (.5-z)
          self.main.config['fft_zoom'] = self.process_zoom(z)
      if t == QEvent.ContextMenu:
        # reset mouse-wheel zoom factor
        self.main.config['fft_zoom'] = self.process_zoom(0)
        lo,hi = self.reset_magnification()
        # default to FFT size of 4096
        #self.main.fft_size_control.set_value(6)
      if t == QEvent.MouseButtonDblClick:
        # double-click assigns frequency
        # of mouse cursor location
        dx = self.zoom_scale(self.mousex/self.dw)
        f = self.ntrp(dx,0,1,self.cf-self.bwd2,self.cf+self.bwd2)
        self.main.assign_freq(f)
      if t == QEvent.MouseButtonPress:
        # start mouse drag mode
        self.mouse_startx = self.mousex
        self.mouse_starty = self.mousey
      if t ==  QEvent.MouseButtonRelease:
        # quit mouse drag mode
        self.mouse_startx = None
    self.config['dbscale_lo'] = lo
    self.config['dbscale_hi'] = hi
    return False
    
  def ntrp(self,x,xa,xb,ya,yb):
    return (x-xa)*(yb-ya)/(xb-xa) + ya
    
  def accept_data(self,source):
    if not self.drawing:
      self.acquire_essential()
      ll = len(source)
      dest = []
      mpa = self.mpa
      mpb = self.mpb
      # shift displayed spectrum by offset frequency
      if self.zoom != None and self.zoom > 0:
        df = float(self.main.radio.compute_offset_f()) / self.bw
        mpa -= df
        mpb -= df
        mpa = (mpa,0)[mpa < 0]
        mpb = (mpb,1)[mpb > 1]
      pa = int(mpa * ll)
      pb = int(mpb * ll)
      sz = pb-pa
      if(sz > 0):
        # select zoomed data array segment
        wfdest = source[pa:pb]
        v = wfdest[sz/2]
        self.ss += (v-self.ss) * self.integ_constant
        self.main.signal_progress_bar.setValue(self.ss)
        self.main.signal_progress_bar.setFormat("%.1f db" % self.ss)
        self.main.waterfall_widget.accept_data_line(wfdest)
        lo = self.config['dbscale_lo']
        hi = self.config['dbscale_hi']
        for x,y in enumerate(wfdest):
          px = self.ntrp(x,0,sz,0,self.dw)
          py = self.ntrp(y,hi,lo,0,self.dh)
          dest.append([px,py])
        # check one more time
        if not self.drawing:
          self.data = dest
          self.update()
  
  # x must be normalized for these to work
  def zoom_scale(self,x):
    return x  * (self.mpb-self.mpa) + self.mpa
    
  def zoom_inv_scale(self,x):
    return (self.mpa - x)/(self.mpa  - self.mpb)
  
  def get_ss(self):
    return self.ss
        
  def paintEvent(self,event):
    if self.isVisible():
      self.drawing = True
      self.acquire_essential()
      qp = QPainter(self)
      qp.fillRect(0, 0, self.width(), self.height(),self.black_color)
      qp.setFont(self.monospace_font)
      # vertical line at center frequency
      qp.setPen(self.disp_vline_color)
      xp = self.dw * self.zoom_inv_scale(.5)
      qp.drawLine(xp,16,xp,self.dh-40)
      # data
      if self.data:
        qp.setPen(self.disp_trace_color)
        ox = None
        oy = None
        for item in self.data:
          x,y = item
          if ox != None:
            qp.drawLine(ox,oy,x,y)
          ox = x
          oy = y
      steps = 10
      # horizontal frequency scale
      qp.setPen(self.disp_text_color)
      for n in range(1,steps):
        nn = self.zoom_scale((float(n)/steps))
        x = self.ntrp(n,0,steps,0,self.dw)
        f = self.ntrp(nn,0,1,self.cf-self.bwd2,self.cf+self.bwd2)
        # a way to limit the number of displayed digits
        # based on the size of the frequency number
        ff = (f,0)[f < 0]
        qs = 3-int(math.log10(1+ff/1e6)+.5)
        qs = (qs,0)[qs < 0]
        sf = "%%.%df" % qs
        s = sf % (f/1e6)
        ssz = len(s) * self.dw/110
        qp.drawText(x-ssz,self.dh-16,s)
      # db scale
      step = int(self.dh/10.0)
      for y in range(step,self.dh-step,step):
        db = self.ntrp(y,self.dh,0,self.config['dbscale_lo'],self.config['dbscale_hi'])
        s = "%4d" % db
        qp.drawText(4,y,s)
      # if the mouse is over the widget,
      # draw information label
      if self.mp != None:
        n = self.zoom_scale(self.mousex/self.dw)
        f = self.ntrp(n,0,1,self.cf-self.bwd2,self.cf+self.bwd2)
        #qp.setPen(QtGui.QColor(128,128,255))
        s = "%.3f MHz" % (f/1e6)
        qp.drawText(self.mp.x(),self.mp.y()-24,s)
        s = "%.1f db" % (self.db)
        qp.drawText(self.mp.x(),self.mp.y()-4,s)
        
      self.drawing = False
    