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
import ast
import time
import struct
import signal
import numpy as np
import glob
from gnuradio import gr

from PyQt5 import Qt
from PyQt5 import QtCore,QtGui
from PyQt5.QtWidgets import QWidget,QMainWindow,QHeaderView, QMessageBox

import osmosdr

from PLSDR_GUI import Ui_MainWindow
import Radio
import FFTDisp
import MyTextEntry
import FreqDigit
import MySlider
import MyCombo
import MyCheckbox
import MyButtonGroup
import Waterfall
import OdsConverter
   
class PLSDR(QMainWindow, Ui_MainWindow):
  def __init__(self,app):
    QMainWindow.__init__(self)
    Ui_MainWindow.__init__(self)
    
    PLSDR.VERSION = "1.2"
    
    # device names and invocation strings
    # some tested, some search results
    # please tell the author of any new, successful
    # devices and invocation strings
    # or problems with/changes to these
    
    self.device_dict = {
      'RTL-SDR':'rtl',
      'RTL-SDR TCP':'rtl_tcp',
      'HackRF':'hackrf',
      'SDRplay':'soapy=0,driver=sdrplay',
      'LimeSDR':'soapy=0,driver=lime',
      'USRP':'uhd',
      'BladeRF':'bladerf',
      'AirSpy':'airspy',
      'OsmoSDR':'osmosdr',
      'Miri':'miri',
      'RFSPACE':'sdr-iq',
      'FCD':'fcd',
       # this IP must be changed for any specific installation
      'RedPitaya':'redpitaya=192.168.1.100:1001',
      'PlutoSDR':'ip:pluto.local',
    }
      
    self.app = app
    self.setupUi(self)
    self.setWindowTitle("PLSDR Version %s" % PLSDR.VERSION)
    self.app_icon = QtGui.QIcon()
    self.app_icon.addFile('icon/app_icon_16x16.png', QtCore.QSize(16,16))
    self.app_icon.addFile('icon/app_icon_24x24.png', QtCore.QSize(24,24))
    self.app_icon.addFile('icon/app_icon_32x32.png', QtCore.QSize(32,32))
    self.app_icon.addFile('icon/app_icon_48x48.png', QtCore.QSize(48,48))
    self.app_icon.addFile('icon/app_icon_128x128.png', QtCore.QSize(128,128))
    self.app_icon.addFile('icon/app_icon_256x256.png', QtCore.QSize(256,256))
    app.setWindowIcon(self.app_icon)
    app.aboutToQuit.connect(self.app_quit)
    self.graphic_data = None
    self.config = self.get_default_config()
    self.full_rebuild_flag = True
    self.running = False
    self.enabled = False
    self.upconvert_state_control = None
    self.radio = Radio.Radio(self)
    self.meta_style_sheet = """
    QLabel[accessibleName=FreqDigit] {
      color:#00c000;
      font-size:24pt;
      background:black;
      padding:0;
    }
    QLabel[accessibleName=FreqDigitDark] {
      color:#003000;
      font-size:24pt;
      background:black;
      padding:0;
    }
    QLabel[accessibleName=FreqDigit]:hover {
      color:#00ff00;
      background:#404040;
    }
    QLabel[accessibleName=FreqDigitDark]:hover {
      color:#00ff00;
      background:#404040;
    }
    QWidget[objectName=digit_widget] {
      background:black;
    }
    /* this solves the mouse tooltip color problem */
    DisplayPlot {
      qproperty-zoomer_color: #c0e0ff;
    }
    QTextEdit {
      text-align:right;
    }
    """
    self.setStyleSheet(self.meta_style_sheet)
    
    # maps keyboard keys to frequency changes in Hz
    self.key_hash = {
      QtCore.Qt.Key_Minus  : -1e2,
      QtCore.Qt.Key_Plus  : 1e2,
      QtCore.Qt.Key_Left  : -1e3, 
      QtCore.Qt.Key_Right  : 1e3, 
      QtCore.Qt.Key_Up  : -1e4, 
      QtCore.Qt.Key_Down  : 1e4, 
      QtCore.Qt.Key_PageUp  : -1e5, 
      QtCore.Qt.Key_PageDown  : 1e5, 
      QtCore.Qt.Key_Insert  : -1e6, 
      QtCore.Qt.Key_Delete  : 1e6, 
    }
    
    # locate user's home directory, create configuration path
    home_dir = os.path.expanduser('~')
    classname = self.__class__.__name__
    self.config_path = os.path.join(home_dir,".%s" % classname)
    if not os.path.exists(self.config_path):
      os.makedirs(self.config_path)
    self.config_file = os.path.join(self.config_path,'config.ini')
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    self.run_stop_button.clicked.connect(self.run_stop_event)
    self.quit_button.clicked.connect(self.app_quit)
    
    self.offset_freq_control = None
    
    self.signal_progress_bar.setMinimum(-120)
    self.signal_progress_bar.setMaximum(10)
    
    self.mode_list = ['AM','FM','WFM','USB','LSB','CW_USB','CW_LSB']
      
    self.MODE_AM = 0
    self.MODE_FM = 1
    self.MODE_WFM = 2
    self.MODE_USB = 3
    self.MODE_LSB = 4
    self.MODE_CW_USB = 5
    self.MODE_CW_LSB = 6
    
    self.mode_control = MyCombo.Combo(self,self.config,self.mode_combo,self.change_modes,'mode',self.mode_list)
        
    self.agc_list = ['SW/F','SW/S','HW','OFF']
    
    self.AGC_FAST = 0
    self.AGC_SLOW = 1
    self.AGC_HW = 2
    self.AGC_OFF = 3
    
    self.agc_control = MyCombo.Combo(self,self.config,self.agc_combo,self.set_agc_mode,'agc_mode',self.agc_list)
    
    self.bw_buttonlist = [self.if_bw_wide_button,self.if_bw_medium_button,self.if_bw_narrow_button]
    
    self.BW_WIDE = 0
    self.BW_MEDIUM = 1
    self.BW_NARROW = 2
    
    self.if_bw_buttongroup_control = MyButtonGroup.ButtonGroup(self.config,self.if_bw_button_group,self.set_bw_mode,'bw_mode',self.bw_buttonlist)
    
    self.gain_control_a = MySlider.Slider(self.config,self.gain_slider_a,self.set_named_gain,'gain_a',0,50)
    self.gain_control_b = MySlider.Slider(self.config,self.gain_slider_b,self.set_named_gain,'gain_b',0,50)
    self.gain_control_c = MySlider.Slider(self.config,self.gain_slider_c,self.set_named_gain,'gain_c',0,50)
    self.gain_control_d = MySlider.Slider(self.config,self.gain_slider_d,self.set_named_gain,'gain_d',0,50)
    
    self.af_gain_control = MySlider.Slider(self.config,self.af_gain_slider,self.set_af_gain,'af_gain',0,1,400)
    self.average_control = MySlider.Slider(self.config,self.averaging_slider,self.set_average,'average',1,.01)
    self.squelch_control = MySlider.Slider(self.config,self.squelch_slider,self.set_squelch,'squelch_level',-130,50,400)
    
    self.populate_freq_list()
    model = self.freq_table.model()
    
    selectionModel = QtCore.QItemSelectionModel(model)
    self.freq_table.setSelectionModel(selectionModel)
    selectionModel.selectionChanged.connect(self.row_selected)
    
    self.setup_freq_digits()
    
    self.bandwidth_control = MyCombo.Combo(self,self.config,self.bandwidth_combo,self.set_bandwidth,'bandwidth')
    
    self.fft_sizes = ["%d" % 2**n for n in range(6,20)]
    
    self.fft_size_control = MyCombo.Combo(self,self.config,self.fft_size_combo,self.critical_change,'fft_size',self.fft_sizes)
    self.framerates = ["%d" % n for n in (60,50,30,25,20,15,10,5,2,1)]
    self.framerate_control = MyCombo.Combo(self,self.config,self.framerate_combo,self.critical_change,'framerate',self.framerates)
    
    self.antenna_control = MyCombo.Combo(self,self.config,self.antenna_combo,self.change_antennas,'antenna')
    
    self.sample_rate_control = MyCombo.Combo(self,self.config,self.sample_rate_combo,self.critical_change,'sample_rate')
    
    self.audio_rate_control = MyTextEntry.TextEntry(self,self.audio_rate_text,self.critical_change,'audio_rate',1e3,60e3)
    
    self.cw_base_control = MyTextEntry.TextEntry(self,self.cw_base_text,self.critical_change,'cw_base',1e2,3e3)
    
    self.audio_device_control = MyTextEntry.TextEntry(self,self.audio_device_text,self.critical_change,'audio_device',0,0,True)
    
    self.corr_ppm_control = MyTextEntry.TextEntry(self,self.corr_ppm_text,self.set_corr_ppm,'corr_ppm',-100,100)
    
    self.corr_ppm_upc_control = MyTextEntry.TextEntry(self,self.corr_ppm_upc_text,self.set_corr_ppm_upc,'corr_ppm_upc',-100,100)
    
    self.upconvert_state_control = MyCheckbox.Checkbox(self,self.upconversion_checkbox,self.use_upconversion,'upconvert_state')
    
    self.upconvert_trans_control = MyTextEntry.TextEntry(self,self.upconvert_trans_text,self.update_freq_event,'upconvert_trans',0,50e6)
    
    self.upconvert_freq_control = MyTextEntry.TextEntry(self,self.upconvert_freq_text,self.update_freq_event,'upconvert_freq',0,1000e6)
    
    self.offset_state_control = MyCheckbox.Checkbox(self,self.offset_checkbox,self.use_offset,'offset_state')
    
    self.offset_freq_control = MyTextEntry.TextEntry(self,self.offset_freq_text,self.update_offset_freq,'offset_freq',-10000,10000)
       
    self.dc_offset_control = MyCheckbox.Checkbox(self,self.dc_offset_checkbox,self.set_dc_offset,'dc_offset')
    
    self.iq_balance_control = MyCheckbox.Checkbox(self,self.iq_balance_checkbox,self.set_iq_balance,'iq_balance')
    
    # pause number 1 waits for interface to be rendered
    # before modifying it
    QtCore.QTimer.singleShot(100, self.first_read_config)
              
  def first_read_config(self):
    self.setup_help()
    self.read_config()
    self.waterfall_widget = Waterfall.WaterfallWidget(self,self.config,self.waterfall_layout)
    self.fft_widget = FFTDisp.FFTDispWidget(self,self.config,self.fft_disp_layout)
    self.enabled = True
  
  def setup_help(self):
    # load help document into help browser
    try:
      with open('help_page/index.html') as f:
        data = f.read()
      data = re.sub('#VERSION#',PLSDR.VERSION,data)
      data = re.sub('#CONFIG_FILE#',self.config_file,data)
      data = re.sub('#CONFIG_DIR#',self.config_path,data)
      self.help_text_browser.setText(data)
      self.help_text_browser.setOpenLinks(True)
      self.help_text_browser.setOpenExternalLinks(True)
    except Exception as e:
      print(e)
          
  def process_tabs(self,config,write = False):
    tablist = {
      'tab1' : self.freq_waterfall_tabwidget,
      'tab2' : self.controls_tabwidget,
    }
    for key in tablist:
      if write:
        config[key] = tablist[key].currentIndex()
      else:
        tablist[key].setCurrentIndex(config[key])
  
  def keyPressEvent(self,evt):
    key = evt.key()
    if key in self.key_hash:
      delta = self.key_hash[key]
      f = self.config['freq'] + delta
      self.assign_freq(f)
    
  def get_default_config(self):
    defaults = {
      'antenna' : 0,
      'app_w' : 800,
      'app_h' : 600,
      'tab1' : 0,
      'tab2' : 0,
      'tab3' : 0,
      'freqlist_scroll_position' : 0,
      'help_scroll_position' : 0,
      'splitter_v_pos' : 0.5,
      'splitter_h_pos' : 0.7,
      'sample_rate' : 2.4e6,
      'audio_rate' : 48000,
      'cw_base' : 750,
      'freq' : 10000000,
      'mode' : 0,
      'audio_device' : 'plughw:0,0',
      'fft_size' : 6,
      'corr_ppm' : 0,
      'corr_ppm_upc' : 0,
      'af_gain' : 10,
      'gain_a' : 50,
      'gain_b' : 50,
      'gain_c' : 50,
      'gain_d' : 50,
      'squelch_level' : 0,
      'average' : 50,
      'bandwidth' : 50,
      'dbscale_lo' : -140,
      'dbscale_hi' : 10,
      'hilbert_taps' : 128,
      'fft_zoom' : 0,
      'framerate' : 6,
      'selected_device' : 0,
      'offset_state' : False,
      'offset_freq' : -10000,
      'upconvert_state' : False,
      'upconvert_trans' : 24000000,
      'upconvert_freq' : 125000000,
      'agc_mode' : 0,
      'bw_mode' : 1,
      'dc_offset' : False,
      'iq_balance' : False,
      'waterfall_bias' : 150,
      'disp_trace_color' : '#ffff00',
      'disp_text_color' : '#80c0ff',
      'disp_vline_color' : '#c00000',
    }
    return defaults
    
  def read_config(self):
    if os.path.exists(self.config_file):
      data = self.read_file(self.config_file)
      # safely convert the configuration dictionary
      oldconfig = ast.literal_eval(data)
      # avoid tricky bug in which the old config
      # doesn't have all the values of the new
      for key in self.config.keys():
        if key in oldconfig:
          self.config[key] = oldconfig[key]
    # set interface values from configuration
    self.assign_freq(self.config['freq'])
    self.update_radio_values()
    self.resize(self.config['app_w'],self.config['app_h'])
    self.freq_table.verticalScrollBar().setValue(self.config['freqlist_scroll_position'])
    self.help_text_browser.verticalScrollBar().setValue(self.config['help_scroll_position'])
    v = self.config['splitter_v_pos']
    self.float_to_splitter(v,self.splitter_v)
    h = self.config['splitter_h_pos']
    self.float_to_splitter(h,self.splitter_h)
    # always process tabs last, so the splitters remain in view
    # otherwise they won't be set up properly
    self.process_tabs(self.config)
    self.configure_device_combo()
    # pause number 2 allows interface to
    # be fully laid out before starting
    # radio configuration
    QtCore.QTimer.singleShot(100, self.change_modes)
    
    
  def update_radio_values(self):
    self.bandwidth_control.set_value()
    self.af_gain_control.set_value()
    self.gain_control_a.set_value()
    self.gain_control_b.set_value()
    self.gain_control_c.set_value()
    self.squelch_control.set_value()
    self.corr_ppm_control.set_value()
    self.corr_ppm_upc_control.set_value()
    self.offset_state_control.get_value()
    self.offset_freq_control.set_value()
    self.upconvert_state_control.get_value()
    self.upconvert_trans_control.set_value()
    self.upconvert_freq_control.set_value()
    self.average_control.set_value()
    self.agc_control.set_value()
    self.if_bw_buttongroup_control.set_value()
    self.dc_offset_control.set_value()
    self.iq_balance_control.set_value()
    self.antenna_control.set_value()
    self.sample_rate_control.get_value()
    self.audio_rate_control.get_value()
    self.cw_base_control.get_value()
    self.mode_control.get_value()
    self.framerate_control.get_value()
    self.fft_size_control.get_value()
    self.audio_device_control.get_value()
  
  def write_config(self,config):
    config['app_w'] = self.width()
    config['app_h'] = self.height()
    config['freqlist_scroll_position'] = self.freq_table.verticalScrollBar().value()
    config['help_scroll_position'] = self.help_text_browser.verticalScrollBar().value()
    config['splitter_v_pos'] = self.splitter_to_float(self.splitter_v)
    config['splitter_h_pos'] = self.splitter_to_float(self.splitter_h)
    config['waterfall_bias'] = self.waterfall_widget.bias
    self.process_tabs(config,True)
    # clean up this dictionary's appearance
    data = str(self.config)
    data = re.sub(r'[{}]',r'',data)
    array = re.split(r', ',data)
    array.sort()
    data = "{\n%s\n}" % ',\n'.join(array)
    self.write_file(self.config_file,data)

  def splitter_to_float(self,splitter):
    # creates normalized splitter position {0 ... 1}
    a,b = splitter.sizes()
    return float(a)/(a+b)
    
  def float_to_splitter(self,v,splitter):
    # requires normalized splitter position {0 ... 1}
    a,b = splitter.sizes()
    t = a+b
    aa = int(t * v)
    bb = t-aa
    splitter.setSizes([aa,bb])
    
  # these are the user-interface frequency digits
  def setup_freq_digits(self):
    self.dsp_digits = (
      self.label_digit_0,
      self.label_digit_1,
      self.label_digit_2,
      self.label_digit_3,
      self.label_digit_4,
      self.label_digit_5,
      self.label_digit_6,
      self.label_digit_7,
      self.label_digit_8,
      self.label_digit_9,
    )
    self.freq_digits = []
    for n in range(10):
      self.freq_digits.append(FreqDigit.FreqDigit("0",self,self.dsp_digits[n]))
    
  def process_mouse_frequency_change(self):
    freq = 0
    m = 1
    for digit in self.freq_digits:
      freq += digit.value * m
      m *= 10
    freq = (freq,0)[freq < 0]
    self.assign_freq(freq)
  
  def update_freq_event(self,x = None):
    self.update_freq()
  
  def acquire_corr_ppm(self):
    if self.upconvert_state_control.get_value():
      if self.config['freq'] <= self.upconvert_trans_control.get_value():
        return self.corr_ppm_upc_control.get_value()
    return self.corr_ppm_control.get_value()

  def test_upconvert_mode(self):
    if self.upconvert_state_control != None:
      if self.upconvert_state_control.get_value():
        if self.config['freq'] <= self.upconvert_trans_control.get_value():
          return True
    return False
  
  def update_status(self):
    if not self.radio.device_found:
      s = "No radio device detected"
    else:
      if self.running:
        s = "%s | %s | %.6f MHz | Upconvert:%s | Offset:%s" % \
        (
          self.device_control.get_value(),
          self.mode_control.get_value(),
          self.config['freq']/1e6,
          self.upconvert_state_control.get_value_as_letter(),
          self.offset_state_control.get_value_as_letter(),
          )  
      else:
        s = "%s | %s | Stopped" % (
          self.device_control.get_value(),
          self.mode_control.get_value(),
          )
    self.status_label.setText(s)
      
  def update_freq(self,f = None):
    if self.enabled:
      self.radio.test_set_cw_offset()
      if f == None:
        f = self.config['freq']
      else:
        self.config['freq'] = f
      upconvert_offset = 0
      if self.test_upconvert_mode():
        upconvert_offset = self.upconvert_freq_control.get_value()
      mf = self.config['freq']+upconvert_offset+self.radio.compute_offset_f()
      if self.radio.osmosdr_source != None:
        #print("assigned freq: %f = %d" % (mf,int(mf)))
        self.radio.osmosdr_source.set_center_freq(int(mf), 0)
        self.radio.osmosdr_source.set_freq_corr(self.acquire_corr_ppm(), 0)
      self.radio.update_freq_xlating_fir_filter()
      self.update_status()

  def assign_freq(self,f = None):
    if f == None:
      f = self.config['freq']
    self.update_freq(f)
    for n,digit in enumerate(self.freq_digits):
      digit.zero = f == 0
      digit.set_value(f % 10)
      f //= 10
        
  def update_default_freq(self):
    self.update_freq(self.config['freq'])
  
  def erase_digits_to_right(self,digit):
    for d in self.freq_digits:
      if d is digit:
        break
      d.set_value(0)
    self.process_mouse_frequency_change()
                  
  def start_process(self,start = True):
    self.run_stop_button.setChecked(start)
    if start and self.radio.error == False:
      self.update_default_freq()
      self.radio.start()
    else:
      self.radio.stop()
      self.radio.wait()
      self.radio.disconnect_all()
               
  def run_stop_event(self):
    self.running = not self.running
    self.run_stop()
    
  def run_stop(self,x = None):
    self.run_stop_button.setChecked(self.running)
    if self.running:
      self.start_process(False)
      self.radio.cw_offset = 0
      if self.full_rebuild_flag:
        self.radio = Radio.Radio(self)
        self.full_rebuild_flag = False  
      self.update_freq()
      self.update_radio_values()
      self.radio.initialize_radio(self.config)
      self.start_process()
    else:
      self.radio.initialize_radio(self.config)
      self.start_process(False)
    self.update_status()
 

  def change_modes(self,value = None,name = None):
    self.run_stop()
    
  def critical_change(self,value,name = None):
    if self.enabled:
      self.full_rebuild_flag = True
      self.run_stop()
    
  def change_framerate(self,value):
    self.run_stop()
  
  def select_device(self,value = None,name = None):
    self.full_rebuild_flag = True
    self.run_stop()
         
  def row_selected(self):
    selection = self.freq_table.selectionModel().selectedRows()
    row = (selection[0].row())
    record = self.accessible_list[row]
    freq_hz = record[self.freq_field]
    self.assign_freq(freq_hz)
    s_mode = record[self.mode_field].upper()
    s_mode = re.sub('CW','CW_USB',s_mode)
    if s_mode in self.mode_list:
      self.mode_control.set_value( self.mode_list.index(s_mode))
      #self.assign_freq()


  def message_dialog(self,title,message):
    mb = QMessageBox (QMessageBox.Warning,title,message,QMessageBox.Ok)
    mb.exec_()
    
  def detect_freq_file(self):
    path = None
    for suffix in ('ods','csv'):
      flist = glob.glob(self.config_path + '/*.%s' % suffix)
      if len(flist) > 0:
        path = flist[0]
        break
    return path
    
    
  def populate_freq_list(self):
    self.accessible_list = []
    path = self.detect_freq_file()
    if path == None:
      data = self.read_file('frequency_spreadsheet/frequency_list.ods')
      path = "%s/frequency_list.ods" % self.config_path
      self.write_file(path,data)
    # if CSV table
    if re.search('(?i).*\.csv',path):
      table = []
      with open(path) as f:
        content = f.read()
      records = re.split('\n+',content)
      for record in records:
        if len(record) > 0:
          record = re.sub('"','',record)
          fields = re.split(',',record)
          table.append(fields)
    # if ODS spreadsheet
    else:
      table = OdsConverter.OdsToArray().array_from_path(path)
    self.fieldNames = table[:1][0]
    table_data = table[1:]
    mults = {'ghz' : 1e9,'mhz':1e6,'khz':1e3,'hz':1}
    rmult = -1 # frequency multipler
    self.freq_field = -1 # field to which above frequency multiplier is applied
    self.mode_field = -1 # field from which mode is extracted
    for mult in mults:
      for n,field in enumerate(self.fieldNames):
        if re.search("(?i).*%s.*" % mult,field) != None:
          rmult = mults[mult]
          self.freq_field = n
        if re.search("(?i).*mode.*",field) != None:
          self.mode_field = n
    if self.freq_field == -1 or self.mode_field == -1:
      self.message_dialog("Malformed Frequency List","The present frequency-table source document (%s) is not correctly formatted -- please read the documentation." % path)
    else:
      self.model = QtGui.QStandardItemModel(parent=self)
      self.model.setHorizontalHeaderLabels(self.fieldNames)
      self.freq_table.setModel(self.model)
      header = self.freq_table.horizontalHeader()
      for n,_ in enumerate(self.fieldNames):
        #None # FIXME
        #header.setResizeMode(n, QtGui.QHeaderView.Stretch)
        header.setSectionResizeMode(QHeaderView.Stretch)
      for record in table_data:
        if(len(record) > 0):
          arecord = []
          qrecord = []
          for n,field in enumerate(record):
            item = QtGui.QStandardItem(field)
            item.setEditable(False)
            qrecord.append(item)
            if n == self.freq_field:
              # results always in Hz
              arecord.append(rmult * float(field))
            else:
              arecord.append(field)
          self.accessible_list.append(arecord)
          self.model.appendRow(qrecord)
    
  def draw_fft_disp(self):
    if self.graphic_data != None:
      #sya = self.config['dbscale_lo']
      #syb = self.config['dbscale_hi']
      # note Y axis reversal
      self.fft_widget.accept_data(self.graphic_data)
      self.graphic_data = None
      
  def configure_device_combo(self):
    dev_name_list = sorted(self.device_dict.keys())
    self.device_control = MyCombo.Combo(self,self.config,self.device_combo,self.select_device,'selected_device',dev_name_list)
    self.device_control.get_value()
   
    
  def set_bandwidth(self,value = None,string = None):
    if self.radio.osmosdr_source != None and string != None:
      bw = float(string)
      #print("set bandwidth: %d" % bw)
      self.radio.osmosdr_source.set_bandwidth(bw, 0)
      
  def set_average(self,result,name = None):
    if self.radio.logpwrfft != None:
      self.radio.logpwrfft.set_avg_alpha(result)
      self.radio.logpwrfft.set_average(result != 1)

  def set_af_gain(self,result,name = None):
    if self.radio.blocks_multiply_const_volume != None:
      # use a power function to control volume levels
      y = 2 * result * result
      self.radio.blocks_multiply_const_volume.set_k((y,))
    
  def set_named_gain(self,result,name = None):
    if self.radio.osmosdr_source != None and name != None:
      #print("result: %.2f, name: %s" % (result,name))
      self.radio.osmosdr_source.set_gain(result,name,0)
      
  def set_squelch(self,result,name):
    if self.radio.analog_pwr_squelch != None:
      self.radio.analog_pwr_squelch.set_threshold(result)
    if self.radio.analog_pwr_squelch_ssb != None:
      self.radio.analog_pwr_squelch_ssb.set_threshold(result)

  def set_corr_ppm(self,result):
    if not self.test_upconvert_mode():
      if self.radio.osmosdr_source != None:
        self.radio.osmosdr_source.set_freq_corr(result,0)
      
  def set_corr_ppm_upc(self,result):
    if self.test_upconvert_mode():
      if self.radio.osmosdr_source != None:
        self.radio.osmosdr_source.set_freq_corr(result,0)
      
  def set_cw_base(self,result):
    self.cw_base = result
    
  def set_agc_mode(self,mode = None,name = None):
    if mode == None:
      mode = self.config['agc_mode']
    if self.radio.osmosdr_source != None:
      hw_mode = False
      agc_reference = 1
      agc_gain = 1
      agc_max_gain = 1
      agc_attack_rate = 1e-1
      agc_decay_rate = 1e-1
      if mode == self.AGC_SLOW:
        agc_decay_rate = 1e-2
        agc_max_gain = 65536
      elif mode == self.AGC_FAST:
        agc_max_gain = 65536
      elif mode == self.AGC_HW:
        hw_mode = True
      self.radio.osmosdr_source.set_gain_mode(hw_mode,0)
      if self.radio.analog_agc_cc != None:
        #print("setting AGC mode: %d" % mode)
        for inst in (self.radio.analog_agc_cc,self.radio.analog_agc_ff):
          inst.set_reference(agc_reference)
          inst.set_gain(agc_gain)
          inst.set_max_gain(agc_max_gain)
          inst.set_attack_rate(agc_attack_rate)
          inst.set_decay_rate(agc_decay_rate)

  def set_bw_mode(self,result):
    self.radio.rebuild_filters(self.config,result)
    
  def set_hardware_agc(self,result):
    if self.radio.osmosdr_source != None:
      self.radio.osmosdr_source.set_gain_mode(result,0)
  
  def set_dc_offset(self,result):
    if self.radio.osmosdr_source != None:
      dco = (0,2)[result]
      self.radio.osmosdr_source.set_dc_offset_mode(dco,0)
      
  def set_iq_balance(self,result):
    if self.radio.osmosdr_source != None:
      iqb = (0,2)[result]
      self.radio.osmosdr_source.set_iq_balance_mode(iqb,0)
  
  def use_offset(self,result):
    if self.radio != None:
      self.radio.create_update_freq_xlating_fir_filter()
      self.update_freq()
      
  def update_offset_freq(self,result):
    if self.radio != None:
      self.radio.create_update_freq_xlating_fir_filter()
      self.update_freq()
    
  def use_upconversion(self,result):
    if(result):
      self.upconvert_freq_control.update_entry()
      self.upconvert_trans_control.update_entry()
    self.run_stop()
    
  def change_antennas(self,index,name):
    #print("change antennas: %s" % name)
    self.radio.change_antennas(name)
    
  def read_file(self,path):
    with open(path) as f:
      return f.read()
      
  def write_file(self,path,data):
    with open(path,'w') as f:
      f.write(data)
          
  def app_quit(self,x=0):
    self.running = False
    self.enabled = False
    self.start_process(False)
    self.write_config(self.config)
    Qt.QApplication.quit()   

if __name__ == "__main__":
  os.chdir(os.path.dirname(sys.argv[0]))
  app = Qt.QApplication(sys.argv)
  window = PLSDR(app)
  window.show()
  sys.exit(app.exec_())

