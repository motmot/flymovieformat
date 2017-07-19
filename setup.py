from setuptools import setup
import os

setup(name='motmot.FlyMovieFormat',
      description='support for .fmf (fly movie format) files',
      long_description = """'Fly movie format' (or .fmf) files are a
simple, uncompressed video format for storing data from digital video
cameras. A fixed-size per frame means that random access is extremely
fast, and a variety of formats (e.g. MONO8, YUV422) are supported.

This is a subpackage of the motmot family of digital image utilities.
""",
      version='1.7',
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      license='BSD',
      url='http://code.astraw.com/projects/motmot/fly-movie-format.html',
      namespace_packages = ['motmot'],
      packages = ['motmot','motmot.FlyMovieFormat'],
      package_data = {'motmot.FlyMovieFormat':['playfmf.xrc',
                                               'matplotlibrc',
                                               'test_raw8.fmf',
                                               'test_rgb8.fmf',
                                               'test_rgb32f.fmf',
                                               'test_mono8.fmf',
                                               'test_mono32f.fmf',
                                               'test_yuv422.fmf',
                                               'description.txt']},
      scripts = ['scripts/pvn2fmf'],
      entry_points = {
    'console_scripts': ['fmf2bmps = motmot.FlyMovieFormat.fmf2bmps:main',
                        'fmf_from_images = motmot.FlyMovieFormat.images2fmf:main',
                        'fmf_collapse = motmot.FlyMovieFormat.fmf_collapse:main',
                        'fmf_info = motmot.FlyMovieFormat.fmf_info:main',
                        'fmfcat = motmot.FlyMovieFormat.fmfcat:main',
                        'ffmpeg2fmf = motmot.FlyMovieFormat.ffmpeg2fmf:main',
                        ],
    'gui_scripts': ['playfmf = motmot.FlyMovieFormat.playfmf:main',
                    'fmf_plottimestamps = motmot.FlyMovieFormat.fmf_plottimestamps:main',
                    'fmf_tail = motmot.FlyMovieFormat.fmf_tail:main',
                    ],
    'motmot.FlyMovieFormat.exporter_plugins':['txt = motmot.FlyMovieFormat.saver_plugins:TxtFileSaverPlugin',
                                              'fmf = motmot.FlyMovieFormat.saver_plugins:FmfFileSaverPlugin',
                                              'image_sequence = motmot.FlyMovieFormat.saver_plugins:ImageSequenceSaverPlugin',
                                       ],
    },
      )
