import pkg_resources
import numpy as np
import pyglet
from pygarrayimage.arrayimage import ArrayInterfaceImage
import sys, time
import motmot.FlyMovieFormat.FlyMovieFormat as fmf_mod
import motmot.imops.imops as imops

from pyglet.gl import *
from pyglet import window
from pyglet import image

def convert(frame,format):
    if format in ['RGB8','ARGB8','YUV411','YUV422']:
        frame = imops.to_rgb8(format,frame)
    elif format in ['MONO8','MONO16']:
        frame = imops.to_mono8(format,frame)
    elif (format.startswith('MONO8:') or
          format.startswith('MONO32f:')):
        # bayer
        frame = imops.to_rgb8(format,frame)
    return frame

def main():
    fmf_filename = sys.argv[1]

    fmf = fmf_mod.FlyMovie(fmf_filename)
    frame,timestamp = fmf.get_next_frame()
    frame = convert(frame,fmf.format)

    w = window.Window(visible=False, resizable=True)
    aii = ArrayInterfaceImage(frame)
    img = aii.texture
    w.width = img.width
    w.height = img.height
    w.set_visible()

    prev_n_frames = None
    while not w.has_exit:
        # TODO add some throttling here...
        w.dispatch_events()

        n_frames=fmf.compute_n_frames_from_file_size(only_full_frames=True)
        if prev_n_frames != n_frames:
            prev_n_frames = n_frames
            fmf.seek(n_frames-1)
            frame,timestamp = fmf.get_next_frame()
            frame = convert(frame,fmf.format)

            aii.view_new_array(frame)

            img.blit(0, 0, 0)
            w.flip()

if __name__=='__main__':
    main()
