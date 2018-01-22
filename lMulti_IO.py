"""Functions associated with I/O"""
import cPickle, traceback
import numpy as np, scipy.io
import cv2, cv2.cv as cv
    
#log
class RedirectText(object):
    def __init__(self,wxTextCtrl):
        self.out=wxTextCtrl
    
    def write(self,string):
        self.out.WriteText(string)

def log_uncaught_exceptions(ex_cls, ex, tb):
    """For catching exceptions that don't show up in STDERR using sys.excepthook"""
    exceptstr = ''.join(traceback.format_tb(tb)) + '\n'+ '{0}: {1}'.format(ex_cls,ex)
    print exceptstr

#data output
def writeMatlab(trackDict,trckParameters,data_file):
    """writes matlab .mat files from tracking data file. img parameters are the settings active at the end of tracking"""
    print "Saving %3.0f objects..." % len(trackDict)
    posData = np.empty((trackDict[0].shape[0],len(trackDict),2),dtype=float)
    for column, track in enumerate(trackDict.itervalues()):
        for axis in [0,1]:
            posData[:,column,axis] = track[:,axis]
    oDict = {"position":posData, "trck_parameters": trckParameters}
    scipy.io.savemat(data_file,oDict,format='5',oned_as='column')

def writeTxtData(trackDict,data_file):
    """formats and writes the the data in trackDict to a text file in the following format:
    0x \t 0y \t 1x \t 1y \t ...\n
    x  \t y \t  x \t  y \t ... \n """
    f2write = open(data_file,'w')
    trackIDs = trackDict.keys()
    header_str = "".join(["%sx\t%sy\t"%(ID,ID) for ID in trackIDs])
    f2write.write(header_str[0:-1]+"\n")
    #ExtDataList = [cData for cData in trackDict.itervalues()]
    #dTable = np.concatenate(tuple(ExtDataList),axis=1)
    #np.savetxt(data_file,dTable,fmt="%2.2f", delimiter="\t", header=header_str)
    for row in range(9000):
        row_str = "".join(["%2.2f\t%2.2f\t"%(c[row,0],c[row,1]) for c in trackDict.itervalues()])
        f2write.write(row_str[0:-1]+"\n")
    f2write.close()

#validation video generation
def InitializeVideoOutput(filename,frameInfo):
    """Initializes and returns a video writer object"""
    fourcc=cv.CV_FOURCC('X','V','I','D')
    #fourcc=-1
    fps = 30.
    vObject = cv2.VideoWriter(filename,fourcc,fps,frameInfo,True)
    return vObject

