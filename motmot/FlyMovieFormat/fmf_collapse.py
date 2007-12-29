from __future__ import division
import os, sys
import FlyMovieFormat
import Image
import numpy

def main():
    try:
        filename1 = sys.argv[1]
        filename2 = sys.argv[2]
    except:
        print """Usage: fmf_collapse fmf_filename1 fmf_filename2

This program takes a set of .fmf files and saves the mean of all
frames from all files as a .bmp image file.

The files used are in the range fmf_filename1 <= FILE <= fmf_filename2.

"""
        sys.exit()

    path,ext = os.path.splitext(filename1)
    if ext != '.fmf':
        print 'fmf_filename1 does not end in .fmf'
        sys.exit()

    path,ext = os.path.splitext(filename2)
    if ext != '.fmf':
        print 'fmf_filename2 does not end in .fmf'
        sys.exit()

    path1 = os.path.split(os.path.abspath(filename1))[0]
    path2 = os.path.split(os.path.abspath(filename2))[0]
    if path1 != path2:
        print 'path of fmf files not the same'
        sys.exit()

    path = path1
    allfiles = os.listdir(path)
    files = [file for file in allfiles if file >= filename1 and file<=filename2 and file.endswith('.fmf')]
    for imnum,filename in enumerate(files):
        try:
            fly_movie = FlyMovieFormat.FlyMovie(filename)
        except Exception,x:
            print 'while reading file',filename
            raise
        n_frames = fly_movie.get_n_frames()
        accum = None
        for i in range(n_frames):
            frame,timestamp = fly_movie.get_next_frame()
            #frame = frame[::-1,:] # flip for PIL
            #print frame.shape
            if accum is None:
                accum = frame.astype(numpy.float64)
            else:
                accum = accum + frame.astype(numpy.float64)
            #print accum.shape
            #print
        save_frame = accum/float(n_frames) # find mean image
        save_frame = save_frame.astype(numpy.uint8)
        save_frame = save_frame[::-1,:] # flip for PIL
        h,w=save_frame.shape
        im = Image.fromstring('L',(w,h),save_frame.tostring())
        f='cal%02d.bmp'%(imnum+1)
        print 'saving',f
        im.save(f)

if __name__=='__main__':
    main()
