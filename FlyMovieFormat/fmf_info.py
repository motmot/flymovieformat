import sys
import FlyMovieFormat

def main():
    try:
        filename1 = sys.argv[1]
    except:
        print """Usage: fmf_info fmf_filename

This program takes a set of .fmf files and saves the mean of all
frames from all files as a .bmp image file.

The files used are in the range fmf_filename1 <= FILE <= fmf_filename2.

"""
        sys.exit()

    fly_movie = FlyMovieFormat.FlyMovie(filename1)
    x = fly_movie.get_height
    print '%s: %d frames, %d x %d pixels, %s format (%d bpp)'%(
        filename1,
        fly_movie.get_n_frames(),
        fly_movie.get_width(), fly_movie.get_height(),
        fly_movie.get_format(),
        fly_movie.get_bits_per_pixel(),
        )

if __name__=='__main__':
    main()
