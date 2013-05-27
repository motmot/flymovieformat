import sys
import FlyMovieFormat

def main():
    try:
        filename1 = sys.argv[1]
    except:
        print """Usage: fmf_info fmf_filename"""
        sys.exit()

    fly_movie = FlyMovieFormat.FlyMovie(filename1)
    ts = fly_movie.get_all_timestamps()
    print '%s: %d frames, %d x %d pixels, %s format (%d bpp), timestamps range %.1f to %.1f'%(
        filename1,
        fly_movie.get_n_frames(),
        fly_movie.get_width(), fly_movie.get_height(),
        fly_movie.get_format(),
        fly_movie.get_bits_per_pixel(),
        ts[0],ts[-1],
        )

if __name__=='__main__':
    main()
