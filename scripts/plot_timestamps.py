#!/usr/bin/env python

import motmot.FlyMovieFormat.FlyMovieFormat as FlyMovieFormat
from pylab import *
import sys
import numarray

filename = sys.argv[1]
fly_movie = FlyMovieFormat.FlyMovie(filename)
n_frames = fly_movie.get_n_frames()
timestamps = numarray.zeros((n_frames,),type=numarray.Float64)
for i in xrange(n_frames):
    timestamps[i]=fly_movie.get_next_timestamp()
diff = (timestamps[1:]-timestamps[:-1])*1000.0
zero_offset_msec = (timestamps[:-1]-timestamps[0])
plot(zero_offset_msec,diff)
set(gca(),'ylabel','Inter frame interval (msec)')
set(gca(),'xlabel','Acquisition time (sec)')
show()
