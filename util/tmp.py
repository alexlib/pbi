import numpy as np
import os, glob
# from struct import unpack


header_dt = np.dtype([('framecount','i'),('tstart','7i'),('tend','7i')])
blob_head_dt = np.dtype([('stamp','i'),('frame_n','i'),('blob_count','i')])
blob_dt = np.dtype([('x0','<h'),('x1','<h'),('y0','<h'),('y1','<h'),('higher_bits',np.int64)])

blob_dir = '/Users/alex/Desktop/181016_10/Blobs_edge_grisha_1/'
filenames = glob.glob(os.path.join(blob_dir,'b*_part0.dat'))

class MultipleFileManager(object):
    def __init__(self, files):
        self.files = files

    def __enter__(self):
        self.open_files = map(open, self.files)
        return self.open_files

    def __exit__(self):
        for f in self.open_files:
            f.close()


with MultipleFileManager(filenames) as files:
    for f in files:
        print(f)
        header = np.fromfile(f,dtype=header_dt,count=1)
        print('header', header)
        framecount = header[0][0]
        print('framecount',framecount)
        
        for frame in range(2): #framecount):
            blob_header = np.fromfile(f,dtype=blob_head_dt,count=1)
            # print('blob header', blob_header)
            blob_count = blob_header[0][-1]
            
            if blob_count:
                print('Not empty blob header', blob_header)
                
        #     blobs = np.fromfile(f,dtype=blob_dt,count=blob_count)
        #     # print('x0,y0,->x1,y1',blob['x0'],blob['y0'],blob['x1'],blob['y1'])
        # 
        #     for blob in blobs:
        #         A = np.bitwise_and(np.array(2**20-1).astype(np.int64),blob['higher_bits'])         # Area
        #         X = (np.bitwise_and(np.array(0x00000fffff000000).astype(np.int64),blob['higher_bits']) >> 24 ) / 256.0
        #         Y = (np.bitwise_and(np.array(0xfffff00000000000).astype(np.int64),blob['higher_bits']) >> 44 ) / 256.0
        #         print('A=%3.1f,xc=%3.1f,yc=%3.1f'%(A,X,Y))