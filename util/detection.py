# -*- coding: utf-8 -*-
"""
Detect inertial particles.

Created on Wed Jan  6 15:46:13 2016

@author: yosef
"""
from itertools import izip
from optv.tracking_framebuf import TargetArray, CORRES_NONE

import numpy as np
from skimage.feature import match_template, peak_local_max, blob_dog
from skimage.morphology import disk

def targetize(detects, approx_size, sumg=10):
    """
    Creates a correct TargetArray object with the detected positions and some
    placeholder values for target parameters that I don't use.
    
    Arguments:
    detects - (n,2) array, pixel coordinates of a detected target.
    approx_size - a value to use for the pixel size placeholders.
    sumg - a value to use for the sum of grey values placeholder.
        Default: 10.
    """
    targs = TargetArray(len(detects))
    
    tnum = 0
    for t, pos in izip(targs, detects):
        t.set_pos(pos)
        t.set_pnr(tnum)
        t.set_sum_grey_value(sumg) # whatever
        t.set_pixel_counts(approx_size**2 * 4, approx_size*2, approx_size*2)
        t.set_tnr(CORRES_NONE) # The official "correspondence not found" that 
                               # the rest of the code expects.
        tnum += 1
    
    return targs
    
def detect_large_particles(image, approx_size=15, peak_thresh=0.5):
    """
    A particle detection method based on template matching followed by peak 
    fitting. It is needed when particles are large, because the other methods
    assume that particles are small clumps of particles and can find multiple
    targets per large particle or find an inconsistent centre.
    
    Arguments:
    image - the image to search for particles.
    approx_size - search for particles whose pixel radius is around this value.
    peak_thresh - minimum grey value for a peak to be recognized.
    
    Returns:
    a TargetArray with the detections.
    """
    sel = disk(approx_size)
    matched = match_template(image, sel, pad_input=True)
    peaks = np.c_[peak_local_max(matched, threshold_abs=peak_thresh)][:,::-1]
    return targetize(peaks, approx_size)

def detect_blobs(image, approx_size=15, thresh=0.1):
    """
    A particle detection method based on the Difference of Gaussians algorithm.
    It is possibly more consistent than the method used in 
    ``detect_large_particles()``. 
    
    Arguments:
    image - the image to search for particles.
    approx_size - just a placeholder and there's a default so don't worry 
        about it.
    thresh - minimum grey value for blob pixels.
    
    Returns:
    a TargetArray with the detections.
    """
    blobs = blob_dog(image.T, max_sigma=5, threshold=thresh)
    return targetize(blobs, approx_size)

def read_blob(fname, frame_num, approx_size=15):
    """
    Reads blob.dat file with the targets created by BlobRecorder software
    of a real-time image processing system
    
    Arguments:
        fname - the name of the .dat file to read
        frame_num - the number of the frame to read
        approx_size - just a placeholder and there's a default so don't worry
        about  it.
    """


    header_dt = np.dtype([('framecount','i'),('tstart','7i'),('tend','7i')])
    blob_head_dt = np.dtype([('stamp','i'),('frame_n','i'),('blob_count','i')])
    blob_dt = np.dtype([('x0','<h'),('x1','<h'),('y0','<h'),('y1','<h'),('higher_bits',np.int64)])
    
    with open('blob0_2017.07.05_09.40.43_part0.dat','rb') as f:
    # with open('b1.dat','rb') as f:
    
        header = np.fromfile(f,dtype=header_dt,count=1)
        print('header', header)
        framecount = header[0][0]
        print('framecount',framecount)
        
        for frame in range(2): #framecount):
            blob_header = np.fromfile(f,dtype=blob_head_dt,count=1)
            # print('blob header', blob_header)
            blob_count = blob_header[0][-1]
            
            if blob_count:
                print('blob header', blob_header)
                blobs = np.fromfile(f,dtype=blob_dt,count=blob_count)
                # print('x0,y0,->x1,y1',blob['x0'],blob['y0'],blob['x1'],blob['y1'])
            
                for blob in blobs:
                    A = np.bitwise_and(np.array(2**20-1).astype(np.int64),blob['higher_bits'])         # Area
                    X = (np.bitwise_and(np.array(0x00000fffff000000).astype(np.int64),blob['higher_bits']) >> 24 ) / 256.0
                    Y = (np.bitwise_and(np.array(0xfffff00000000000).astype(np.int64),blob['higher_bits']) >> 44 ) / 256.0
                    print('A=%3.1f,xc=%3.1f,yc=%3.1f'%(A,X,Y))
        
