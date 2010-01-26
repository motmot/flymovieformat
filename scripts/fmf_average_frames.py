import pkg_resources
import motmot.FlyMovieFormat.FlyMovieFormat as FMF
import motmot.imops.imops as imops
import sys, os
from pylab import prctile
import numpy as np
import collections
from optparse import OptionParser

def doit(input_fname,
         single_channel=False,
         start=None,
         stop=None,
         ):
    output_fname = os.path.splitext(input_fname)[0]+'.av.fmf'
    in_fmf = FMF.FlyMovie(input_fname)
    input_format = in_fmf.get_format()
    input_is_color = imops.is_coding_color(input_format)

    if single_channel is not None:
        if not input_is_color:
            warnings.warn('ignoring --single-channel option for non-color input')
            single_channel = False
        output_format = 'MONO32f'
    else:
        if input_is_color:
            output_format = 'RGB32f'
        else:
            output_format = 'MONO32f'
    out_fmf = FMF.FlyMovieSaver(output_fname,
                                version=3,
                                format=output_format,
                                )
    try:
        if input_is_color:
            channels = [('red',0),('green',1),('blue',2)]
        else:
            channels = [('gray',0)]
        channel_dict = dict(channels)

        if stop is None:
            stop = in_fmf.get_n_frames()-1
        if start is None:
            start = 0
        n_frames = stop-start+1
        n_samples = max(30,n_frames)
        frame,timestamp0 = in_fmf.get_next_frame()
        if input_is_color:
            frame = imops.to_rgb8(input_format,frame)
        else:
            frame = np.atleast_3d(frame)
        cumsum = np.zeros( frame.shape, dtype=np.float32)
        for fno in np.linspace(start,stop,n_samples):
            fno = int(round(fno))
            in_fmf.seek(fno)
            frame,timestamp = in_fmf.get_next_frame()
            if input_is_color:
                frame = imops.to_rgb8(input_format,frame)
            else:
                frame = np.atleast_3d(frame)
            cumsum += frame

        frame = cumsum/n_samples

        if output_format == 'MONO32f':
            # drop dimension
            assert frame.shape[2]==1
            frame = frame[:,:,0]
        out_fmf.add_frame(frame,timestamp0)
        out_fmf.close()
    except:
        os.unlink(output_fname)
        raise
    in_fmf.close()

def main():
    parser = OptionParser(usage="%prog [options] filename.fmf",
                          version="%prog 0.1")

    parser.add_option("--single-channel", type='string',default=None,
                      help="use single channel color only")

    parser.add_option("--start", type='int',
                      help="first frame")

    parser.add_option("--stop", type='int',
                      help="last frame")

    (options, args) = parser.parse_args()
    filename = args[0]
    doit(filename,
         start = options.start,
         stop = options.stop,
         single_channel=options.single_channel,
         )

if __name__=='__main__':
    main()
