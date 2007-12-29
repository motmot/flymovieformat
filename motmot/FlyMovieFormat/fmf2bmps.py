import os, sys
import FlyMovieFormat
import Image

def main():
    try:
        filename = sys.argv[1]
    except:
        print 'Usage: fmf2bmps fmf_filename'
        sys.exit()
        
    path,ext = os.path.splitext(filename)
    if ext != '.fmf':
        print 'fmf_filename does not end in .fmf'
        sys.exit()

    fly_movie = FlyMovieFormat.FlyMovie(filename)
    n_frames = fly_movie.get_n_frames()

    for i in xrange(n_frames):
        save_frame,timestamp = fly_movie.get_next_frame()
        save_frame = save_frame[::-1,:] # flip for PIL
        h,w=save_frame.shape
        im = Image.fromstring('L',(w,h),save_frame.tostring())
        f='%s_%08d.bmp'%(path,i)
        print 'saving',f
        im.save(f)

if __name__=='__main__':
    main()
    
