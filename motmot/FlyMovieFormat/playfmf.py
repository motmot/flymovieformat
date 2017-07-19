#!/usr/bin/env python
from __future__ import print_function
import sys, time, os, gc, datetime, warnings
from optparse import OptionParser

import pkg_resources # from setuptools
matplotlibrc = pkg_resources.resource_filename(__name__,"matplotlibrc") # trigger extraction
matplotlibrc_dir = os.path.split(matplotlibrc)[0]
os.environ['MATPLOTLIBRC'] = matplotlibrc_dir
RESFILE = pkg_resources.resource_filename(__name__,"playfmf.xrc") # trigger extraction

# py2exe stuff done
import FlyMovieFormat
import motmot.imops.imops as imops

import wx
import wx.xrc as xrc
import numpy
import numpy as np

# force use of numpy by matplotlib(FlyMovieFormat uses numpy)
import matplotlib
matplotlib.use('WXAgg')

import matplotlib as mpl
import matplotlib.cm as cm
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import matplotlib.colors as mcolors
import matplotlib.ticker

RES = xrc.EmptyXmlResource()
RES.LoadFromString(open(RESFILE).read())

bpp = FlyMovieFormat.format2bpp_func

_thresh = [(0.0,       0.0, 0.0),
          (1.0/255.0, 1.0, 1.0),
          (1.0, 1.0, 1.0)]
_cm_threshold_binary_data = {
    'red': _thresh,
    'green': _thresh,
    'blue': _thresh,
    }
LUTSIZE = mpl.rcParams['image.lut']
threshold_cmap = mcolors.LinearSegmentedColormap('threshold',
                                                 _cm_threshold_binary_data,
                                                 LUTSIZE)

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
##            print("%.2f, %.2f"%(mouse_event.xdata, mouse_event.ydata))

    def _convert_to_displayable(self,frame):
        if self.format in ['RGB8','ARGB8','YUV411','YUV422','RGB32f']:
            frame = imops.to_rgb8(self.format,frame)
        elif self.format in ['MONO8','MONO16']:
            frame = imops.to_mono8(self.format,frame)
        elif (self.format.startswith('MONO8:') or
              self.format.startswith('MONO32f:') or
              self.format.startswith('RAW8:')
              ):
            # bayer
            frame = imops.to_rgb8(self.format,frame)
        else:
            warnings.warn('unknown format "%s" conversion to displayable'%
                          self.format)
        #frame = self.convert_to_matplotlib(frame)
        return frame

    def init_plot_data(self,frame,format):
        self.axes = self.fig.add_subplot(111)
        a = self.axes # shorthand
        self.format = format
        frame = self._convert_to_displayable(frame)
        extent = 0, frame.shape[1]-1, frame.shape[0]-1, 0
        self.im = a.imshow( frame,
                            origin='upper',
                            interpolation='nearest',
                            extent=extent,
                            cmap=cm.pink,
                            )
        self.cbar = self.fig.colorbar(self.im)
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
        for cmap in 'gray','jet','pink','binary threshold':
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

            for name in egg.get_entry_map('motmot.FlyMovieFormat.exporter_plugins'):
                egg.activate()
                entry_point = egg.get_entry_info('motmot.FlyMovieFormat.exporter_plugins', name)
                try:
                    PluginClass = entry_point.load()
                except Exception as x:
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
        slider.SetRange( self.frame_offset+0, max(1,self.frame_offset+self.n_frames-1 ))
        slider.SetValue( self.frame_offset+frame_number )
    def OnColormapMenu(self, event):
        cmap_name = self.cmap_ids[event.GetId()] # e.g. 'pink', 'jet', etc.
        if cmap_name == 'binary threshold':
            cmap = threshold_cmap
        else:
            cmap = getattr(cm,cmap_name)
        self.plotpanel.im.set_cmap(cmap)
        # update display
        self.OnScroll(None)

    def OnNewMovie(self,flymovie,
                   corruption_fix=False,
                   force_format=None,
                   ):
        if corruption_fix:
            self.allow_partial_frames=True
        else:
            self.allow_partial_frames=False
        self.axes = self.plotpanel.fig.add_subplot(111) # not really new, just gets axes
        a = self.axes
        a.set_title('%s (%s)'%(flymovie.filename,flymovie.get_format()))

        self.fly_movie = flymovie
        self.n_frames = self.fly_movie.get_n_frames()
        frame,timestamp = self.fly_movie.get_frame(
            0, allow_partial_frames=self.allow_partial_frames)
        if corruption_fix:
            test_frame = self.n_frames
            while 1:
                test_frame -= 1
                try:
                    self.fly_movie.get_frame(
                        test_frame,
                        allow_partial_frames=True)
                except FlyMovieFormat.NoMoreFramesException:
                    print('no frame %d, shortening movie'%test_frame,file=sys.stderr)
                else:
                    # if we get here, it means we had a good frame
                    self.n_frames = test_frame+1
                    break

        self.frame_shape = frame.shape
        self.first_timestamp=timestamp
        frame_number = 0
        slider = self.slider
        slider.SetRange( self.frame_offset+0, max(self.frame_offset+self.n_frames-1,1) )
        slider.SetValue( self.frame_offset+frame_number )

        # window title
        self.frame.SetTitle('playfmf: %s'%(self.fly_movie.filename,))

        if force_format is None:
            self.format = self.fly_movie.get_format()
        else:
            self.format = force_format
        self.width_height = (self.fly_movie.get_width(),
                             self.fly_movie.get_height())

        self.plotpanel.init_plot_data(frame,self.format)
        self.plot_container.Layout()
        self.OnScroll(None)

    def OnScroll(self,event):
        frame_number = self.slider.GetValue() - self.frame_offset
        try:
            frame,timestamp = self.fly_movie.get_frame(
                frame_number,
                allow_partial_frames=self.allow_partial_frames)
        except FlyMovieFormat.NoMoreFramesException:
            frame_number = 0 - self.frame_offset
            self.slider.SetValue(frame_number)
            frame,timestamp = self.fly_movie.get_frame(
                frame_number,
                allow_partial_frames=self.allow_partial_frames)

        self.plotpanel.set_array(frame)

        label = xrc.XRCCTRL(self.frame,"time_rel_label")
        label.SetLabel('%.1f (msec)'%((timestamp-self.first_timestamp)*1000.0,))

        label = xrc.XRCCTRL(self.frame,"time_abs_label")

        try:
            my_datetime = datetime.datetime.fromtimestamp(timestamp)
            label.SetLabel('%.3f (sec) %s'%(timestamp, my_datetime.isoformat()))
        except ValueError as err:
            label.SetLabel('%.3f (sec)'%(timestamp,))

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

            for i in range(start,stop+1,interval):
                orig_frame,timestamp = self.fly_movie.get_frame(
                    i,
                    allow_partial_frames=self.allow_partial_frames)
                if orig_frame.dtype == np.uint8:
                    # usual case: frame encoded as uint8
                    crop_xmin = xmin*bpp(self.format)//8
                    crop_xmax = (xmax+1)*bpp(self.format)//8
                else:
                    # sometimes (e.g. YUV422) frame has alternate dtype
                    crop_xmin = xmin
                    crop_xmax = (xmax+1)
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
    usage = '%prog FILE [options]'

    parser = OptionParser(usage)

    parser.add_option("--disable-corruption-fix",
                      action='store_false', default=True,
                      dest='corruption_fix',
                      help="disable automatic fixing of corrupted .fmf files")

    parser.add_option("--frame-offset", type="int",
                      default=0,
                      help="add an integer offset to frame numbers")

    parser.add_option("--format", type="string", help="force the movie coding")

    (options, args) = parser.parse_args()

    if len(args)<1:
        parser.print_help()
        return

    filename = args[0]

    if (sys.platform.startswith('win') or
        sys.platform.startswith('darwin')):
        kws = dict(redirect=True,filename='playfmf.log')
    else:
        kws = {}
    app = MyApp(**kws)
    flymovie = FlyMovieFormat.FlyMovie(filename)
    app.OnNewMovie(flymovie,
                   corruption_fix=options.corruption_fix,
                   force_format=options.format,
                   )
    app.update_frame_offset(options.frame_offset)
    app.MainLoop()

if __name__ == '__main__':
    main()
