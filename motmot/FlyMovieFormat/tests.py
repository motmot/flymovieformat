import unittest
import FlyMovieFormat
import pkg_resources # requires setuptools
import numpy
import tempfile, os, shutil

fmf_filenames = [pkg_resources.resource_filename(__name__,x) for x in\
    ['test_mono8.fmf',
     'test_raw8.fmf',
     'test_yuv422.fmf',
     'test_mono32f.fmf',
     'test_rgb8.fmf',
     'test_rgb32f.fmf',
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
            if (filename.endswith('test_rgb8.fmf') or
                filename.endswith('test_rgb32f.fmf')):
                continue
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

class TestExporterPlugins(unittest.TestCase):
    def setUp(self):
        # load plugins
        PluginClasses = []
        pkg_env = pkg_resources.Environment()
        for name in pkg_env:
            egg = pkg_env[name][0]
            modules = []

            for name in egg.get_entry_map('motmot.FlyMovieFormat.exporter_plugins'):
                egg.activate()
                entry_point = egg.get_entry_info('motmot.FlyMovieFormat.exporter_plugins', name)
                PluginClass = entry_point.load()
                PluginClasses.append( PluginClass )
                modules.append(entry_point.module_name)
        self.plugins = [PluginClass() for PluginClass in PluginClasses]

    def test_plugins(self):
        bpp = FlyMovieFormat.format2bpp
        for filename in fmf_filenames:
            fmf = FlyMovieFormat.FlyMovie( filename )
            format = fmf.get_format()
            width_height = (fmf.get_width(),
                             fmf.get_height())
            for plugin in self.plugins:
                dlg = None
                origdir = os.path.abspath(os.curdir)
                tmpdir = tempfile.mkdtemp()
                os.chdir(tmpdir)
                try:
                    saver = plugin.get_saver(dlg,format,width_height)

                    for i in range(2):
                        orig_frame,timestamp = fmf.get_frame(i)
                        save_frame = orig_frame
                        saver.save( save_frame, timestamp )
                    saver.close()
                finally:
                    os.chdir(origdir)
                    shutil.rmtree(tmpdir)

def get_test_suite():
    ts=unittest.TestSuite([unittest.makeSuite(TestFMF),
                           unittest.makeSuite(TestExporterPlugins),
                           ])
    return ts

if __name__=='__main__':
    if 1:
        ts = get_test_suite()
        ts.debug()
    else:
        unittest.main()
