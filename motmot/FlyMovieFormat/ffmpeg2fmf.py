import pyglet
import pyglet.media as media
import numpy as np
import sys, os
import motmot.FlyMovieFormat.FlyMovieFormat as fmf_mod
from optparse import OptionParser

def get_frame(source):
    ts = source.get_next_video_timestamp()
    im = source.get_next_video_frame()
    if im is None:
        return None, None
    n_8bit_chans = im.pitch / im.width
    imn = np.fromstring(im.data,np.uint8)
    if n_8bit_chans==1:
        imn.resize((im.height,im.width))
    else:
        imn.resize((im.height,im.width,n_8bit_chans))
        imn = np.mean(imn,axis=2) # collapse last dim, convert to float64
        imn = imn.astype(np.uint8) # convert back to uint8
    imn2 = np.array(imn,copy=True)
    return imn2, ts

def main():
    usage = '%prog [options] FILE'

    parser = OptionParser(usage)

    parser.add_option("--format", type='string', default=None)

    (options, args) = parser.parse_args()

    in_filename = args[0]

    if options.format is None or options.format.lower() != 'mono8':
        raise NotImplementedError('Only mono8 format is supported with no '
                                  'autodetection. Use "--format=mono8".')

    source = media.load(in_filename)
    imn, ts = get_frame(source)

    file_base = os.path.splitext(in_filename)[0]
    out_filename = file_base+'.fmf'

    fmf = fmf_mod.FlyMovieSaver(out_filename,
                                format='MONO8',
                                bits_per_pixel=8,
                                version=3,
                                )

    while imn is not None:
        fmf.add_frame( imn, ts )
        imn, ts = get_frame(source)
