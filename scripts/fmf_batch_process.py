#!/usr/bin/env python
import glob
import motmot.FlyMovieFormat.FlyMovieFormat as FlyMovieFormat

# change this to current filenames
input_filenames = glob.glob('/home/jbender/data/081704_a*.fmf')

for input_filename in input_filenames:
    output_filename = input_filename + '.aoi'

    input_fmf = FlyMovieFormat.FlyMovie(input_filename)
    in_width = input_fmf.get_width()
    in_height = input_fmf.get_height()

    # change these to current aoi
    xmin,ymin=280,260
    width,height=100,100

    xmax=xmin+width
    ymax=ymin+height

    fmin=0
    fmax=input_fmf.get_n_frames()
    finterval=1
    frame_numbers=range(fmin,fmax,finterval)
    n_output_frames=len(frame_numbers)

    output_fmf = FlyMovieFormat.FlyMovieSaver(output_filename,version=1)

    print '%(input_filename)s (%(in_width)dx%(in_height)d, '\
          '%(fmax)d frames) ->'%locals()

    print '    %(output_filename)s (%(width)dx%(height)d, '\
          '%(n_output_frames)d frames) :          '%locals(),

    for i in range(fmin,fmax,finterval):
        frame,timestamp=input_fmf.get_next_frame()
        output_fmf.add_frame(frame[ymin:ymax,xmin:xmax],timestamp)
	j = i + 1
        print '\b\b\b\b\b\b\b\b\b\b%(j)4d/%(fmax)4d'%locals(),
    output_fmf.close()
    print
