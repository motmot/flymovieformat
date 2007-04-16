from distutils.core import setup
import py2exe

import sys, os, glob
opj = os.path.join

mpl_data_dir = opj( sys.prefix, 'share', 'matplotlib' )

setup(windows=['scripts/playfmf.py'],
      data_files=[('',['scripts/playfmf.xrc']),
                  ('',['scripts/matplotlibrc']),
                  ('matplotlibdata',glob.glob(opj(mpl_data_dir,'*.xpm'))),
                  ]
      )
