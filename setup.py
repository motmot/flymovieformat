from setuptools import setup, find_packages

kws=dict(
    )

setup(name='motmot.FlyMovieFormat',
      description='support for .fmf files (part of the motmot camera packages)',
      version='0.5.2',
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      license='BSD',
      url='http://code.astraw.com/projects/motmot',
      namespace_packages = ['motmot'],
      packages = find_packages(),
      package_data = {'motmot.FlyMovieFormat':['playfmf.xrc',
                                               'matplotlibrc',
                                               'test_raw8.fmf',
                                               'test_mono8.fmf',
                                               'description.txt']},
      entry_points = {
    'console_scripts': ['fmf2bmps = motmot.FlyMovieFormat.fmf2bmps:main',
                        'fmf_collapse = motmot.FlyMovieFormat.fmf_collapse:main',
                        'fmf_info = motmot.FlyMovieFormat.fmf_info:main',
                        ],
    'gui_scripts': ['playfmf = motmot.FlyMovieFormat.playfmf:main',
                    'fmf_plottimestamps = motmot.FlyMovieFormat.fmf_plottimestamps:main',
                    ],
    'motmot.FlyMovieFormat.exporter_plugins':['txt = motmot.FlyMovieFormat.playfmf:TxtFileSaverPlugin',
                                              'fmf = motmot.FlyMovieFormat.playfmf:FmfFileSaverPlugin',
                                              'image_sequence = motmot.FlyMovieFormat.playfmf:ImageSequenceSaverPlugin',
                                       ],
    },
      )
