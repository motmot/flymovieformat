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

def encode_plane( frame, color=1 ):
    if color==0:
        buf = frame.tostring()
    elif color==1:
        # Convert pure luminance data (mono8) into YCbCr. First plane
        # is lumance data, next two planes are color chrominance.
        h,w = frame.shape
        nh = h*3//2
        f2 = numpy.zeros( (nh,w), dtype=numpy.uint8)
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
          autocrop = 1,
          color = 1,
          raw = False,
          non_blocking = False
          ):
    fmf = FMF.FlyMovie(filename)
    if not raw and fmf.get_format() not in ['MONO8','RAW8']:
        raise NotImplementedError('Only MONO8 and RAW8 formats are currently supported.')
    width = fmf.get_width()//(fmf.get_bits_per_pixel()//8)
    height = fmf.get_height()

    if autocrop==0:
        use_width = width
        use_height = height
    else:
        if autocrop==1:
            use_width  = (width >> 1) << 1
            use_height = height
        elif autocrop==2:
            use_width  = (width >> 4) << 4
            use_height  = (height >> 4) << 4
        else:
            raise ValueError('Unknown autocrop value: %s'%autocrop)
        if use_width!=width or use_height!=height:
            print >> sys.stderr, 'fmfcat autocropping from (%d,%d) to (%d,%d)'%(
                width,height, use_width,use_height)

    if raw:
        print >> sys.stderr, 'raw image width=%d height=%d' %(use_width,use_height)

    Y4M_MAGIC = 'YUV4MPEG2'
    Y4M_FRAME_MAGIC = 'FRAME'

    inter = 'Ip' # progressive
    if color==0:
        # Warn about not being in spec? OTOH it works in VLC and
        # Ubuntu Precise mplayer(2), but not Medibuntu Precise
        # mplayer.

        # See http://wiki.multimedia.cx/index.php?title=YUV4MPEG2
        colorspace = 'Cmono'
    elif color==1:
        colorspace = 'C420paldv'
    else:
        raise ValueError('unknown color: %s'%color)

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

Pipe the contents of an .fmf file to stdout in raw (--raw) or the
yuv4mpegpipe format. This allows an .fmf file to be converted to many
formats. For example, to convert the file x.fmf to x.mp4 using the
h264 codec:

%prog x.fmf | x264 --stdin y4m - -o x.mp4

the raw format can be viewed directly using gstreamer (but rememeber to set
the video width and height)

%prog x.fmf --raw | gst-launch-0.10 \\
 fdsrc ! videoparse format="gray8" width=1296 height=966 \\
 ! ffmpegcolorspace ! xvimagesink
"""

    parser = OptionParser(usage)

    parser.add_option('--rotate-180', action='store_true',
                      default=False )

    parser.add_option('--autocrop', default=1, type=int,
                      help='autocrop image (0:no, 1: width%2==0, '
                                            '2=width%16==0,height%16==0) ')

    parser.add_option('--color', default=1, type=int,
                      help='set color mode (0:mono, 1:YCbCr 420)')

    parser.add_option('--raten', default=25, type=int,
                      help='numerator of fps (frame rate)')
    parser.add_option('--rated', default=1, type=int,
                      help='denominator of fps (frame rate)')

    parser.add_option('--aspectn', default=0, type=int,
                      help='numerator of aspect ratio')
    parser.add_option('--aspectd', default=0, type=int,
                      help='denominator of aspect ratio')

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
          raten = options.raten,
          rated = options.rated,
          aspectn = options.aspectn,
          aspectd = options.aspectd,
          rotate_180 = options.rotate_180,
          autocrop = options.autocrop,
          color = options.color,
          raw = options.raw,
          non_blocking = options.non_blocking,
          )

if __name__=='__main__':
    main()
