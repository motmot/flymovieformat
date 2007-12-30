#!/usr/bin/env python
import motmot.FlyMovieFormat.FlyMovieFormat as FlyMovieFormat

input_filename = '20050304_1834.fmf'
output_filename = 'blah_converted.fmf'
start_frame = 20
stop_frame = 2000

input_fmf = FlyMovieFormat.FlyMovie(input_filename)

fmax=input_fmf.get_n_frames()
assert start_frame <= fmax
assert stop_frame <= fmax
frame_numbers=range(start_frame,stop_frame+1)
n_output_frames=len(frame_numbers)

output_fmf = FlyMovieFormat.FlyMovieSaver(output_filename)
print '%(input_filename)s (%(fmax)d frames) ->'%locals()
print '    %(output_filename)s (%(n_output_frames)d frames) :          '%locals(),

for i in frame_numbers:
    frame,timestamp=input_fmf.get_frame(i)
    output_fmf.add_frame(frame,timestamp)
    j = i + 1
    print '\b\b\b\b\b\b\b\b\b\b%(j)4d/%(fmax)4d'%locals(),
output_fmf.close()
print
