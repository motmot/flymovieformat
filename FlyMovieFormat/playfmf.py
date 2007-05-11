#!/usr/bin/env python
import sys, time, os, gc

import pkg_resources # from setuptools
matplotlibrc = pkg_resources.resource_filename(__name__,"matplotlibrc") # trigger extraction
matplotlibrc_dir = os.path.split(matplotlibrc)[0]
os.environ['MATPLOTLIBRC'] = matplotlibrc_dir
RESFILE = pkg_resources.resource_filename(__name__,"playfmf.xrc") # trigger extraction

# py2exe stuff done
import FlyMovieFormat
import Image
import imops

from wxwrap import wx
import wxPython.xrc as xrc

# force use of numpy by matplotlib(FlyMovieFormat uses numpy)
import matplotlib
from matplotlib import rcParams
rcParams['numerix'] = 'numpy'
matplotlib.use('WXAgg')

import matplotlib.cm as cm
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import matplotlib.numerix as numerix
import matplotlib.ticker

RES = xrc.wxEmptyXmlResource()
RES.LoadFromString(open(RESFILE).read())

bpp = FlyMovieFormat.format2bpp

class MovieAnnotation:
    def __init__( self, filename ):
        """Attempt to open annotation file."""
        try:
            self.annotation_file = open( '%s.ann'%(filename,), "r" )
        except IOError:
            self.annotation_exists = False
            self.show_annotation = False
        else:
            self.annotation_exists = True
            self.show_annotation = True

    def __del__( self ):
        """Close annotation file, if open."""
        if self.annotation_exists:
            self.annotation_file.close()

    def _get_ann( self, framenumber ):
        return False

    def add_ann_to_frame( self, frame, framenumber ):
        data = self._get_ann( framenumber )
        return frame

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
                if self.format=='MONO8':
                    im=Image.fromstring('L',self.width_height,save_frame.tostring())
                elif self.format in ['RGB8','ARGB8','YUV411','YUV422']:
                    rgb8 = imops.to_rgb8(self.format,save_frame)
                    im=Image.fromstring('RGB', self.width_height,
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
            dlg3 = wx.FileDialog(wx_parent,"Select basename...",
                                 os.getcwd(),"",
                                 "",wx.SAVE)
            try:
                if dlg3.ShowModal()==wx.ID_OK:
                    basename=dlg3.GetPath()
                    xrc.XRCCTRL(dlg2,"image_basename").SetValue(basename)
            finally:
                dlg3.Destroy()

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
        return ImageSequenceSaver(filename,flip_upside_down,format,width_height)

class GenericSaverPlugin(object):
    def get_saver(self,wx_parent,format,widthheight):
        wildcard = self.get_wildcard()
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
                                                             bits_per_pixel=bpp[format])
            def save(self,save_frame,timestamp):
                self.fmf_file.add_frame(save_frame,timestamp)
            def close(self):
                self.fmf_file.close()
        return FmfSaver(filename,format)
    
class PlotPanel(wx.Panel):

    def __init__(self, parent,statbar=None):
        wx.Panel.__init__(self, parent, -1)

        self.fig = Figure((5,4), 75)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)
        if statbar is not None:
            self.toolbar = NavigationToolbar2Wx(self.canvas) #matplotlib toolbar
            self.toolbar.set_status_bar(statbar)
            self.toolbar.Realize()
        else:
            self.toolbar = None
                           
        #self.canvas.mpl_connect('button_press_event',self._onButton)

        # Now put all into a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 1, wx.LEFT|wx.TOP|wx.GROW)
        
        if self.toolbar is not None:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)

        self.SetSizer(sizer)
        #self.Fit()
        #self.Update()
        
##    def _onButton(self,mouse_event):
##        if mouse_event.inaxes:
##            print "%.2f, %.2f"%(mouse_event.xdata, mouse_event.ydata)

    def _convert_to_displayable(self,frame):
        if self.format in ['RGB8','ARGB8','YUV411','YUV422']:
            frame = imops.to_rgb8(self.format,frame)
        elif self.format in ['MONO8','MONO16']:
            frame = imops.to_mono8(self.format,frame)
        #frame = self.convert_to_matplotlib(frame)
        return frame

    def init_plot_data(self,frame,format):
        a = self.fig.add_subplot(111)
        self.format = format
        frame = self._convert_to_displayable(frame)
        extent = 0, frame.shape[1]-1, frame.shape[0]-1, 0
        self.im = a.imshow( frame,
                            origin='upper',
                            interpolation='nearest',
                            extent=extent,
                            cmap=cm.pink,
                            )
        self.im.set_clim(0,255)
        a.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter(useOffset=False))
        a.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter(useOffset=False))
        a.fmt_xdata = str
        a.fmt_ydata = str

        if 0:
            # flipLR (x) for display
            xlim = a.get_xlim()
            a.set_xlim((xlim[1],xlim[0]))
        
        if self.toolbar is not None:
            self.toolbar.update()

    def GetToolBar(self):
        # You will need to override GetToolBar if you are using an 
        # unmanaged toolbar in your frame
        return self.toolbar
		
    def onEraseBackground(self, evt):
        # this is supposed to prevent redraw flicker on some X servers...
        pass

##     def convert_to_matplotlib(self,frame):
##         # XXX this should not be needed -- figure out what's wrong
##         frame = frame.astype(numerix.Float)
##         frame = frame/255.0
##         return frame

    def set_array(self,frame):
        frame = self._convert_to_displayable(frame)
        self.im.set_array(frame)
        self.canvas.draw()

class MyApp(wx.App):
    def OnInit(self):
        self.res = RES
        
        # main frame and panel ---------

        self.frame = self.res.LoadFrame(None,"MainFrame")
        
        statbar = matplotlib.backends.backend_wx.StatusBarWx(self.frame)
        self.frame.SetStatusBar(statbar)
        
        self.panel = xrc.XRCCTRL(self.frame,"MainPanel")

        # menubar ----------------------
        
        menubar = self.res.LoadMenuBarOnFrame(self.frame,"MENUBAR")
        self.frame_offset = 0
        wx.EVT_MENU(self.frame, xrc.XRCID("set_frame_offset"),
                 self.OnSetFrameOffset)
        wx.EVT_MENU(self.frame, xrc.XRCID("export_smaller_movie"),
                 self.OnExportSmallerMovie)
        wx.EVT_MENU(self.frame, xrc.XRCID("quit_menuitem"), self.OnQuit)

        colormap_menu = wx.Menu()
        self.cmap_ids={}
        for cmap in 'gray','jet','pink':
            id = wx.NewId()
            colormap_menu.Append(id, cmap)
            wx.EVT_MENU(self.frame, id, self.OnColormapMenu)
            self.cmap_ids[id]=cmap
        menubar.Append(colormap_menu,"&Colormap")
            
        # matplotlib panel -------------

        # container for matplotlib panel (I like to make a container
        # panel for our panel so I know where it'll go when in XRCed.)
        self.plot_container = xrc.XRCCTRL(self.frame,"plot_container_panel")
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # matplotlib panel itself
        self.plotpanel = PlotPanel(self.plot_container,statbar=statbar)

        label = xrc.XRCCTRL(self.frame,"time_abs_label")
        #label.SetLabel('%.3f (sec)'%(timestamp,))

        # wx boilerplate
        sizer.Add(self.plotpanel, 1, wx.EXPAND)
        self.plot_container.SetSizer(sizer)

        # slider ------------------

        slider = xrc.XRCCTRL(self.frame,"frame_slider")
        wx.EVT_COMMAND_SCROLL(slider, slider.GetId(), self.OnScroll)
        self.slider = slider

        # final setup ------------------
        
        sizer = self.panel.GetSizer()
        
        self.frame.SetSize((800,800))
        self.frame.Show(1)
        self.SetTopWindow(self.frame)

        self._load_plugins()

        return True

    def _load_plugins(self):
        PluginClasses = []
        pkg_env = pkg_resources.Environment()
        for name in pkg_env:
            egg = pkg_env[name][0]
            modules = []

            for name in egg.get_entry_map('FlyMovieFormat.exporter_plugins'):
                egg.activate()
                entry_point = egg.get_entry_info('FlyMovieFormat.exporter_plugins', name)
                try:
                    PluginClass = entry_point.load()
                except Exception,x:
                    if int(os.environ.get('PLAYFMF_RAISE_ERRORS','0')):
                        raise x
                    else:
                        import warnings
                        warnings.warn('could not load plugin %s: %s'%(str(entry_point),str(x)))
                        continue
                PluginClasses.append( PluginClass )
                modules.append(entry_point.module_name)
        # make instances of plugins
        self.plugins = [PluginClass() for PluginClass in PluginClasses]

    def OnSetFrameOffset(self, event):
        dlg=wx.TextEntryDialog(self.frame, 'Frame offset',
                              'Set frame offset',str(self.frame_offset))
        try:
            if dlg.ShowModal() == wx.ID_OK:
                new_frame_offset = int(dlg.GetValue())
                self.update_frame_offset(new_frame_offset)
        finally:
            dlg.Destroy()

    def update_frame_offset(self, new_frame_offset):
        frame_number = self.slider.GetValue() - self.frame_offset
        self.frame_offset = new_frame_offset
        slider = self.slider
        slider.SetRange( self.frame_offset+0, self.frame_offset+self.n_frames-1 )
        slider.SetValue( self.frame_offset+frame_number )
    def OnColormapMenu(self, event):
        cmap_name = self.cmap_ids[event.GetId()]
        cmap = getattr(cm,cmap_name)
        self.plotpanel.im.set_cmap(cmap)
        # update display
        self.OnScroll(None)
    
    def OnNewMovie(self,filename):
        a = self.plotpanel.fig.add_subplot(111) # not really new, just gets axes
        
        self.fly_movie = FlyMovieFormat.FlyMovie(filename)
        self.n_frames = self.fly_movie.get_n_frames()
        frame,timestamp = self.fly_movie.get_frame(0)
        self.frame_shape = frame.shape
        self.first_timestamp=timestamp
        frame_number = 0
        slider = self.slider
        slider.SetRange( self.frame_offset+0, self.frame_offset+self.n_frames-1 )
        slider.SetValue( self.frame_offset+frame_number )
        
        self.frame.SetTitle('playfmf: %s'%(filename,)) # window title    
        self.fly_movie = FlyMovieFormat.FlyMovie(filename)
        self.format = self.fly_movie.get_format()
        self.width_height = (self.fly_movie.get_width()//(bpp[self.format]//8),
                             self.fly_movie.get_height())
        
        # movie annotation, if present
        self.annotation = MovieAnnotation( filename )

        # set mat-figure title
        if self.annotation.annotation_exists:
            a.set_title('%s %s +ann'%(filename,self.format))
        else:
            a.set_title('%s %s'%(filename,self.format))
        
        frame,timestamp = self.fly_movie.get_frame(0)
        if self.annotation.show_annotation:
            frame = self.annotation.add_ann_to_frame( frame, 0 )
        self.plotpanel.init_plot_data(frame,self.format)

##        self.plot_container.Update()
        self.plot_container.Layout()
##        self.frame.Update()
##        self.frame.Layout()
##        self.frame.GetSizer().Layout()
##        ## Forces a resize event to get around a minor bug...
##        self.frame.SetSize(self.frame.GetSize())
##        ## Forces a resize event to get around a minor bug...
##        self.plot_container.SetSize(self.plot_container.GetSize())

    def OnScroll(self,event):
        frame_number = self.slider.GetValue() - self.frame_offset
        frame,timestamp = self.fly_movie.get_frame(frame_number)

        if self.annotation.show_annotation:
            frame = self.annotation.add_ann_to_frame( frame, frame_number )

        self.plotpanel.set_array(frame)
        
        label = xrc.XRCCTRL(self.frame,"time_rel_label")
        label.SetLabel('%.1f (msec)'%((timestamp-self.first_timestamp)*1000.0,))
        
        label = xrc.XRCCTRL(self.frame,"time_abs_label")
        
        time_fmt = '%Y-%m-%d %H:%M:%S %Z%z'
        label.SetLabel('%.3f (sec) %s'%(timestamp,
                                        time.strftime(time_fmt, time.localtime(timestamp))))
        
    def OnQuit(self, event):
        self.frame.Close(True)

    def OnExportSmallerMovie(self, event):
        def OnCancelExportSmallerMovie(event):
            dlg.Close(True)
        def OnSaveExportSmallerMovie(event):
            xmin = int(xrc.XRCCTRL(dlg,"xmin_textctrl").GetValue())
            xmax = int(xrc.XRCCTRL(dlg,"xmax_textctrl").GetValue())
            ymin = int(xrc.XRCCTRL(dlg,"ymin_textctrl").GetValue())
            ymax = int(xrc.XRCCTRL(dlg,"ymax_textctrl").GetValue())
            
            start = int(xrc.XRCCTRL(dlg,"start_frame").GetValue())
            stop = int(xrc.XRCCTRL(dlg,"stop_frame").GetValue())
            interval = int(xrc.XRCCTRL(dlg,"interval_frames").GetValue())

            flipLR = xrc.XRCCTRL(dlg,"flipLR").GetValue()

            description = xrc.XRCCTRL(dlg,"movie_format_choice").GetStringSelection()

            assert xmin<=xmax
            assert ymin<=ymax

            for plugin in self.plugins:
                if description == plugin.get_description():
                    break
                
            assert description == plugin.get_description()

            saver = plugin.get_saver(dlg,self.format,self.width_height)
            dlg.Close()

            crop_xmin = xmin*bpp[self.format]//8
            crop_xmax = (xmax+1)*bpp[self.format]//8

            for i in xrange(start,stop+1,interval):
                orig_frame,timestamp = self.fly_movie.get_frame(i)
                save_frame = orig_frame[ymin:ymax+1,crop_xmin:crop_xmax]
                if flipLR:
                    save_frame = save_frame[:,::-1]
                saver.save( save_frame, timestamp )
            saver.close()
            
        dlg = self.res.LoadDialog(self.frame,"EXPORT_DIALOG")

        format_choice_ctrl = xrc.XRCCTRL(dlg,"movie_format_choice")
        for plugin in self.plugins:
            description = plugin.get_description()
            format_choice_ctrl.Append(description)
        
        xrc.XRCCTRL(dlg,"xmax_textctrl").SetValue(str(self.width_height[0]-1))
        xrc.XRCCTRL(dlg,"ymax_textctrl").SetValue(str(self.width_height[1]-1))
        xrc.XRCCTRL(dlg,"stop_frame").SetValue(str(self.n_frames-1))
        
        cancel_button=xrc.XRCCTRL(dlg,"cancel_button")
        wx.EVT_BUTTON(dlg, cancel_button.GetId(),OnCancelExportSmallerMovie)
        save_button=xrc.XRCCTRL(dlg,"save_button")
        wx.EVT_BUTTON(dlg, save_button.GetId(),OnSaveExportSmallerMovie)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
    
def main():
    try:
        filename = sys.argv[1]
    except IndexError:
        raise RuntimeError('must provide FMF filename as command line argument')
    
    if len(sys.argv) > 2:
        frame_offset = int(sys.argv[2])
    else:
        frame_offset = 0

    #app = MyApp(0)
    if sys.platform.startswith('win') or sys.platform.startswith('darwin'):
        kws = dict(redirect=True,filename='playfmf.log')
    else:
        kws = {}
    app = MyApp(**kws)
    app.OnNewMovie(filename)
    app.update_frame_offset(frame_offset)
    app.MainLoop()

if __name__ == '__main__':
    main()
