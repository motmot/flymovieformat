import FlyMovieFormat
import Image
import numpy as np
import argparse

mode2format = {'L':'MONO8',
               'RGB':'RGB8',
              }

def images2fmf( input_filenames, out_fname, version=3 ):
    """convert a series of images into an .fmf file

    arguments
    ---------

    input_filenames: a list of strings of filenames ['filename1.png','filename2.png']
    out_fname: an output filename for the resulting .fmf movie
    version: a version specifier for the output .fmf

    notes
    -----

    The input images must be have the same width, height and mode. The
    order in which they are specified is the order saved into the new
    .fmf movie. Timestamps are generated from framenumbers starting
    from zero.

    """
    im_size = None
    im_mode = None
    fmf_out = None

    for timestamp,in_fname in enumerate(input_filenames):
        im = Image.open(in_fname)
        if im_size is None:
            im_size = im.size
            im_mode = im.mode
        else:
            assert im_size == im.size
            assert im_mode == im.mode
        buf = im.tostring()

        if fmf_out is None:
            fmf_out = FlyMovieFormat.FlyMovieSaver(out_fname,
                                                   version=version,
                                                   format=mode2format[im_mode],
                                                   )

        if im.mode=='L':
            data = np.fromstring( buf, dtype=np.uint8 )
            data.shape = (im.size[1], im.size[0])
        elif im.mode=='RGB':
            data = np.fromstring( buf, dtype=np.uint8 )
            data.shape = (im.size[1], im.size[0],3)
        else:
            raise NotImplementedError('no support for mode %r'%im.mode)

        fmf_out.add_frame( data, timestamp )

    fmf_out.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_fmf_name', type=str, help='filename of output .fmf')
    parser.add_argument('input_images', nargs='+', help='input filenames')

    args = parser.parse_args()
    images2fmf( args.input_images, args.output_fmf_name )

if __name__=='__main__':
    main()
