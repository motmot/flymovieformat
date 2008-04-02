import unittest
import FlyMovieFormat
import pkg_resources # requires setuptools
import numpy
import tempfile

fmf_filenames = [pkg_resources.resource_filename(__name__,x) for x in ['test_mono8.fmf',
                                                                       'test_raw8.fmf',
                                                                       'test_yuv422.fmf',
                                                                       'test_mono32f.fmf',
                                                                       ]]

class TestFMF(unittest.TestCase):

    def test_formats(self):
        for filename in fmf_filenames:
            fmf = FlyMovieFormat.FlyMovie(filename)
            frame, timestamp = fmf.get_next_frame()

    def test_roundtrip(self):
        for filename in fmf_filenames:

            for version in [3]:
                # write a new movie
                fmf_in = FlyMovieFormat.FlyMovie(filename)
                tmpfile = tempfile.TemporaryFile()
                fmf_out = FlyMovieFormat.FlyMovieSaver(tmpfile,
                                                       version=version,
                                                       format=fmf_in.get_format(),
                                                       bits_per_pixel=fmf_in.get_bits_per_pixel(),
                                                       )
                for i in range(fmf_in.get_n_frames()):
                    frame, timestamp = fmf_in.get_next_frame()
                    fmf_out.add_frame( frame, timestamp )
                fmf_in.close()
                fmf_out.close()

                tmpfile.seek(0)

                # now read our new movie and compare it
                fmf_in = FlyMovieFormat.FlyMovie(filename)
                fmf_out = FlyMovieFormat.FlyMovie(tmpfile)
                assert fmf_in.get_n_frames() == fmf_out.get_n_frames()
                for i in range(fmf_in.get_n_frames()):
                    frame_in, timestamp_in = fmf_in.get_next_frame()
                    frame_out, timestamp_out = fmf_out.get_next_frame()
                    assert timestamp_in == timestamp_out
                    assert frame_in.shape == frame_out.shape
                    assert numpy.allclose(frame_in,frame_out)
                fmf_in.close()
                fmf_out.close()
                tmpfile.close()

    def test_random_vs_sequential_reads(self):
        fmf = FlyMovieFormat.FlyMovie(
            pkg_resources.resource_filename(__name__,'test_mono8.fmf'))
        N = fmf.get_n_frames()
        frames = []
        timestamps = []
        for i in range(N):
            # test sequential access
            frame, timestamp = fmf.get_next_frame()
            frames.append(frame)
            timestamps.append( timestamp )
        for i in range(N-1,-1,-1):
            # test random access
            frame, timestamp = fmf.get_frame(i)

            # check vs. sequential access
            assert numpy.allclose(frame,frames[i])
            assert timestamp == timestamps[i]

    def test_mmap(self):
        for filename in fmf_filenames:
            fmf = FlyMovieFormat.FlyMovie( filename )
            ra = FlyMovieFormat.mmap_flymovie( filename )
            n_frames = len(ra)
            assert n_frames == fmf.get_n_frames()

            for i in range(n_frames):
                frame, timestamp = fmf.get_next_frame()
                mmap_frame = ra['frame'][i]
                assert mmap_frame.shape == frame.shape
                assert numpy.allclose( mmap_frame, frame )
                assert timestamp == ra['timestamp'][i]
            fmf.close()

def get_test_suite():
    ts=unittest.TestSuite([unittest.makeSuite(TestFMF),
                           ])
    return ts

if __name__=='__main__':
    if 1:
        ts = get_test_suite()
        ts.debug()
    else:
        unittest.main()
