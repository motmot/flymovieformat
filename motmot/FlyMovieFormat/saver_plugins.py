#!/usr/bin/env python
import sys, time, os, gc, datetime
from optparse import OptionParser

import pkg_resources # from setuptools
matplotlibrc = pkg_resources.resource_filename(__name__,"matplotlibrc") # trigger extraction
matplotlibrc_dir = os.path.split(matplotlibrc)[0]
os.environ['MATPLOTLIBRC'] = matplotlibrc_dir
RESFILE = pkg_resources.resource_filename(__name__,"playfmf.xrc") # trigger extraction

# py2exe stuff done
import FlyMovieFormat
import PIL.Image as Image
import motmot.imops.imops as imops

import numpy

bpp = FlyMovieFormat.format2bpp_func

class ImageSequenceSaverPlugin(object):
    def get_description(self):
        return 'Image sequence (CAUTION: loses timestamps)'
    def get_saver(self,wx_parent,format,width_height):

        class ImageSequenceSaver(object):
            def __init__(self,filename,flip_upside_down,format,width_height):
                self.filename = filename
                self.flip_upside_down = flip_upside_down
                self.count = 0
                self.format = format
                self.width_height = width_height
            def save( self, save_frame, timestamp ):
                fname = self.filename%self.count
                self.count += 1
                if self.flip_upside_down:
                    save_frame = save_frame[::-1,:] # flip
                if self.format in ['MONO8','RAW8']:
                    height,width = save_frame.shape
                    im=Image.fromstring('L',(width,height),save_frame.tostring())
                elif self.format in ['MONO32f']:
                    save_frame = save_frame.astype( numpy.uint8 )
                    height,width = save_frame.shape
                    im=Image.fromstring('L',(width,height),save_frame.tostring())
                else:
                    rgb8 = imops.to_rgb8(self.format,save_frame)
                    height,width,depth = rgb8.shape
                    im=Image.fromstring('RGB', (width,height),
                                        rgb8.tostring())
                im.save(fname)
            def close(self):
                return

        def OnCancelImageSequence(event):
            dlg2.Close(True)
        def CalcFilename():
            filename=xrc.XRCCTRL(dlg2,"image_basename").GetValue()
            filename+=xrc.XRCCTRL(dlg2,"image_number_format").GetValue()
            filename+=xrc.XRCCTRL(dlg2,"image_extension_choice").GetStringSelection()
            return filename
        def ShowExampleFilename():
            filename=CalcFilename()
            xrc.XRCCTRL(dlg2,"example_filename").SetValue(filename%(1,))
        def OnTextEvent(event):
            ShowExampleFilename()
        def OnChoiceEvent(event):
            ShowExampleFilename()
        def OnSaveImageSequence(event):
            filename=CalcFilename()
            extension = os.path.splitext(filename)[1]
            if extension == '':
                import wx
                dlg = wx.MessageDialog(self.frame, 'No extension specified',
                                       'playfmf error',
                                       wx.OK | wx.ICON_ERROR
                                       )
                dlg.ShowModal()
                dlg.Destroy()
                return
            filedir=os.path.split(filename)[0]
            if filedir == '':
                filedir = os.curdir
            if not os.path.isdir(filedir):
                os.makedirs(filedir)
            dlg2.filename = filename
#            dlg2._close_parent=True
            dlg2.Close(True)
        def OnImageSequenceBrowse(event):
            if wx_parent is not None:
                import wx
                dlg3 = wx.FileDialog(wx_parent,"Select basename...",
                                     os.getcwd(),"",
                                     "",wx.SAVE)
                try:
                    if dlg3.ShowModal()==wx.ID_OK:
                        basename=dlg3.GetPath()
                        xrc.XRCCTRL(dlg2,"image_basename").SetValue(basename)
                finally:
                    dlg3.Destroy()

        if wx_parent is not None:
            import wx
            import wx.xrc as xrc
            RES = xrc.EmptyXmlResource()
            RES.LoadFromString(open(RESFILE).read())
            dlg2 = RES.LoadDialog(wx_parent,"EXPORT_IMAGE_SEQUENCE")
            dlg2.filename = None
    #        dlg2._close_parent=False

            wx.EVT_BUTTON(dlg2, xrc.XRCCTRL(dlg2,"image_basename_browse").GetId(),
                       OnImageSequenceBrowse)
            wx.EVT_TEXT(dlg2,xrc.XRCCTRL(dlg2,"image_basename").GetId(),
                     OnTextEvent)
            wx.EVT_TEXT(dlg2,xrc.XRCCTRL(dlg2,"image_number_format").GetId(),
                     OnTextEvent)
            wx.EVT_CHOICE(dlg2,xrc.XRCCTRL(dlg2,"image_extension_choice").GetId(),
                       OnChoiceEvent)
            wx.EVT_BUTTON(dlg2, xrc.XRCCTRL(dlg2,"cancel_button").GetId(),
                       OnCancelImageSequence)
            wx.EVT_BUTTON(dlg2, xrc.XRCCTRL(dlg2,"save_button").GetId(),
                       OnSaveImageSequence)

            filename = None
            try:
                dlg2.ShowModal()
                filename = dlg2.filename
                flip_upside_down = xrc.XRCCTRL(dlg2,"flip_upside_down").GetValue()
    #            if dlg2._close_parent:
    #                dlg.Close()
            finally:
                dlg2.Destroy()
        else:
            filename = 'filename%02d.png'
            flip_upside_down = False
        return ImageSequenceSaver(filename,flip_upside_down,format,width_height)

class GenericSaverPlugin(object):
    def get_saver(self,wx_parent,format,widthheight):
        wildcard = self.get_wildcard()
        if wx_parent is not None:
            import wx
            wildcard += "|All files (*.*)|*.*"
            dlg2 = wx.FileDialog(wx_parent,"Save movie as...",os.getcwd(),"",
                                wildcard,wx.SAVE)
            filename = None
            try:
                if dlg2.ShowModal()==wx.ID_OK:
                    filename=dlg2.GetPath()
            finally:
                dlg2.Destroy()
            if filename is None:
                return
        else:
            ext = wildcard.split('|')[-1]
            assert ext[0]=='*'
            ext = ext[1:]
            filename = 'test_fmf_export' + ext
        saver = self.sub_get_saver(wx_parent,filename,format,widthheight)
        return saver

class TxtFileSaverPlugin(GenericSaverPlugin):
    def get_description(self):
        return 'text file of timestamps (*.txt)'
    def get_wildcard(self):
        return "Text file (*.txt)|*.txt"
    def sub_get_saver(self,wx_parent,filename,format,widthheight):
        class TxtSaver(object):
            def __init__(self,filename):
                self.txt_file = output_movie = open(filename,'w')
            def save(self,save_frame,timestamp):
                self.txt_file.write("%s\n"%(repr(timestamp,)))
            def close(self):
                self.txt_file.close()
        return TxtSaver(filename)

class FmfFileSaverPlugin(GenericSaverPlugin):
    def get_description(self):
        return 'Fly Movie Format (*.fmf)'
    def get_wildcard(self):
        return "Fly Movie Format (*.fmf)|*.fmf"
    def sub_get_saver(self,wx_parent,filename,format,widthheight):
        class FmfSaver(object):
            def __init__(self,filename,format):
                self.fmf_file = FlyMovieFormat.FlyMovieSaver(filename,
                                                             version=3,
                                                             format=format,
                                                             bits_per_pixel=bpp(format))
            def save(self,save_frame,timestamp):
                self.fmf_file.add_frame(save_frame,timestamp)
            def close(self):
                self.fmf_file.close()
        return FmfSaver(filename,format)
