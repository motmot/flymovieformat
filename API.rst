************************************************************************
:mod:`motmot.FlyMovieFormat` - simple, uncompressed movie storage format
************************************************************************

.. module:: motmot.FlyMovieFormat
  :synopsis: simple, uncompressed movie storage format
.. index::
  module: motmot.FlyMovieFormat
  single: motmot.FlyMovieFormat
  single: FlyMovieFormat

This package contains code to read, write and view FlyMovieFormat
files, which end with extension .fmf.

The primary design goals of FlyMovieFormat were:

* Single pass, low CPU overhead writing of lossless movies for
  realtime streaming applications
* Precise timestamping for correlation with other activities
* Simple format that can be read from Python, C, and MATLAB®.

These goals are acheived via using a very simple format. After an
initial header containing meta-data such as image size and color
coding scheme (e.g. monochromatic 8 bits per pixel, YUV422, etc.),
repeated chunks of raw image data and timestamp are saved. Because the
raw image data from the native camera driver is saved, no additional
processing is performed. Thus, streaming of movies from camera to disk
will keep the CPU free for other tasks, but it will require a lot of
disk space. Furthermore, the disk bandwidth required is equivalent to
the camera bandwidth (unless you save only a region of the images, or
if you only save a fraction of the incoming frames).

Reading an .fmf from Python
===========================

In Python accessing frames from an .fmf files is as easy as::

  import motmot.FlyMovieFormat.FlyMovieFormat as FMF
  import sys

  fname = sys.argv[1]
  fmf = FMF.FlyMovie(fname)
  for frame_number in range(10):
      frame,timestamp = fmf.get_frame(frame_number)

More information
================

.. toctree::
  :maxdepth: 1

  fmf-format-spec.rst
