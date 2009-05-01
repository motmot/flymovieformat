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
