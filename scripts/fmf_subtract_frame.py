import pkg_resources
import motmot.FlyMovieFormat.FlyMovieFormat as FMF
import motmot.imops.imops as imops
import sys, os
from pylab import prctile
import numpy as np
import collections
from optparse import OptionParser

def doit(input_fname,
         subtract_frame,
         start=None,
         stop=None,
         gain=1.0,
         offset=0.0,
         ):
    output_fname = os.path.splitext(input_fname)[0]+'.sub.fmf'
    in_fmf = FMF.FlyMovie(input_fname)
    input_format = in_fmf.get_format()
    input_is_color = imops.is_coding_color(input_format)


    if not subtract_frame.endswith('.fmf'):
        raise NotImplementedError('only fmf supported for --subtract-frame')
    tmp_fmf = FMF.FlyMovie(subtract_frame)
    if input_is_color:
        tmp_frame, tmp_timestamp = tmp_fmf.get_next_frame()
        subtract_frame = imops.to_rgb8(tmp_fmf.get_format(),tmp_frame)
        subtract_frame = subtract_frame.astype(np.float32) # force upconversion to float
    else:
        tmp_frame, tmp_timestamp = tmp_fmf.get_next_frame()
        subtract_frame = imops.to_mono8(tmp_fmf.get_format(),tmp_frame)
        subtract_frame = subtract_frame.astype(np.float32) # force upconversion to float

    if input_is_color:
        output_format = 'RGB8'
    else:
        output_format = 'MONO8'
    out_fmf = FMF.FlyMovieSaver(output_fname,
                                version=3,
                                format=output_format,
                                )
    try:
        if stop is None:
            stop = in_fmf.get_n_frames()-1
        if start is None:
            start = 0
        n_frames = stop-start+1
        n_samples = max(30,n_frames)
        for fno in np.linspace(start,stop,n_samples):
            fno = int(round(fno))
            in_fmf.seek(fno)
            frame,timestamp = in_fmf.get_next_frame()

            if input_is_color:
                frame = imops.to_rgb8(input_format,frame)
                new_frame = frame-subtract_frame
            else:
                frame = np.atleast_3d(frame)
                new_frame = frame-subtract_frame
            new_frame = np.clip(new_frame*gain + offset,0,255)
            new_frame = new_frame.astype(np.uint8)
            out_fmf.add_frame(new_frame,timestamp)
        out_fmf.close()
    except:
        os.unlink(output_fname)
        raise
    in_fmf.close()

def main():
    parser = OptionParser(usage="%prog [options] filename.fmf",
                          version="%prog 0.1")

    parser.add_option("--start", type='int',
                      help="first frame")

    parser.add_option("--stop", type='int',
                      help="last frame")

    parser.add_option("--gain", type='float',
                      default=1.0)

    parser.add_option("--offset", type='float',
                      default=127.0)

    (options, args) = parser.parse_args()
    filename = args[0]
    subtract_frame = args[1]
    doit(filename,
         subtract_frame,
         start = options.start,
         stop = options.stop,
         gain = options.gain,
         offset = options.offset,
         )

if __name__=='__main__':
    main()
