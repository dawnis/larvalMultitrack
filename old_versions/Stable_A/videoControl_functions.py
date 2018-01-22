"""Functions associated with controlling video input"""
import cv2.cv as cv, cv2

def GetGSFrame(videostream):
    """bool,frame=GetGSFrame(videostream)
    Returns the bool from videostream.read() and the grayscale frame"""
    s,frame=videostream.read()
    if s:
        if (frame.ndim==3):
            return s, cv2.cvtColor(frame,cv.CV_RGB2GRAY)
    return s, frame
        
