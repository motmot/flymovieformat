import os, sys
import FlyMovieFormat
import Image
from optparse import OptionParser
import motmot.imops.imops as imops
import warnings

def main():
    usage = """%prog FILE [options]

Example:

fmf2bmps myvideo.fmf --start=10 --stop=100 --extension=jpg --outdir=tmp
"""

    parser = OptionParser(usage)
    parser.add_option('--start',type='int',default=0,help='first frame to save')
    parser.add_option('--stop',type='int',default=-1,help='last frame to save')
    parser.add_option('--interval',type='int',default=1,help='save every Nth frame')
    parser.add_option('--extension',type='string',default='bmp',
                      help='image extension (default: bmp)')
    parser.add_option('--outdir',type='string',default=None,
                      help='directory to save images (default: same as fmf)')
    parser.add_option('--progress',action='store_true',default=False,
                      help='show progress bar')
    parser.add_option('--prefix',default=None,type='str',
                      help='prefix for image filenames')
    (options, args) = parser.parse_args()

    if len(args)<1:
        parser.print_help()
        return

    filename = args[0]
    startframe = options.start
    endframe = options.stop
    interval = options.interval
    assert interval >= 1
    imgformat = options.extension

    base,ext = os.path.splitext(filename)
    if ext != '.fmf':
        print 'fmf_filename does not end in .fmf'
        sys.exit()

    path,base = os.path.split(base)
    if options.prefix is not None:
        base = options.prefix

    if options.outdir is None:
        outdir = path
    else:
        outdir = options.outdir

    fly_movie = FlyMovieFormat.FlyMovie(filename)
    fmf_format = fly_movie.get_format()
    n_frames = fly_movie.get_n_frames()
    if endframe < 0 or endframe >= n_frames:
        endframe = n_frames - 1

    fly_movie.seek(startframe)
    frames = range(startframe,endframe+1,interval)
    n_frames = len(frames)
    if options.progress:
        import progressbar
        widgets=['fmf2bmps', progressbar.Percentage(), ' ',
                 progressbar.Bar(), ' ', progressbar.ETA()]
        pbar=progressbar.ProgressBar(widgets=widgets,
                                     maxval=n_frames).start()
    else:
        pbar = None

    for count,frame_number in enumerate(frames):
        if pbar is not None:
            pbar.update(count)
        frame,timestamp = fly_movie.get_frame(frame_number)

        mono=False
        if (fmf_format in ['RGB8','ARGB8','YUV411','YUV422'] or
            fmf_format.startswith('MONO8:') or
            fmf_format.startswith('MONO32f:')):
            save_frame = imops.to_rgb8(fmf_format,frame)
        else:
            if fmf_format not in ['MONO8','MONO16']:
                warnings.warn('converting unknown fmf format %s to mono'%(
                    fmf_format,))
            save_frame = imops.to_mono8(fmf_format,frame)
            mono=True
        h,w=save_frame.shape[:2]
        if mono:
            im = Image.fromstring('L',(w,h),save_frame.tostring())
        else:
            im = Image.fromstring('RGB',(w,h),save_frame.tostring())
        f='%s_%08d.%s'%(os.path.join(outdir,base),frame_number,imgformat)
        im.save(f)
    if pbar is not None:
        pbar.finish()

if __name__=='__main__':
    main()
