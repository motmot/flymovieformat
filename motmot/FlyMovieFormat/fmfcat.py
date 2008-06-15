from optparse import OptionParser
import sys
import motmot.FlyMovieFormat.FlyMovieFormat as FMF

if 1:
    import signal
    # http://mail.python.org/pipermail/python-list/2004-June/268512.html
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def doit( filename,
          raten=25, # numerator
          rated=1,  # denom
          aspectn = 1, # numerator
          aspectd = 1, # denom
          ):
    fmf = FMF.FlyMovie(filename)
    if fmf.get_format() not in ['MONO8','RAW8']:
        raise NotImplementedError('Only MONO8 and RAW8 formats are currently supported.')
    width = fmf.get_width()//(fmf.get_bits_per_pixel()//8)
    height = fmf.get_height()

    Y4M_MAGIC = 'YUV4MPEG2'
    Y4M_FRAME_MAGIC = 'FRAME'

    inter = 'Ip' # progressive
    colorspace = 'Cmono'

    out_fd = sys.stdout

    out_fd.write('%(Y4M_MAGIC)s W%(width)d H%(height)d F%(raten)d:%(rated)d %(inter)s A%(aspectn)d:%(aspectd)d %(colorspace)s\n'%locals())
    while 1:
        try:
            frame,timestamp = fmf.get_next_frame()
        except FMF.NoMoreFramesException, err:
            break
        out_fd.write('%(Y4M_FRAME_MAGIC)s\n'%locals())

        for i in range(height):
            out_fd.write(frame[i,:].tostring())
        out_fd.flush()

def main():
    usage = """%prog FILENAME [options]

Pipe the contents of an .fmf file to stdout in the yuv4mpegpipe
format. This allows an .fmf file to be converted to any format that
ffmpeg supports. For example, to convert the file x.fmf to x.avi using
the MPEG4 codec:

fmfcat x.fmf | ffmpeg -vcodec msmpeg4v2 -i - x.avi"""

    parser = OptionParser(usage)

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return

    filename = args[0]

    doit( filename = args[0],
          )

if __name__=='__main__':
    main()

