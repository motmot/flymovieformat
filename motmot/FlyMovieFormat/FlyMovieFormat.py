# -*- coding: utf-8 -*-
"""
This module contains code to read and write FlyMovieFormat
files, which end with extension .fmf.

Users may like to use these classes:

 - :class:`~motmot.FlyMovieFormat.FlyMovieFormat.FlyMovie` : read .fmf files
 - :class:`~motmot.FlyMovieFormat.FlyMovieFormat.FlyMovieSaver` : write .fmf files

The following Exception types may sometimes be raised:

 - :class:`~motmot.FlyMovieFormat.FlyMovieFormat.NoMoreFramesException` :
 - :class:`~motmot.FlyMovieFormat.FlyMovieFormat.InvalidMovieFileException` :

Reading an .fmf from Python
===========================

In Python accessing frames from an .fmf files is as easy as::

  import motmot.FlyMovieFormat.FlyMovieFormat as FMF
  import sys

  fname = sys.argv[1]
  fmf = FMF.FlyMovie(fname)
  for frame_number in range(10):
      frame,timestamp = fmf.get_frame(frame_number)

Writing an .fmf in Python
=========================

Writing frames to an .fmf file is also easy::

  import motmot.FlyMovieFormat.FlyMovieFormat as FMF
  import sys
  import numpy as np

  fname = sys.argv[1]
  fmf_saver = FMF.FlyMovieSaver(fname)

  width, height = 640,480
  for i in range(10):
      fake_image = np.zeros( (height,width), dtype=np.uint8)
      fake_timestamp = 0.0
      fmf_saver.add_frame(fake_image,fake_timestamp)

  fmf_saver.close()

Module documentation
====================

"""
from __future__ import division
import sys
import struct
import warnings
import os.path

import numpy
from numpy import nan

import time

import math

# version 1 formats:
VERSION_FMT = '<I'
FORMAT_LEN_FMT = '<I'
BITS_PER_PIXEL_FMT = '<I'
FRAMESIZE_FMT = '<II'
CHUNKSIZE_FMT = '<Q'
N_FRAME_FMT = '<Q'
TIMESTAMP_FMT = 'd' # XXX struct.pack('<d',nan) dies

# additional version 2 formats:
CHUNK_N_FRAME_FMT = '<Q'
CHUNK_TIMESTAMP_FMT = 'd' # XXX struct.pack('<d',nan) dies
CHUNK_DATASIZE_FMT = '<Q'

format2bpp = { # convert format to bits per pixel
    'RAW8':8,
    'RAW16':16,
    'RAW32f':32,
    'MONO8':8,
    'MONO16':16,
    'MONO32f':32,
    'RGB8':24,
    'ARGB8':32,
    'YUV411':12,
    'YUV422':16,
    'RGB32f':32*3,
    }

def format2bpp_func(format):
    result = format2bpp.get(format,None)
    if result is None:
        if format.startswith('MONO8:'):
            result=8
        elif format.startswith('MONO32f:'):
            result=32
        else:
            raise ValueError('unknown format: %s'%format)
    return result

class NoMoreFramesException( Exception ):
    """A frame was requested, but no more frames exist"""
    pass

class InvalidMovieFileException( Exception ):
    """The file is not a valid movie file"""
    pass

class FlyMovie:
    """.fmf file reader

    - *file* : string or file object to open

    Optional keyword arguments:

    - *check_integrity* :  whether to scan the last frame(s) for completeness

    """
    def __init__(self,file,check_integrity=False):

        if isinstance(file,basestring):
            self.filename = file
            try:
                self.file = open(self.filename,mode="r+b")
            except IOError:
                self.file = open(self.filename,mode="r")
                self.writeable = False
            else:
                self.writeable = True
            self.opened_file = True
        else:
            self.file = file
            self.opened_file = False
            self.writeable = False
            self.filename = None

        r=self.file.read # shorthand
        size=struct.calcsize
        unpack=struct.unpack

        version_buf = r(size(VERSION_FMT))
        if len(version_buf)!=size(VERSION_FMT):
            raise InvalidMovieFileException("could not read data file")

        version, = unpack(VERSION_FMT,version_buf)
        if version not in (1,3):
            raise NotImplementedError('Can only read version 1 and 3 files')

        if version  == 1:
            self.format = 'MONO8'
            self.bits_per_pixel = 8
        elif version == 3:
            format_len = unpack(FORMAT_LEN_FMT,r(size(FORMAT_LEN_FMT)))[0]
            self.format = r(format_len)
            self.bits_per_pixel = unpack(BITS_PER_PIXEL_FMT,r(size(BITS_PER_PIXEL_FMT)))[0]

        try:
            self.framesize = unpack(FRAMESIZE_FMT,r(size(FRAMESIZE_FMT)))
        except struct.error:
            raise InvalidMovieFileException('file could not be read')

        self.bytes_per_chunk, = unpack(CHUNKSIZE_FMT,r(size(CHUNKSIZE_FMT)))
        self.n_frames, = unpack(N_FRAME_FMT,r(size(N_FRAME_FMT)))
        self.timestamp_len = size(TIMESTAMP_FMT)
        self.chunk_start = self.file.tell()
        self.next_frame = None

	if self.n_frames == 0: # unknown movie length, read to find out
            self.n_frames = self.compute_n_frames_from_file_size()

        if check_integrity:
            n_frames_ok = False
            while not n_frames_ok:
                try:
                    self.get_frame(-1)
                    n_frames_ok = True
                except NoMoreFramesException:
                    self.n_frames -= 1
                    if self.n_frames == 0:
                        break
	    self.file.seek(self.chunk_start) # go back to beginning

        self._all_timestamps = None # cache

    def compute_n_frames_from_file_size(self,only_full_frames=False):
        eb = os.fstat(self.file.fileno()).st_size
        if only_full_frames:
            round = math.floor
        else:
            round = math.ceil
        n_frames = int(round((eb-self.chunk_start)/self.bytes_per_chunk))
        return n_frames

    def close(self):
        if self.opened_file:
            self.file.close()
        self.writeable = False
        self.n_frames = None
        self.next_frame = None

    def get_width(self):
        """returns width of data, in bytes

        Returns:
        - *width* : integer, width of image, in bytes

        Note, to get the width of underlying image, do this::

          image_width = fmf.get_width()//(fmf.get_bits_per_pixel()//8)

        """
        return self.framesize[1]

    def get_height(self):
        """returns height of data, in pixels

        Returns:
        - *height* : integer, height of image, in pixels
        """
        return self.framesize[0]

    def get_n_frames(self):
        """get the number of frames

        Returns:
        - *n_frames* : integer, number of frames
        """
        return self.n_frames

    def get_format(self):
        return self.format

    def get_bits_per_pixel(self):
        """get the number of bits per pixel

        Returns:
        - *bits_per_pixel* : integer, number of bits per pixel (e.g. 8)
        """
        return self.bits_per_pixel

    def _read_next_frame(self,allow_partial_frames=False):
        data = self.file.read( self.bytes_per_chunk )
        if data == '':
            raise NoMoreFramesException('EOF')
        if len(data)<self.bytes_per_chunk:
            if allow_partial_frames:
                missing_bytes = self.bytes_per_chunk-len(data)
                data = data + '\x00'*missing_bytes
                warnings.warn('appended %d bytes (to a total of %d), image will be corrupt'%(missing_bytes,self.bytes_per_chunk))
            else:
                raise NoMoreFramesException('short frame '\
                                            '(%d bytes instead of %d)'%(
                    len(data),self.bytes_per_chunk))
        timestamp_buf = data[:self.timestamp_len]
        timestamp, = struct.unpack(TIMESTAMP_FMT,timestamp_buf)

        if self.format in ('MONO8','RAW8') or self.format.startswith('MONO8:'):
            frame = numpy.fromstring(data[self.timestamp_len:],numpy.uint8)
            frame.shape = self.framesize
        elif self.format in ('YUV422'):
            frame = numpy.fromstring(data[self.timestamp_len:],numpy.uint16)
            frame.shape = self.framesize
        elif self.format in ('RGB8'):
            frame = numpy.fromstring(data[self.timestamp_len:],
                                     dtype=numpy.uint8)
            h,w = self.framesize
            frame.shape = (h,w*3)
        elif (self.format in ('MONO32f','RAW32f') or
              self.format.startswith('MONO32f:')):
            frame = numpy.fromstring(data[self.timestamp_len:],numpy.float32)
            frame.shape = self.framesize
        elif (self.format=='RGB32f'):
            frame = numpy.fromstring(data[self.timestamp_len:],numpy.float32)
            frame.shape = self.framesize[0], self.framesize[1], 3
        else:
            raise NotImplementedError("Reading not implemented for %s format"%(self.format,))
        return frame, timestamp

    def _read_next_timestamp(self):
        read_len = struct.calcsize(TIMESTAMP_FMT)
        timestamp_buf = self.file.read( read_len )
        self.file.seek( self.bytes_per_chunk-read_len, 1) # seek to next frame
        if timestamp_buf == '':
            raise NoMoreFramesException('EOF')
        timestamp, = struct.unpack(TIMESTAMP_FMT,timestamp_buf)
        return timestamp

    def is_another_frame_available(self):
        try:
            if self.next_frame is None:
                self.next_frame = self._read_next_frame()
        except NoMoreFramesException:
            return False
        return True

    def get_next_frame(self,allow_partial_frames=False):
        """return image data for frame number

        Returns:

        - *frame* : array of image data
        - *timestamp* : float, timestamp of image time
        """
        if self.next_frame is not None:
            frame, timestamp = self.next_frame
            self.next_frame = None
            return frame, timestamp
        else:
            frame, timestamp = self._read_next_frame(
                allow_partial_frames=allow_partial_frames)
            return frame, timestamp

    def get_frame(self,frame_number,allow_partial_frames=False):
        self.seek(frame_number)
        return self.get_next_frame(allow_partial_frames=allow_partial_frames)

    def get_all_timestamps(self):
        """return all timestamps in .fmf file

        Returns:
        - *all_timestamps* : array of timestamps
        """
        if self._all_timestamps is None:
            self.seek(0)
            read_len = struct.calcsize(TIMESTAMP_FMT)
            self._all_timestamps = []
            while 1:
                timestamp_buf = self.file.read( read_len )
                self.file.seek( self.bytes_per_chunk-read_len, 1) # seek to next frame
                if timestamp_buf == '':
                    break
                timestamp, = struct.unpack(TIMESTAMP_FMT,timestamp_buf)
                self._all_timestamps.append( timestamp )
            self.next_frame = None
            self._all_timestamps = numpy.asarray(self._all_timestamps)
        return self._all_timestamps

    def seek(self,frame_number):
        """go to frame number"""
        if frame_number < 0:
            frame_number = self.n_frames + frame_number
        if frame_number < 0:
            raise IndexError("negative index out of range (movie has no frames)")
        seek_to = self.chunk_start+self.bytes_per_chunk*frame_number
        self.file.seek(seek_to)
        self.next_frame = None

    def get_next_timestamp(self):
        if self.next_frame is not None:
            frame, timestamp = self.next_frame
            self.next_frame = None
            return timestamp
        else:
            timestamp = self._read_next_timestamp()
            return timestamp

    def get_frame_at_or_before_timestamp(self, timestamp):
        tss = self.get_all_timestamps()
        at_or_before_timestamp_cond = tss <= timestamp
        nz = numpy.nonzero(at_or_before_timestamp_cond)
        if len(nz)==0:
            raise ValueError("no frames at or before timestamp given")
        fno = nz[-1]
        return self.get_frame(fno)

def mmap_flymovie( *args, **kwargs ):
    """map .fmf file to RAM

    Note: make mmap does not currently work with RGB images.

    Note: to map a 4 GB or larger file to RAM, a 64 bit computer is
    required.
    """
    supported_formats = ['MONO8','RAW8']
    fmf = FlyMovie(*args,**kwargs)

    format = fmf.get_format()

    if fmf.bits_per_pixel == 8 and format in ['MONO8','RAW8']:
        dtype_str = '|u1'
    elif fmf.bits_per_pixel == 16 and format in ['MONO16','RAW16','YUV422']:
        dtype_str = '<u2'
    elif fmf.bits_per_pixel == 32 and format in ['MONO32f','RAW32f']:
        dtype_str = '<f4'
    else:
        raise ValueError("don't know how to encode dtype of your format")

    my_dtype = numpy.dtype([('timestamp', '<f8'),
                            ('frame', dtype_str, fmf.framesize)])
    assert my_dtype.itemsize == fmf.bytes_per_chunk

    offset = fmf.chunk_start
    shape = (fmf.get_n_frames(),)
    ra = numpy.memmap( fmf.filename, dtype=my_dtype, offset=offset,
                       mode='r', shape=shape)
    fmf.close()
    return ra

class FlyMovieSaver:
    """.fmf file writer

    - *file* : string or file object to open

    Keyword arguments:

    - *version* : 1 or 3, defaults to 1
    - *seek_ok* : boolean indicating whether calling seek() is OK on this file
    - *format* : format string (e.g. 'MONO8', required for version 3 only)
    - *bits_per_pixel* : number of bits per pixel. inferred from format if not supplied.

    """
    def __init__(self,
                 file,
                 version=1,
                 seek_ok=True,
                 format=None,
                 bits_per_pixel=None,
                 ):
        if isinstance(file,basestring):
            # filename
            self.filename=file

            # seek_ok
            if seek_ok:
                mode = "w+b"
            else:
                mode = "wb"
            self.seek_ok = seek_ok

            self.file = open(self.filename,mode=mode)
            self.opened_file = True
        else:
            self.seek_ok = True
            self.file = file
            self.opened_file = False
            self.filename=None

        self.file.write(struct.pack(VERSION_FMT,version))

        if version == 3:
            if not isinstance(format,str):
                raise ValueError("format must be string (e.g. 'MONO8', 'YUV422')")
            if bits_per_pixel is None:
                bits_per_pixel = format2bpp_func(format)
            if not isinstance(bits_per_pixel,int):
                raise ValueError("bits_per_pixel must be integer")
            format_len = len(format)
            self.file.write(struct.pack(FORMAT_LEN_FMT,format_len))
            self.file.write(format)
            self.file.write(struct.pack(BITS_PER_PIXEL_FMT,bits_per_pixel))
        else:
            if format is None: format = 'MONO8'
            if bits_per_pixel is None: bits_per_pixel = 8
            if format != 'MONO8' or bits_per_pixel != 8:
                raise ValueError("version 1 fmf files only support MONO8 8bpp images")
        self.format = format
        self.bits_per_pixel = bits_per_pixel

        self.framesize = None

        self.n_frames = 0
        self.n_frame_pos = None

    def add_frame(self,origframe,timestamp=nan,error_if_not_fast=False):
        """save a single image frame to the file

        - *origframe* : array of image data

        Optional keyword arguments:

        - *timestamp* : double precision floating point timestamp (default: nan)
        - *error_if_not_fast* : boolean: raise error if no origframe.dump_to_file()

        """
        TIMESTAMP_FMT = 'd' # XXX struct.pack('<d',nan) dies
        frame = numpy.asarray(origframe)
        thisshape = frame.shape

        if self.format=='RGB8' and frame.ndim==2:
            # image in raw encoded shape
            thisshape = (frame.shape[0], frame.shape[1]//3)

        if self.framesize is None:
            self._do_v1_header(frame)
        else:
            if self.framesize != thisshape:
                raise ValueError('frame shape is now %s, but it used to be %s'%(str(thisshape),str(self.framesize)))

        b1 = struct.pack(TIMESTAMP_FMT,timestamp)
        self.file.write(b1)
        if hasattr(origframe,'dump_to_file'):
            nbytes = origframe.dump_to_file( self.file )
            assert nbytes == self._bytes_per_image
        else:
            if error_if_not_fast:
                origframe.dump_to_file # trigger AttributeError
            if not hasattr(self,'gave_dump_fd_warning'):
                #warnings.warn('could save faster if %s implemented dump_to_file()'%(str(type(origframe)),))
                self.gave_dump_fd_warning = True
            b2 = frame.tostring()
            if len(b2) != self._bytes_per_image:
                raise ValueError("expected buffer of length %d, got length %d (shape %s)"%(self._bytes_per_image,len(b2),str(thisshape)))
            self.file.write(b2)
        self.n_frames += 1

    def add_frames(self, frames, timestamps=None):
        """add multiple image frames

        - *frames* : arrays of image data

        Optional keyword arguments:

        - *timestamps* : double precision floating point timestamps

        """
        if 0:
            for frame, timestamp in zip(frames,timestamps):
                self.add_frame(frame,timestamp)
        else:
            if timestamps is None:
                timestamps = [nan]*len(frames)
            TIMESTAMP_FMT = 'd' # XXX struct.pack('<d',nan) dies
            if self.framesize is None:
                self._do_v1_header(frames[0])
            else:
                assert self.framesize == frames[0].shape
            mega_buffer = ''
            for frame, timestamp in zip(frames,timestamps):
                b1 = struct.pack(TIMESTAMP_FMT,timestamp)
                mega_buffer += b1
                b2 = frame.tostring()
                assert len(b2) == self._bytes_per_image
                mega_buffer += b2
            self.file.write(mega_buffer)
            self.n_frames += len(frames)

    def _do_v1_header(self,frame):
        # first frame

        # frame data are always type uint8, so frame shape (width) varies if data format not MONO8
        self.framesize = frame.shape
        if self.format=='RGB8' and frame.ndim==2:
            # image in raw encoded shape
            self.framesize = (frame.shape[0], frame.shape[1]//3)

        buf = struct.pack(FRAMESIZE_FMT,
                          self.framesize[0],self.framesize[1])
        self.file.write(buf)

        bits_per_image = self.framesize[0] * self.framesize[1] * self.bits_per_pixel
        if bits_per_image % 8 != 0:
            raise ValueError('combination of frame size and bits_per_pixel make non-byte aligned image')
        self._bytes_per_image = bits_per_image / 8
        bytes_per_chunk = self._bytes_per_image + struct.calcsize(TIMESTAMP_FMT)

        buf = struct.pack(CHUNKSIZE_FMT,bytes_per_chunk)
        self.file.write(buf)

        self.n_frame_pos = self.file.tell()

        buf = struct.pack(N_FRAME_FMT,self.n_frames) # will fill in later
        self.file.write(buf)

        ####### end of header ###########################

    def close(self):
        """finish writing the file"""
        if not hasattr(self,'file'):
            # hmm, we've already been closed
            #warnings.warn("attempting to close multiple times")
            return

        if self.n_frames == 0:
            #warnings.warn('no frames in FlyMovie')
            # no frames added
            if self.opened_file:
                # We opened it, we can close it.
                self.file.close()
            del self.file
            return

        if self.seek_ok:
            self.file.seek( self.n_frame_pos )
            buf = struct.pack(N_FRAME_FMT,self.n_frames) # will fill in later
            self.file.write(buf)
        if self.opened_file:
            # We opened it, we can close it.
            self.file.close()
        del self.file # make sure we can't access self.file again

    def __del__(self):
        if hasattr(self,'file'):
            self.close()
