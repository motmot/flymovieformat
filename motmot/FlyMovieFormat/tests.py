import unittest
import FlyMovieFormat
import pkg_resources # requires setuptools
import numpy

fmf_filenames = [pkg_resources.resource_filename(__name__,x) for x in ['test_mono8.fmf',
                                                                       'test_raw8.fmf',
                                                                       ]]

class TestFMF(unittest.TestCase):

    def test_formats(self):
        for filename in fmf_filenames:
            fmf = FlyMovieFormat.FlyMovie(filename)
            frame, timestamp = fmf.get_next_frame()

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
    unittest.main()
