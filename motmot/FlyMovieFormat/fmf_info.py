from __future__ import print_function
import sys, datetime
import FlyMovieFormat

def main():
    try:
        filename1 = sys.argv[1]
    except:
        print("Usage: fmf_info fmf_filename")
        sys.exit()

    fly_movie = FlyMovieFormat.FlyMovie(filename1)
    ts = fly_movie.get_all_timestamps()
    dt0 = datetime.datetime.fromtimestamp(ts[0])
    dt1 = datetime.datetime.fromtimestamp(ts[-1])
    print('%s: %d frames, %d x %d pixels, %s format (%d bpp), timestamps range %.1f (%s) to %.1f (%s)'%(
        filename1,
        fly_movie.get_n_frames(),
        fly_movie.get_width(), fly_movie.get_height(),
        fly_movie.get_format(),
        fly_movie.get_bits_per_pixel(),
        ts[0],dt0.isoformat(),ts[-1],dt1.isoformat(),
        ))

if __name__=='__main__':
    main()
