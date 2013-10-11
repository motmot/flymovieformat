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

def check_format_and_color(buffer_width, buffer_height, format=None, color=1):
    final_width, final_height = buffer_width, buffer_height

    if format in ['mono8:bggr','mono8:gbrg', 'mono8:grbg',
                  'raw8:bggr','raw8:gbrg', 'raw8:grbg',
                  ] and color==0:
        print >> sys.stderr, 'fmfcat taking green channel as luminance'
        final_width = buffer_width//2
        final_height = buffer_height//2
    elif format=='rgb8':
        final_width = buffer_width//3
    return final_width, final_height

def quarter(cr):
    """get quarter size (by area) array with low-pass filtering"""
    assert cr.dtype==numpy.uint8
    assert cr.ndim==2
    assert cr.shape[0]%2==0
    assert cr.shape[1]%2==0
    accum = numpy.zeros((cr.shape[0]//2, cr.shape[1]//2),dtype=numpy.uint16)
    accum += cr[0::2,0::2]
    accum += cr[0::2,1::2]
    accum += cr[1::2,1::2]
    accum += cr[1::2,0::2]
    accum = accum >> 2 # divide by four
    result = accum.astype(numpy.uint8)
    return result

def get_yuv420_from_rgb(rgb_image):
    import cv2
    ycbcr = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2YCR_CB)

    y =  ycbcr[:,:,0]
    cb = ycbcr[:,:,1]
    cr = ycbcr[:,:,2]

    h,w = rgb_image.shape[:2]
    nh = h*3//2
    w2 = w//2
    f2 = numpy.empty( (nh,w), dtype=numpy.uint8)
    f2[:h, :] = y
    red_start = w*h
    red_q = quarter(cr)
    blue_q = quarter(cb)
    q = red_q.shape[0]*red_q.shape[1]
    f2.flat[red_start:red_start+q] = red_q
    f2.flat[red_start+q:] = blue_q
    buf = f2.tostring()
    return buf

def encode_plane( frame, color=1, format=None ):
    if format in ['mono8','raw8']:
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
    else:
        if format in ('mono8:bggr','mono8:gbrg', 'mono8:grbg',
                      'raw8:bggr','raw8:gbrg', 'raw8:grbg'):
            pattern = format.split(':')[1]
            if color==0:
                if pattern == 'bggr':
                    frame2 = frame[1::2,0::2] # take even rows, odd columns
                elif pattern in ('gbrg','grbg'):
                    frame2 = frame[0::2,0::2] # take odd rows, odd columns
                buf = frame2.tostring()
            else:
                import cv2
                if pattern=='bggr':
                    code = cv2.COLOR_BAYER_BG2RGB
                elif pattern=='gbrg':
                    code = cv2.COLOR_BAYER_GB2RGB
                else:
                    assert pattern=='grbg'
                    code = cv2.COLOR_BAYER_GR2RGB
                rgb_image = cv2.cvtColor(frame,code)
                buf = get_yuv420_from_rgb(rgb_image)
        elif format=='rgb8' and color==1:
            newshape = frame.shape[0], frame.shape[1]//3, 3
            newframe = numpy.empty( newshape, dtype=numpy.uint8)
            newframe.flat = frame.flat
            buf = get_yuv420_from_rgb(newframe)
        else:
            raise NotImplementedError('format=%r, color=%d not supported.'%(
                format,color))
    return buf

def doit( filename,
          raten=25, # numerator
          rated=1,  # denom
          aspectn = 0, # numerator
          aspectd = 0, # denom
          use_nth_frame = 1, # nth frame to skip
          rotate_180 = False,
          autocrop = 1,
          color = 1,
          raw = False,
          non_blocking = False,
          format = None,
          clip_one_pixel = False,
          ):
    fmf = FMF.FlyMovie(filename)
    if format is None:
        format = fmf.get_format()
    format = format.lower()
    width = fmf.get_width()
    if clip_one_pixel:
        width -= 1
    height = fmf.get_height()

    if autocrop==0:
        buffer_width = width
        buffer_height = height
    else:
        if autocrop==1:
            buffer_width  = (width >> 1) << 1
            buffer_height = height
        elif autocrop==2:
            buffer_width  = (width >> 4) << 4
            buffer_height  = (height >> 4) << 4
        else:
            raise ValueError('Unknown autocrop value: %s'%autocrop)
        if buffer_width!=width or buffer_height!=height:
            print >> sys.stderr, 'fmfcat autocropping from (%d,%d) to (%d,%d)'%(
                width,height, buffer_width,buffer_height)
    if format=='rgb8':
        buffer_width*=3

    final_width, final_height = check_format_and_color(buffer_width, buffer_height,
                                                       format=format, color=color)

    if raw:
        print >> sys.stderr, 'raw image width=%d height=%d' %(final_width,final_height)

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
        out_fd.write('%(Y4M_MAGIC)s W%(final_width)d H%(final_height)d '
                     'F%(raten)d:%(rated)d %(inter)s A%(aspectn)d:%(aspectd)d '
                     '%(colorspace)s Xconverted-by-fmfcat\n'%locals())

    n_frames_done = 0
    while 1:
        try:
            frame,timestamp = fmf.get_next_frame()
        except FMF.NoMoreFramesException, err:
            break
        if clip_one_pixel:
            frame = frame[:,1:]

        if n_frames_done % use_nth_frame != 0:
            n_frames_done +=1
            continue
        n_frames_done +=1

        if not raw:
            out_fd.write('%(Y4M_FRAME_MAGIC)s\n'%locals())

        if rotate_180:
            frame = numpy.rot90(numpy.rot90(frame))

        if autocrop > 0:
            frame = frame[:buffer_height,:buffer_width]

        buf = encode_plane( frame, color=color, format=format )
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
                      help='set color output mode (0:mono, 1:YCbCr 420)')

    parser.add_option('--format', default=None, type=str,
                      help='force the input format (e.g. "mono8:bggr")')

    parser.add_option('--raten', default=25, type=int,
                      help='numerator of fps (frame rate)')
    parser.add_option('--rated', default=1, type=int,
                      help='denominator of fps (frame rate)')

    parser.add_option('--use-nth-frame', default=1, type=int,
                      help='emit only Nth frame')

    parser.add_option('--aspectn', default=0, type=int,
                      help='numerator of aspect ratio')
    parser.add_option('--aspectd', default=0, type=int,
                      help='denominator of aspect ratio')

    parser.add_option('--raw', action='store_true',
                      default=False,
                      help='do not include any YUV4MPEG2 headers, just output raw frame data' )

    parser.add_option('--off_by_one', action='store_true',
                      default=False, dest='clip_one_pixel',
                      help='clip leftmost pixels (for off-by-one errors with Bayer pattern)')

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
          format = options.format,
          clip_one_pixel = options.clip_one_pixel,
          use_nth_frame = options.use_nth_frame,
          )

if __name__=='__main__':
    main()
