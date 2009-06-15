************************************************************************
:mod:`motmot.FlyMovieFormat` - simple, uncompressed movie storage format
************************************************************************

.. module:: motmot.FlyMovieFormat
  :synopsis: simple, uncompressed movie storage format
.. index::
  module: motmot.FlyMovieFormat
  single: motmot.FlyMovieFormat
  single: FlyMovieFormat

.. toctree::
  :maxdepth: 1

  fmf-format-spec.rst

Converting files to .fmf
========================

The command :command:`ffmpeg2fmf` will use avbin (part of `Pyglet`_)
to read a variety of movie formats and save them as .fmf files. Use it
like so::

  ffmpeg2fmf --format=mono8 /path/to/my/movie.mp4
  # or
  ffmpeg2fmf --format=mono8 /path/to/my/movie.avi

This will save a file `/path/to/my/movie.fmf`.

.. _Pyglet: http://pyglet.org

:mod:`motmot.FlyMovieFormat.FlyMovieFormat`
===========================================

.. automodule:: motmot.FlyMovieFormat.FlyMovieFormat
   :members:
   :show-inheritance:

