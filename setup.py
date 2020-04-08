from setuptools import setup
from os import path
from io import open

# read the contents of README.md
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="motmot.FlyMovieFormat",
    version="1.10",
    description="support for .fmf (fly movie format) files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Andrew Straw",
    author_email="strawman@astraw.com",
    license="BSD",
    url="http://code.astraw.com/projects/motmot/fly-movie-format.html",
    namespace_packages=["motmot"],
    packages=["motmot", "motmot.FlyMovieFormat"],
    package_data={
        "motmot.FlyMovieFormat": [
            "test_raw8.fmf",
            "test_rgb8.fmf",
            "test_rgb32f.fmf",
            "test_mono8.fmf",
            "test_mono32f.fmf",
            "test_yuv422.fmf",
        ]
    },
    scripts=["scripts/pvn2fmf"],
    entry_points={
        "console_scripts": [
            "fmf2bmps = motmot.FlyMovieFormat.fmf2bmps:main",
            "fmf_from_images = motmot.FlyMovieFormat.images2fmf:main",
            "fmf_collapse = motmot.FlyMovieFormat.fmf_collapse:main",
            "fmf_info = motmot.FlyMovieFormat.fmf_info:main",
            "fmfcat = motmot.FlyMovieFormat.fmfcat:main",
            "ffmpeg2fmf = motmot.FlyMovieFormat.ffmpeg2fmf:main",
        ],
        "gui_scripts": [
            "fmf_plottimestamps = motmot.FlyMovieFormat.fmf_plottimestamps:main",
        ],
    },
)
