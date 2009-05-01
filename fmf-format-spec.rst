.. _fmf-format:

****************************************
FlyMovieFormat (.fmf) file specification
****************************************

This file type defines 8-bit grayscale image sequences where each
image is associated with a timestamp.

All numbers are little-endian (Intel standard). Type key is below::

  Typecode Name      Description 					       
  -------- --------- --------------------------------------------------- 
  I    	 version   Version number (currently only 1 or 3)              
  II   	 framesize Number of rows and columns in each frame	        
  Q    	 chunksize Bytes per "chunk" (timestamp + frame)	        
  Q    	 n_frames  Number of frames (0=unknown, read file to find out) 
  -------- --------- --------------------------------------------------- 
     For version 3 only                                                  
  -------- --------- --------------------------------------------------- 
  I        lenformat Length of the subsequent format string              
  *B       format    string containing format, e.g. 'MONO8' or 'YUV422'  
  I        bpp       Bits per pixel, e.g. 8                              
  -------- --------- --------------------------------------------------- 
     For the rest of the file, repeats of the following                  
  -------- --------- --------------------------------------------------- 
  d        timestamp Timestamp (seconds in current epoch)                
  *B       frame     Image data, rows*columns bytes, row major ordering  
  -------- --------- --------------------------------------------------- 
                                                                         
  Typecode description bytes C type            		               
  -------- ----------- ----- --------------------------------------      
  B    	 UInt8       1	   unsigned char     		               
  I    	 UInt32      4	   unsigned int      		               
  Q    	 UInt64      8	   unsigned long long (__int64 on Windows)     
  d    	 Double64    8	   double	                               
