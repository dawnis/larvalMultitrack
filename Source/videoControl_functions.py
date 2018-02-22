"""Functions associated with controlling video input"""
import cv2 as cv, cv2


#def setVideoCapture(GlProp,inputStream):
#    """sets up the video capture with either a file (inputStream is file location) or video capture (inputStream is -1)
#    """
#    if inputStream==-1:
#        GlProp.vidstream=cv2.VideoCapture(-1)
#        #GlProp.vidstream.open(0)
#        #GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
#        #GlProp.fps = GlProp.vidstream.get(cv.CV_CAP_PROP_FPS)
#        GlProp.fps = 30.
#        cv2.waitKey(20)
#    else:
#        GlProp.vidstream=cv2.VideoCapture(self.dirname+'\\'+self.filename)
#        GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
#        GlProp.fps = 1000.

#def count_cameras():
#    for i in range(10):
#        temp_camera = cv2.VideoCapture(i)
#        temp_frame = temp_camera.retrieve()
#        if temp_frame==None:
#            del(temp_frame)
#            return i-1

def GetGSFrame(videostream):
    """bool,frame=GetGSFrame(videostream)
    Returns the bool from videostream.read() and the grayscale frame"""
    s,frame=videostream.read()
    #videostream.grab()
    #s,frame=videostream.retrieve()
    if s:
        if (frame.ndim==3):
            return s, cv2.cvtColor(frame,cv.COLOR_RGB2GRAY)
    return s, frame
        
