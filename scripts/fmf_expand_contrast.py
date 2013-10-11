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
         gain=1.0,
         offset=0.0,
         blur=0.0,
         ):
    if blur != 0:
        import scipy.ndimage.filters

    output_fname = os.path.splitext(input_fname)[0]+'.highcontrast.fmf'
    in_fmf = FMF.FlyMovie(input_fname)
    input_format = in_fmf.get_format()
    input_is_color = imops.is_coding_color(input_format)

    if single_channel is not None:
        if not input_is_color:
            warnings.warn('ignoring --single-channel option for non-color input')
            single_channel = False
        output_format = 'MONO8'
    else:
        if input_is_color:
            output_format = 'RGB8'
        else:
            output_format = 'MONO8'
    out_fmf = FMF.FlyMovieSaver(output_fname,
                                version=3,
                                format=output_format,
                                )
    try:
        # pass 1 - get 5,95 percentiles
        if input_is_color:
            channels = [('red',0),('green',1),('blue',2)]
        else:
            channels = [('gray',0)]
        channel_dict = dict(channels)
        minvs = collections.defaultdict(list)
        maxvs = collections.defaultdict(list)
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
            else:
                frame = np.atleast_3d(frame)
            for channel_name, channel_idx in channels:
                minv,maxv=prctile(frame[:,:,channel_idx].ravel(),p=(5.0,95.0))
                minvs[channel_name].append(minv)
                maxvs[channel_name].append(maxv)

        orig_center = {}
        orig_range = {}
        for channel_name, channel_idx in channels:
            minv = np.min(minvs[channel_name])
            maxv = np.max(maxvs[channel_name])
            orig_center[channel_name] = (minv+maxv)/2.0
            orig_range[channel_name] = maxv-minv

        new_center = 127.5+offset
        new_range = 127.5*gain

        # pass 2 - rescale and save
        in_fmf.seek(0)
        for fno in range(start,stop+1):
            frame,timestamp = in_fmf.get_next_frame()
            if input_is_color:
                frame = imops.to_rgb8(input_format,frame)
            else:
                frame = np.atleast_3d(frame)

            if single_channel is not None:
                # input is, by definition, color
                frame = frame[:,:,channel_dict[single_channel]] # drop all but single_channel dim
                frame = frame.astype(np.float32)
                frame = (frame-orig_center[single_channel])/orig_range[single_channel]
                frame = frame * new_range + new_center
                frame = np.atleast_3d(frame) # add dim
            else:
                frame = frame.astype(np.float32)
                for channel_name, channel_idx in channels:
                    frame[:,:,channel_idx] = (frame[:,:,channel_idx]-orig_center[channel_name])/orig_range[channel_name]
                    frame[:,:,channel_idx] = frame[:,:,channel_idx] * new_range + new_center

            if blur != 0:
                for chan in range( frame.shape[2] ):
                    # filter each channel independently
                    frame[:,:,chan] = scipy.ndimage.filters.gaussian_filter(frame[:,:,chan], blur)
            frame = np.clip(frame,0,255).astype(np.uint8)
            if output_format is 'MONO8':
                # drop dimension
                assert frame.shape[2]==1
                frame = frame[:,:,0]
            out_fmf.add_frame(frame,timestamp)
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

    parser.add_option("--gain", type='float',
                      default=1.0)

    parser.add_option("--offset", type='float',
                      default=1.0)

    parser.add_option("--blur", type='float',
                      default=0.0)

    (options, args) = parser.parse_args()
    filename = args[0]
    doit(filename,
         start = options.start,
         stop = options.stop,
         gain = options.gain,
         offset = options.offset,
         single_channel=options.single_channel,
         blur = options.blur,
         )

if __name__=='__main__':
    main()
