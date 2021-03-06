#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Sun Jun 26 02:45:27 2011

import wx
import os
import autoqc
from RegistryEnv_v1 import RegistryEnv

# begin wxGlade: extracode
# end wxGlade

env = RegistryEnv()
if not "defaultPathPOS" in env:
    env["defaultPathPOS"] = os.curdir
if not "defaultPathSBET" in env:
    env["defaultPathSBET"] = os.curdir

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.sizer_settings_staticbox = wx.StaticBox(self, -1, "Settings")
        self.lbl_pos = wx.StaticText(self, -1, "POSPac Project:", style=wx.ALIGN_RIGHT)
        self.txt_pos = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        self.btn_pos = wx.Button(self, -1, "Open POSPac Project")
        self.lbl_sbet = wx.StaticText(self, -1, "NAVDIF Reference SBET:", style=wx.ALIGN_RIGHT)
        self.txt_sbet = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        self.btn_sbet = wx.Button(self, -1, "Open Reference SBET")
        self.btn_run = wx.Button(self, -1, "Run Auto QC")
        self.text_ctrl_1 = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.gauge = wx.Gauge(self, -1, 100)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

        #set event handlers
        wx.EVT_BUTTON(self.btn_pos, 		self.btn_pos.GetId(), 		self.OnOpenPOS)
        wx.EVT_BUTTON(self.btn_sbet, 		self.btn_sbet.GetId(), 		self.OnOpenSBET)
        wx.EVT_BUTTON(self.btn_run, 		self.btn_run.GetId(), 		self.OnRunQC)

        # after run status is set to true
        self.result_status = False


    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("POSPac Automated QC")
        self.SetSize((700, 600))
        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.lbl_pos.SetMinSize((140, 13))
        self.btn_pos.SetMinSize((130,-1))
        self.lbl_sbet.SetMinSize((140, 13))
        self.btn_sbet.SetMinSize((130,-1))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_settings = wx.StaticBoxSizer(self.sizer_settings_staticbox, wx.VERTICAL)
        sizer_sbet = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pos = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pos.Add(self.lbl_pos, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_pos.Add(self.txt_pos, 1, wx.EXPAND, 0)
        sizer_pos.Add(self.btn_pos, 0, 0, 0)
        sizer_settings.Add(sizer_pos, 1, wx.TOP|wx.BOTTOM|wx.EXPAND, 3)
        sizer_sbet.Add(self.lbl_sbet, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_sbet.Add(self.txt_sbet, 1, wx.EXPAND, 0)
        sizer_sbet.Add(self.btn_sbet, 0, 0, 0)
        sizer_settings.Add(sizer_sbet, 1, wx.TOP|wx.BOTTOM|wx.EXPAND, 3)
        sizer_main.Add(sizer_settings, 0, wx.ALL|wx.EXPAND, 5)
        sizer_main.Add(self.btn_run, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_main.Add(self.text_ctrl_1, 1, wx.EXPAND, 0)
        sizer_main.Add(self.gauge, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_main)
        self.Layout()
        # end wxGlade

    def OnOpenPOS(self, event):
        if not self.result_status or self.Reset():
            wxdlg = wx.FileDialog(self,"Open POSPac Project",defaultDir = env["defaultPathPOS"], \
                            wildcard = "Applanix POSPac Project (*.pospac)|*.pospac",\
                            style = wx.OPEN|wx.FILE_MUST_EXIST)
            if wxdlg.ShowModal() != wx.ID_OK:
                return False
            path = wxdlg.GetPaths()[0]
            wxdlg.Destroy()

            self.txt_pos.Value = path

            # save the path for use later
            env["defaultPathPOS"] = os.path.split(path)[0]

    def OnOpenSBET(self, event):
        if not self.result_status or self.Reset():
            wxdlg = wx.FileDialog(self,"Open Exported SBET",defaultDir = env["defaultPathSBET"], \
                            wildcard = "Applanix Smoothed BET (*.sbet;sbet*.out)|*.sbet;sbet*.out",\
                            style = wx.OPEN|wx.FILE_MUST_EXIST)
            if wxdlg.ShowModal() != wx.ID_OK:
                return False
            path = wxdlg.GetPaths()[0]
            wxdlg.Destroy()

            self.txt_sbet.Value = path

            # save the path for use later
            env["defaultPathSBET"] = os.path.split(path)[0]

    def OnRunQC(self, event):
        if not self.result_status or self.Reset():
            posPath = self.txt_pos.Value
            sbetPath = self.txt_sbet.Value

            if os.path.exists(posPath) and os.path.exists(sbetPath):
                self.result_status = True
                autoqc.autoqc(posPath,sbetPath,self.UpdateTxt,self.Progress)

    def ClearTxt(self):
        self.text_ctrl_1.Clear()

    def UpdateTxt(self,text):
        print text
        self.text_ctrl_1.WriteText("%s\n" % text)
        # if needed give processor a break to catch up rendering the GUI
        while wx.GetApp().Pending():
            wx.GetApp().Dispatch()

    def Progress(self, value, start_time = 0):
        #print time.time() - start_time
        self.gauge.SetValue(value)
        # if needed give processor a break to catch up rendering the GUI
        while wx.GetApp().Pending():
            wx.GetApp().Dispatch()

    def Reset(self):
        dlg = wx.MessageDialog(self,"This will reset the previous results. Continue?","Reset?", wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            self.ClearTxt()
            dlg.Destroy()
            self.result_status = False
            return True

        dlg.Destroy()
        return False

# end of class MyFrame


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
