import FlyMovieFormat
import sys
import os
import pylab
import numpy

def main():
    try:
        filename = sys.argv[1]
    except:
        print 'Usage: fmf_plottimestamps fmf_filename'
        sys.exit()


    path,ext = os.path.splitext(filename)
    if ext != '.fmf':
        print 'fmf_filename does not end in .fmf'
        sys.exit()

    fly_movie = FlyMovieFormat.FlyMovie(filename)
    n_frames = fly_movie.get_n_frames()

    ts = numpy.asarray(fly_movie.get_all_timestamps())
    if 0:
        pylab.figure()
        pylab.plot(ts)
        pylab.ylabel('timestamp (sec)')
        pylab.xlabel('frame number')
    
    pylab.figure()
    pylab.plot(ts-ts[0])
    pylab.ylabel('relative timestamp (sec)')
    pylab.xlabel('frame number')
    
    pylab.figure()
    ydiff_msec = (ts[1:]-ts[:-1])*1000.0
    max_ydiff = ydiff_msec.max()
    pylab.plot(ydiff_msec)
    pylab.setp(pylab.gca(),'ylim',[0,max_ydiff])
    pylab.ylabel('IFI (msec)')
    pylab.xlabel('frame number')
    pylab.show()
    
if __name__=='__main__':
    main()
