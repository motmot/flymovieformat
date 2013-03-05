from optparse import OptionParser
import sys
import motmot.FlyMovieFormat.FlyMovieFormat as FMF
import numpy
import fcntl, os
import time

if 1:
    import signal
    # Restore the default SIGPIPE handler (Python sets a handler to
    # raise an exception).
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def encode_plane( frame, color=False ):
    if not color:
        buf = frame.tostring()
    else:
        # 420
        # See IMC1 at http://msdn.microsoft.com/en-us/library/windows/desktop/dd206750(v=vs.85).aspx
        h,w = frame.shape
        f2 = numpy.zeros( (h*2,w), dtype=numpy.uint8)
        f2[:h, :] = frame
        f2[h:, :] = 128
        buf = f2.tostring()
    return buf

def doit( filename,
          raten=25, # numerator
          rated=1,  # denom
          aspectn = 0, # numerator
          aspectd = 0, # denom
          rotate_180 = False,
          autocrop = False,
          color = False,
          raw = False,
          non_blocking = False
          ):
    fmf = FMF.FlyMovie(filename)
    if not raw and fmf.get_format() not in ['MONO8','RAW8']:
        raise NotImplementedError('Only MONO8 and RAW8 formats are currently supported.')
    width = fmf.get_width()//(fmf.get_bits_per_pixel()//8)
    height = fmf.get_height()

    if autocrop:
        use_width  = (width >> 4) << 4
        use_height  = (height >> 4) << 4
        print >> sys.stderr, 'fmfcat autocropping from (%d,%d) to (%d,%d)'%(
            width,height, use_width,use_height)
    else:
        use_width = width
        use_height = height

    if raw:
        print >> sys.stderr, 'raw image width=%d height=%d' %(use_width,use_height)

    Y4M_MAGIC = 'YUV4MPEG2'
    Y4M_FRAME_MAGIC = 'FRAME'

    inter = 'Ip' # progressive
    if not color:
        # Warn about not being in spec? OTOH it works in VLC and
        # Ubuntu Precise mplayer(2), but not Medibuntu Precise
        # mplayer.

        # See http://wiki.multimedia.cx/index.php?title=YUV4MPEG2
        colorspace = 'Cmono'
    else:
        # This is only working in VLC
        colorspace = 'C420'

    out_fd = sys.stdout

    if non_blocking:
        fcntl.fcntl(out_fd.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

    if not raw:
        out_fd.write('%(Y4M_MAGIC)s W%(use_width)d H%(use_height)d '
                     'F%(raten)d:%(rated)d %(inter)s A%(aspectn)d:%(aspectd)d '
                     '%(colorspace)s Xconverted-by-fmfcat\n'%locals())
    while 1:
        try:
            frame,timestamp = fmf.get_next_frame()
        except FMF.NoMoreFramesException, err:
            break

        if not raw:
            out_fd.write('%(Y4M_FRAME_MAGIC)s\n'%locals())

        if rotate_180:
            frame = numpy.rot90(numpy.rot90(frame))

        if autocrop:
            frame = frame[:use_height,:use_width]

        buf = encode_plane( frame, color=color )
        while 1:
            try:
                out_fd.write(buf)
                break
            except IOError, err:
                if err.errno == 11:
                    print >> sys.stderr, 'write error, waiting...'
                    time.sleep(0.1)
                    continue
                raise
        out_fd.flush()

def main():
    usage = """%prog FILENAME [options]

Pipe the contents of an .fmf file to stdout in raw (--raw) or the yuv4mpegpipe
format. This allows an .fmf file to be converted to any format that
ffmpeg supports. For example, to convert the file x.fmf to x.avi using
the MPEG4 codec:

%prog x.fmf > x.y4m
ffmpeg -vcodec msmpeg4v2 -i x.y4m x.avi

the raw format can be viewed directly using gstreamer (but rememeber to set
the video width and height)

%prog x.fmf --raw | gst-launch-0.10 \\
 fdsrc ! videoparse format="gray8" width=1296 height=966 \\
 ! ffmpegcolorspace ! xvimagesink
"""

    parser = OptionParser(usage)

    parser.add_option('--rotate-180', action='store_true',
                      default=False )

    parser.add_option('--autocrop', action='store_true',
                      default=False )

    parser.add_option('--color', action='store_true',
                      default=False )

    parser.add_option('--raw', action='store_true',
                      default=False,
                      help='do not include any YUV4MPEG2 headers, just output raw frame data' )

    parser.add_option('--non-blocking', action='store_true',
                      default=False,
                      help='set stdout to be nonblocking (helps with ffmpeg, causes corruption with gstreamer' )


    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return

    filename = args[0]

    doit( filename = args[0],
          rotate_180 = options.rotate_180,
          autocrop = options.autocrop,
          color = options.color,
          raw = options.raw,
          non_blocking = options.non_blocking
          )

if __name__=='__main__':
    main()
