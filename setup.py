import sys
from setuptools import setup
import distutils.command.sdist

if 1:
    kws=dict(
      extras_require = {
    'imops':      ['imops>=0.3.dev275'],
    },

      entry_points = {
    'console_scripts': [
    'fmf2bmps = FlyMovieFormat.fmf2bmps:main',
    'fmf_collapse = FlyMovieFormat.fmf_collapse:main',
    'fmf_info = FlyMovieFormat.fmf_info:main',
    ],
    'gui_scripts': [
    'playfmf = FlyMovieFormat.playfmf:main [imops]',
    'fmf_plottimestamps = FlyMovieFormat.fmf_plottimestamps:main',
    ],
    'FlyMovieFormat.exporter_plugins':[
        'txt = FlyMovieFormat.playfmf:TxtFileSaverPlugin',
        'fmf = FlyMovieFormat.playfmf:FmfFileSaverPlugin',
        'image_sequence = FlyMovieFormat.playfmf:ImageSequenceSaverPlugin',
        ],
    },
      )

setup(name='FlyMovieFormat',
      description='support for .fmf files (part of the motmot camera packages)',
      version='0.5.2',
      author='Andrew Straw',
      author_email='strawman@astraw.com',
      license='BSD',
      url='http://code.astraw.com/projects/motmot',
      packages = ['FlyMovieFormat'],
      package_data = {'FlyMovieFormat':['playfmf.xrc',
                                        'matplotlibrc',
                                        'test_mono8.fmf',
                                        'description.txt']},
      **kws
      )
