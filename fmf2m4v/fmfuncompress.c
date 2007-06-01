// avcodec_sample.cpp

// A small sample program that shows how to use libavformat and libavcodec to
// read video from a file.
//
// Use
//
// g++ -o avcodec_sample avcodec_sample.cpp -lavformat -lavcodec -lz
//
// to build (assuming libavformat and libavcodec are correctly installed on
// your system).
//
// Run using
//
// avcodec_sample myvideofile.mpg
//
// to write the first five frames from "myvideofile.mpg" to disk in PPM
// format.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "avcodec.h"
#include "avformat.h"

double framerate;

int GetNextFrame(AVFormatContext *pFormatCtx, AVCodecContext *pCodecCtx, 
    int videoStream, AVFrame *pFrame)
{
    static AVPacket packet;
    static int      bytesRemaining=0;
    static uint8_t  *rawData;
    static int      fFirstTime=1;
    int             bytesDecoded;
    int             frameFinished;

    // First time we're called, set packet.data to NULL to indicate it
    // doesn't have to be freed
    if(fFirstTime)
    {
        fFirstTime=0;
        packet.data=NULL;
    }

    // Decode packets until we have decoded a complete frame
    while(1)
    {
        // Work on the current packet until we have decoded all of it
        while(bytesRemaining > 0)
        {
            // Decode the next chunk of data
            bytesDecoded=avcodec_decode_video(pCodecCtx, pFrame,
                &frameFinished, rawData, bytesRemaining);

            // Was there an error?
            if(bytesDecoded < 0)
            {
                fprintf(stderr, "Error while decoding frame\n");
                return 0;
            }

            bytesRemaining-=bytesDecoded;
            rawData+=bytesDecoded;

            // Did we finish the current frame? Then we can return
            if(frameFinished)
                return 1;
        }

        // Read the next packet, skipping all packets that aren't for this
        // stream
        do
        {
            // Free old packet
            if(packet.data!=NULL)
                av_free_packet(&packet);

            // Read new packet
            if(av_read_frame(pFormatCtx, &packet)<0)
                goto loop_exit;
        } while(packet.stream_index!=videoStream);

        bytesRemaining=packet.size;
        rawData=packet.data;
    }

loop_exit:

    // Decode the rest of the last frame
    bytesDecoded=avcodec_decode_video(pCodecCtx, pFrame, &frameFinished, 
        rawData, bytesRemaining);

    // Free last packet
    if(packet.data!=NULL)
        av_free_packet(&packet);

    return frameFinished!=0;
}

/*********************************************************************/
/* fmf file handling */

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
uint32 nr;
/* number or columns of pixels in each frame */
uint32 nc;
/* number of bytes to encode each frame */
uint64 bytesperchunk;
/* number of frames */
uint64 nframes;
/* number of bits used to encode each pixel */
uint32 bitsperpixel;

void fmf_write_header(){

  uint32 formatlen = 5;
  uint32 version = 3;
  uint32 bitsperpixel = 8;
  const char dataformat[] = "MONO8";
  int sizeofuint32 = 4;
  int sizeofuint64 = 8;

  /* version number */
  if(fwrite(&version,sizeofuint32,1,fmffp) < 1){
    fprintf(stderr,"Error writing version number to output fmf file.\n");
    exit(1);
  }

  /* format length */
  if(fwrite(&formatlen,sizeofuint32,1,fmffp)<1){
    fprintf(stderr,"Error writing format length to output fmf file.\n");
    exit(1);
  }

  /* format string */
  if(fwrite(&dataformat,sizeof(char),formatlen,fmffp)<formatlen){
    fprintf(stderr,"Error writing format string to output fmf file.\n");
    exit(1);
  }

  /* bits per pixel */
  if(fwrite(&bitsperpixel,sizeofuint32,1,fmffp)<1){
    fprintf(stderr,"Error writing bits per pixel to output fmf file.\n");
    exit(1);
  }

  /* height of the frame */
  if(fwrite(&nr,sizeofuint32,1,fmffp)<1){
    fprintf(stderr,"Error writing frame height to output fmf file.\n");
    exit(1);
  }

  /* width of the frame */
  if(fwrite(&nc,sizeofuint32,1,fmffp)<1){
    fprintf(stderr,"Error writing frame width to output fmf file.\n");
    exit(1);
  }

  /* bytes encoding a frame */
  if(fwrite(&bytesperchunk,sizeofuint64,1,fmffp)<1){
    fprintf(stderr,"Error writing bytes per chunk to output fmf file.\n");
    exit(1);
  }

  /* number of frames */
  if(fwrite(&nframes,sizeofuint64,1,fmffp)<1){
    fprintf(stderr,"Error writing number of frames to output fmf file.\n");
    exit(1);
  }

  return;

}

void fmf_write_frame(AVFrame *pFrame, int iFrame)
{
    double timestamp;
    int y;

    // Write time stamp
    timestamp = (double)iFrame/framerate;
    fwrite(&timestamp,sizeof(double),1,fmffp);

    // Write pixel data
    for(y=0; y<nr; y++){
      fwrite(pFrame->data[0]+y*pFrame->linesize[0], 1, nc, fmffp);
    }
}

int main(int argc, char *argv[])
{
    AVFormatContext *pFormatCtx;
    int             i, videoStream;
    AVCodecContext  *pCodecCtx;
    AVCodec         *pCodec;
    AVFrame         *pFrame; 
    const char * infilename;
    char * outfilename;
    int filenamelength;
    
    /* get input fmf filename and output m4v filename */
    if(argc <= 1){
      fprintf(stderr,"Usage: fmfuncompress input.m4v [output.fmf]\n");
      exit(1);
    }
    else{
      infilename = argv[1];
      if(argc == 2){
	/* take stem from infilename, append "avi" */
	filenamelength = strlen(infilename);
	outfilename = (char*)malloc(sizeof(char)*filenamelength);
	strcpy(outfilename,infilename);
	strcpy(&outfilename[filenamelength-3],"fmf");
      }
      else{
	outfilename = (char*)argv[2];
	filenamelength = strlen(outfilename);
	if(strcmp(&outfilename[filenamelength-4],".fmf")){
	  fprintf(stderr,"Output file name extension must be .fmf\n");
	  exit(1);
	}
      }
    }

    // Register all formats and codecs
    av_register_all();

    // Open video file
    if(av_open_input_file(&pFormatCtx, infilename, NULL, 0, NULL)!=0)
        return -1; // Couldn't open file

    // Retrieve stream information
    if(av_find_stream_info(pFormatCtx)<0)
        return -1; // Couldn't find stream information

    // Dump information about file onto standard error
    dump_format(pFormatCtx, 0, infilename, 0);

    // Find the first video stream
    videoStream=-1;
    for(i=0; i<pFormatCtx->nb_streams; i++)
        if(pFormatCtx->streams[i]->codec->codec_type==CODEC_TYPE_VIDEO)
        {
            videoStream=i;
            break;
        }
    if(videoStream==-1)
        return -1; // Didn't find a video stream

    // Get a pointer to the codec context for the video stream
    pCodecCtx=pFormatCtx->streams[videoStream]->codec;

    // Find the decoder for the video stream
    pCodec=avcodec_find_decoder(pCodecCtx->codec_id);
    if(pCodec==NULL)
        return -1; // Codec not found

    // Inform the codec that we can handle truncated bitstreams -- i.e.,
    // bitstreams where frame boundaries can fall in the middle of packets
    if(pCodec->capabilities & CODEC_CAP_TRUNCATED)
        pCodecCtx->flags|=CODEC_FLAG_TRUNCATED;

    // Open codec
    if(avcodec_open(pCodecCtx, pCodec)<0)
        return -1; // Could not open codec

     // Allocate video frame
    pFrame=avcodec_alloc_frame();

    // Store information about video

    // frame rate
    framerate = (double)pCodecCtx->time_base.num/
      (double)pCodecCtx->time_base.den;
    printf("Frame rate set to %f\n",framerate);
    // number of rows
    nr = pCodecCtx->height;
    // number of columns
    nc = pCodecCtx->width;
    // number of pixels
    fmfnpixels = nr*nc;
    // bytes per frame
    bytesperchunk = sizeof(double)+fmfnpixels;

    // Open the output fmf file
    fmffp = fopen(outfilename,"wb");
    if(fmffp == 0){
      fprintf(stderr,"Could not open output fmf file %s for writing.\n",
	      outfilename);
    }

    // Write the header
    fmf_write_header();

    // Read frames and write as fmf format
    i=0;
    while(GetNextFrame(pFormatCtx, pCodecCtx, videoStream, pFrame))
    {
      fmf_write_frame(pFrame,i);
      printf("decoding frame %10d\r", i);
      i++;
    }

    // close output file
    fclose(fmffp);

    // Free the YUV frame
    av_free(pFrame);

    // Close the codec
    avcodec_close(pCodecCtx);

    // Close the video file
    av_close_input_file(pFormatCtx);

    return 0;
}
