import pkg_resources
import motmot.FlyMovieFormat.FlyMovieFormat as FMF
import sys, os
from pylab import prctile
import numpy as np

def doit(input_fname):
    output_fname = os.path.splitext(input_fname)[0]+'.highcontrast.fmf'
    in_fmf = FMF.FlyMovie(input_fname)
    out_fmf = FMF.FlyMovieSaver(output_fname,
                                version=3,
                                format=in_fmf.get_format(),
                                )
    try:
        # pass 1 - get 5,95 percentiles
        minvs = []
        maxvs = []
        n_samples = max(30,in_fmf.get_n_frames(),30)
        for fno in np.linspace(0,in_fmf.get_n_frames(),n_samples,endpoint=False):
            fno = int(round(fno))
            in_fmf.seek(fno)
            frame,timestamp = in_fmf.get_next_frame()
            minv,maxv=prctile(frame.ravel(),p=(5.0,95.0))
            minvs.append(minv)
            maxvs.append(maxv)
        minv = np.min(minvs)
        maxv = np.max(maxvs)
        orig_center = (minv+maxv)/2.0
        orig_range = maxv-minv

        new_center = 127.5
        new_range = 127.5

        # pass 2 - rescale and save
        in_fmf.seek(0)
        for fno in range(in_fmf.get_n_frames()):
            frame,timestamp = in_fmf.get_next_frame()
            frame = (frame.astype(np.float32)-orig_center)/orig_range
            frame = frame * new_range + new_center
            frame = np.clip(frame,0,255).astype(np.uint8)
            out_fmf.add_frame(frame,timestamp)
        out_fmf.close()
    except:
        os.unlink(output_fname)
        raise
    in_fmf.close()

def main():
    filename = sys.argv[1]
    doit(filename)

if __name__=='__main__':
    main()
