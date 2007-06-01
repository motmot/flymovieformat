/*
 * fmfcompress: Read in a movie in FMF, output the movie in M4V.
 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "avformat.h"
#include "swscale.h"

/*#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
*/

/* in the compressed output, how many bits per pixel? */
#define BITRATEPERPIXEL 5
/* how often to we emit a key frame? */
#define STREAM_GOP_SIZE 100
/* frames per second */
#define STREAM_FRAME_RATE 25 
/* color encoding for each pixel; most formats seem to like
   YUV420 */
#define STREAM_PIX_FMT PIX_FMT_YUV420P /* default pix_fmt */

/* only needed if we STREAM_PIX_FMT is not PIX_FMT_YUV420P */
static int sws_flags = SWS_BICUBIC;

/**************************************************************/
/* fmf input */
typedef unsigned int uint32;
typedef unsigned long long uint64;

/* make variables describing fmf video global, since we are
   only reading in one movie, and it is used by multiple 
   functions */

/* pointer to fmf file stream */
FILE * fmffp;
/* number of pixels in each frame */
int fmfnpixels;
/* number of bytes in header */
uint64 headersize;
/* version of fmf file */
uint32 version;
/* number or rows of pixels in each frame */
uint32 nr;
/* number or columns of pixels in each frame */
uint32 nc;
/* number of bytes to encode each frame */
uint64 bytesperchunk;
/* number of frames */
uint64 nframes;
/* number of bits used to encode each pixel */
uint32 bitsperpixel;
/* 1 if nr is odd, 0 o.w. This is necessary because the 
   video is required to have and even number of rows and 
   columns. We pad one column on the right and one column 
   on th bottom if necessary. */
int isoddrows;
/* 1 if nc is odd, 0 o.w. */
int isoddcols;
/* if isoddcols==1, then we will need an extra buffer to 
   read in the unpadded image. */
uint8_t * extrabuf;

/* fmf_read_header:
   Reads the header from stream fmffp and stores information
   about the movie in the global variables defined above. 
 */
void fmf_read_header(){

  uint32 formatlen;
  int sizeofuint32 = 4;
  int sizeofuint64 = 8;
  
  /* seek to the start of the movie */
  fseek(fmffp,0,SEEK_SET);

  /* version number */
  if(fread(&version,sizeofuint32,1,fmffp) < 1){
    fprintf(stderr,"Error reading version number of input fmf file.\n");
    exit(1);
  }

  if(version == 1){
    /* version 1 only formats with MONO8 */
    bitsperpixel = 8;
  }
  else if(version == 3){
    /* version 3 encodes the length of the format string */
    if(fread(&formatlen,sizeofuint32,1,fmffp)<1){
      fprintf(stderr,"Error reading format length of input fmf file.\n");
      exit(1);
    }
    /* followed by the format string */
    fseek(fmffp,formatlen,SEEK_CUR);
    /* followed by the bits per pixel */
    if(fread(&bitsperpixel,sizeofuint32,1,fmffp)<1){
      fprintf(stderr,"Error reading bits per pixel of input fmf file.\n");
      exit(1);
    }
  }
  /* all versions then have the height of the frame */
  if(fread(&nr,sizeofuint32,1,fmffp)<1){
    fprintf(stderr,"Error reading frame height of input fmf file.\n");
    exit(1);
  }
  /* width of the frame */
  if(fread(&nc,sizeofuint32,1,fmffp)<1){
    fprintf(stderr,"Error reading frame width of input fmf file.\n");
    exit(1);
  }
  /* bytes encoding a frame */
  if(fread(&bytesperchunk,sizeofuint64,1,fmffp)<1){
    fprintf(stderr,"Error reading bytes per chunk of input fmf file.\n");
    exit(1);
  }
  /* number of frames */
  if(fread(&nframes,sizeofuint64,1,fmffp)<1){
    fprintf(stderr,"Error reading number of frames of input fmf file.\n");
    exit(1);
  }
  /* we've now read in the whole header, so use ftell 
     to get the header size */
  headersize = ftell(fmffp);
  /* check to see if the number of frames was written */
  if(nframes == 0){
    /* if not, then seek to the end of the file, and compute number
       of frames based on file size */
    fseek(fmffp,0,SEEK_END);
    nframes = (ftell(fmffp) - headersize)/bytesperchunk;
  }

  /* compute total number of pixels */
  fmfnpixels = nr*nc;
  /* store whether the number of rows, columns is odd */
  isoddrows = (nr%2) == 1;
  isoddcols = (nc%2) == 1;
  /* if number of columns is odd, allocate extrabuf */
  if(isoddcols){
    /* allocate an extra buffer so that we can pad images */
    extrabuf = (uint8_t*)malloc(sizeof(uint8_t)*fmfnpixels);
  }

  return;

}

/* fmf_read_frame:
   Reads frame number "frame" of the stream fmffp into buf.
*/
void fmf_read_frame(int frame, uint8_t * buf){

  int i;

  /* seek to the start of the frame: size of header + size of 
     previous frames + size of timestamp */
  fseek(fmffp,headersize+bytesperchunk*frame+sizeof(double),SEEK_SET);

  /* read in the image */
  if(isoddcols){
    /* if the number of columns is odd, we are going to pad
       with a column on the right that is 128. first, read
       frame into extra buffer */
    if(fread(extrabuf,sizeof(uint8_t),fmfnpixels,fmffp) < fmfnpixels){
      exit(1);
    }
    /* then copy over to buf, adding an extra pixel at every row */
    for(i = 0; i < nr; i++){
      memcpy(buf,extrabuf,nc);
      buf[nc] = 128;
      buf = &buf[nc+1];
      extrabuf = &extrabuf[nc];
    }
  }
  else{
    /* otherwise, just read in the frame */
    if(fread(buf,sizeof(uint8_t),fmfnpixels,fmffp) < fmfnpixels){
      exit(1);
    }
  }

  /* if the number of rows is odd, we are going to pad with a row
     on the bottom that is 128 */
  if(isoddrows){
    for(i = 0; i < nc; i++){
      buf[fmfnpixels-i-1] = 128;
    }
  }

  return;

}

/**************************************************************/
/* video output. all of this is basically the same as 
   output_example.c, except that the fill_yuv_image has 
   been changed to copy the fmf frame, frame size has been 
   changed to reflect size of fmf video, bit rate has been 
   set to something high */

AVFrame *picture, *tmp_picture;
uint8_t *video_outbuf;
int frame_count, video_outbuf_size;

/* add a video output stream */
static AVStream *add_video_stream(AVFormatContext *oc, int codec_id)
{
    AVCodecContext *c;
    AVStream *st;
    double bitrate;

    st = av_new_stream(oc, 0);
    if (!st) {
        fprintf(stderr, "Could not alloc stream\n");
        exit(1);
    }

    c = st->codec;
    c->codec_id = codec_id;
    c->codec_type = CODEC_TYPE_VIDEO;

    /* guess a reasonable bit rate */
    bitrate = BITRATEPERPIXEL*nr*nc;
    c->bit_rate = (int)bitrate;
    /* resolution must be a multiple of two */
    if(isoddcols){
      c->width = nc+1;
    }
    else{
      c->width = nc;
    }
    if(isoddrows){
      c->height = nr+1;
    }
    else{
      c->height = nr;
    }
    /* time base: this is the fundamental unit of time (in seconds) in terms
       of which frame timestamps are represented. for fixed-fps content,
       timebase should be 1/framerate and timestamp increments should be
       identically 1. */
    c->time_base.den = STREAM_FRAME_RATE;
    c->time_base.num = 1;
    c->gop_size = STREAM_GOP_SIZE;
    c->pix_fmt = STREAM_PIX_FMT;

    if (c->codec_id == CODEC_ID_MPEG2VIDEO) {
        /* just for testing, we also add B frames */
        c->max_b_frames = 2;
    }
    if (c->codec_id == CODEC_ID_MPEG1VIDEO){
        /* needed to avoid using macroblocks in which some coeffs overflow
           this doesnt happen with normal video, it just happens here as the
           motion of the chroma plane doesnt match the luma plane */
        c->mb_decision=2;
    }
    // some formats want stream headers to be separate
    if(!strcmp(oc->oformat->name, "mp4") || 
       !strcmp(oc->oformat->name, "mov") || 
       !strcmp(oc->oformat->name, "3gp"))
        c->flags |= CODEC_FLAG_GLOBAL_HEADER;

    return st;
}

static AVFrame *alloc_picture(int pix_fmt, int width, int height)
{
    AVFrame *picture;
    uint8_t *picture_buf;
    int size, i;

    picture = avcodec_alloc_frame();
    if (!picture)
        return NULL;
    size = avpicture_get_size(pix_fmt, width, height);
    picture_buf = av_malloc(size);
    if (!picture_buf) {
        av_free(picture);
        return NULL;
    }
    /* check me !!! */
    for(i = 0; i < size; i++){
      picture_buf[i] = 128;
    }
    avpicture_fill((AVPicture *)picture, picture_buf,
                   pix_fmt, width, height);
    return picture;
}

static void open_video(AVFormatContext *oc, AVStream *st)
{
    AVCodec *codec;
    AVCodecContext *c;

    c = st->codec;

    /* find the video encoder */
    codec = avcodec_find_encoder(c->codec_id);
    if (!codec) {
        fprintf(stderr, "codec not found\n");
        exit(1);
    }

    /* open the codec */
    if (avcodec_open(c, codec) < 0) {
        fprintf(stderr, "could not open codec\n");
        exit(1);
    }

    video_outbuf = NULL;
    if (!(oc->oformat->flags & AVFMT_RAWPICTURE)) {
        /* allocate output buffer */
        /* XXX: API change will be done */
        /* buffers passed into lav* can be allocated any way you prefer,
           as long as they're aligned enough for the architecture, and
           they're freed appropriately (such as using av_free for buffers
           allocated with av_malloc) */
        video_outbuf_size = 200000;
        video_outbuf = av_malloc(video_outbuf_size);
    }

    /* allocate the encoded raw picture */
    picture = alloc_picture(c->pix_fmt, c->width, c->height);
    if (!picture) {
        fprintf(stderr, "Could not allocate picture\n");
        exit(1);
    }

    /* if the output format is not YUV420P, then a temporary YUV420P
       picture is needed too. It is then converted to the required
       output format */
    tmp_picture = NULL;
    if (c->pix_fmt != PIX_FMT_YUV420P) {
        tmp_picture = alloc_picture(PIX_FMT_YUV420P, c->width, c->height);
        if (!tmp_picture) {
            fprintf(stderr, "Could not allocate temporary picture\n");
            exit(1);
        }
    }
}

/* prepare a dummy image */
static void fill_yuv_image(AVFrame *pict, int frame_index, int width, int height)
{

    /* read in video frame*/
    fmf_read_frame(frame_index,pict->data[0]);

}

static void write_video_frame(AVFormatContext *oc, AVStream *st)
{
    int out_size, ret;
    AVCodecContext *c;
    static struct SwsContext *img_convert_ctx;

    c = st->codec;

    if (frame_count >= nframes) {
        /* no more frame to compress. The codec has a latency of a few
           frames if using B frames, so we get the last frames by
           passing the same picture again */
    } else {
        if (c->pix_fmt != PIX_FMT_YUV420P) {
            /* as we only generate a YUV420P picture, we must convert it
               to the codec pixel format if needed */
            if (img_convert_ctx == NULL) {
                img_convert_ctx = sws_getContext(c->width, c->height,
                                                 PIX_FMT_YUV420P,
                                                 c->width, c->height,
                                                 c->pix_fmt,
                                                 sws_flags, NULL, NULL, NULL);
                if (img_convert_ctx == NULL) {
                    fprintf(stderr, "Cannot initialize the conversion context\n");
                    exit(1);
                }
            }
            fill_yuv_image(tmp_picture, frame_count, c->width, c->height);
            sws_scale(img_convert_ctx, tmp_picture->data, tmp_picture->linesize,
                      0, c->height, picture->data, picture->linesize);
        } else {
            fill_yuv_image(picture, frame_count, c->width, c->height);
        }
    }


    if (oc->oformat->flags & AVFMT_RAWPICTURE) {
        /* raw video case. The API will change slightly in the near
           futur for that */
        AVPacket pkt;
        av_init_packet(&pkt);

        pkt.flags |= PKT_FLAG_KEY;
        pkt.stream_index= st->index;
        pkt.data= (uint8_t *)picture;
        pkt.size= sizeof(AVPicture);

        ret = av_write_frame(oc, &pkt);
    } else {
        /* encode the image */
        out_size = avcodec_encode_video(c, video_outbuf, 
					video_outbuf_size, picture);
        /* if zero size, it means the image was buffered */
        if (out_size > 0) {
            AVPacket pkt;
            av_init_packet(&pkt);

            pkt.pts= av_rescale_q(c->coded_frame->pts, c->time_base, 
				  st->time_base);
            if(c->coded_frame->key_frame)
                pkt.flags |= PKT_FLAG_KEY;
            pkt.stream_index= st->index;
            pkt.data= video_outbuf;
            pkt.size= out_size;

            /* write the compressed frame in the media file */
            ret = av_write_frame(oc, &pkt);
        } else {
            ret = 0;
        }
    }
    if (ret != 0) {
        fprintf(stderr, "Error while writing video frame\n");
        exit(1);
    }
    frame_count++;
}

static void close_video(AVFormatContext *oc, AVStream *st)
{
    avcodec_close(st->codec);
    av_free(picture->data[0]);
    av_free(picture);
    if (tmp_picture) {
        av_free(tmp_picture->data[0]);
        av_free(tmp_picture);
    }
    av_free(video_outbuf);
}

/**************************************************************/
/* main function
 */

int main(int argc, char **argv)
{
  /* name of input file */
  const char *infilename;
  /* name of output file */
  char * outfilename;
  /* length of one of the file names */
  int filenamelength;
  /* format of output video */
  AVOutputFormat *fmt;
  /* context of output video. stores fmt, among other things */
  AVFormatContext *oc;
  /* video stream we create */
  AVStream *video_st;
  /* counter */
  int i;

  /* get input fmf filename and output m4v filename */
  if(argc <= 1){
    fprintf(stderr,"Usage: fmfcompress input.fmf [output.m4v]\n");
    exit(1);
  }
  else{
    infilename = argv[1];
    if(argc == 2){
      /* take stem from infilename, append "avi" */
      filenamelength = strlen(infilename);
      outfilename = (char*)malloc(sizeof(char)*filenamelength);
      strcpy(outfilename,infilename);
      strcpy(&outfilename[filenamelength-3],"m4v");
    }
    else{
      outfilename = (char*)argv[2];
      filenamelength = strlen(outfilename);
      if(strcmp(&outfilename[filenamelength-4],".m4v")){
	fprintf(stderr,"Output file name extension must be .m4v\n");
	exit(1);
      }
    }
  }
  
  /* open the fmf movie */
  fmffp = fopen(infilename,"rb");
  if(fmffp == 0){
    fprintf(stderr,"Could not open input fmf file %s for reading.\n",
	    infilename);
    exit(1);
  }
  
  /* read in the header information */
  fmf_read_header();
  
  /* initialize libavcodec, and register all codecs and formats */
  av_register_all();
  
  /* get fmt information for mpeg4 */
  fmt = guess_format("m4v",NULL,NULL);
  if (!fmt) {
    fprintf(stderr, "Could not find MPEG4 output format\n");
    exit(1);
  }
  
  /* allocate the output media context */
  oc = av_alloc_format_context();
  if (!oc) {
    fprintf(stderr, "Memory error\n");
    exit(1);
  }
  oc->oformat = fmt;
  snprintf(oc->filename, sizeof(oc->filename), "%s", outfilename);
  
  /* add the video stream using the default format codecs
     and initialize the codecs */
  video_st = NULL;
  if (fmt->video_codec != CODEC_ID_NONE) {
    video_st = add_video_stream(oc, fmt->video_codec);
  }
  
  /* set the output parameters (must be done even if no
     parameters). */
  if (av_set_parameters(oc, NULL) < 0) {
    fprintf(stderr, "Invalid output format parameters\n");
    exit(1);
  }
  
  dump_format(oc, 0, outfilename, 1);
  
  /* now that all the parameters are set, we can open the
     video codec and allocate the necessary encode buffers */
  if (video_st)
    open_video(oc, video_st);
  
  /* open the output file, if needed */
  if (!(fmt->flags & AVFMT_NOFILE)) {
    if (url_fopen(&oc->pb, outfilename, URL_WRONLY) < 0) {
      fprintf(stderr, "Could not open '%s'\n", outfilename);
      exit(1);
    }
  }
  
  /* write the stream header, if any */
  av_write_header(oc);
  
  for(i=0;i<nframes;i++) {
    /* output the video */
    if (!video_st)
      break;
    write_video_frame(oc, video_st);
    printf("encoding frame %10d\r", i);
  }
  
  /* close the codec */
  if (video_st)
    close_video(oc, video_st);
  
  /* write the trailer, if any */
  av_write_trailer(oc);
  
  /* free the streams */
  for(i = 0; i < oc->nb_streams; i++) {
    av_freep(&oc->streams[i]->codec);
    av_freep(&oc->streams[i]);
  }
  
  if (!(fmt->flags & AVFMT_NOFILE)) {
    /* close the output file */
    url_fclose(&oc->pb);
  }
  
  /* free the stream */
  av_free(oc);
  
  /* close the fmf movie */
  fclose(fmffp);
  
  /* deallocate the extra buffer */
  if(isoddcols){
    free(extrabuf);
  }
  
  return 0;
}
