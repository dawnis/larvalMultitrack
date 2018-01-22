"""Functions Associated With Image Processing and Tracking"""
import numpy as np
import cv2.cv as cv, cv2
#from collections import namedtuple as namedtuple

#def SetLmFnc_Globals((width,height)):
#    """Defines globals for containing the frames"""
#    global diffImg
#    global trackImg
#    global contourlist
#    global bgMask
#    diffImg = np.zeros((width,height),dtype="uint8")
#    trackImg = np.empty((width,height,3),dtype="uint8")
#    contourlist = np.empty((100,3),dtype=int) 
#    bgMask = np.zeros((width,height),dtype="bool")
#    oBG = np.zeros((width,height,2),dtype="uint8")

def CalculateBGDiff(bgIMG,currFrame,trckThrsh):
    """Calculates and thresholds the difference between the threshold image and the background. Returns 255 for all pixels above the threshold"""
#    diffImg = bgIMG.astype(float)-currFrame.astype(float)
#    diffImg[diffImg<0]=0
    bgMask = currFrame>bgIMG
    diffImg = bgIMG-currFrame
    diffImg[bgMask] = 0
    #cv2.imshowp("output",diffImg)
    (thresh,binIMG)=cv2.threshold(diffImg,trckThrsh,255,cv.CV_THRESH_BINARY)
    binIMG = cv2.medianBlur(binIMG,ksize=3)
    binIMG = cv2.erode(binIMG,cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3)))
    #binIMG = cv2.erode(binIMG,cv2.getStructuringElement(cv2.MORPH_ERODE,(3,3)))
    binIMG = cv2.dilate(binIMG,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)),iterations=2)
    return binIMG 

def BGUpdateFnc(bgIMG,currFrame,alpha):
    """updates background image based on alpha"""
    alpha = alpha/1000.
    #uBGImg = (1.-alpha)*bgIMG+alpha*currFrame
    oBG=cv2.convertScaleAbs(bgIMG,alpha=1.-alpha)
    nBG=cv2.convertScaleAbs(currFrame,alpha=alpha)
    return nBG+oBG

def draw_tObjs(liveframe,contours,currObjs,neighborDist):
    """returns the current live frame with contours from currObjs drawn"""
    trackImg=np.empty((liveframe.shape[0], liveframe.shape[1], 3), dtype="uint8")
    for c in range(trackImg.shape[2]):
        trackImg[:,:,c] = liveframe

    for tObj in currObjs.itervalues():
        if tObj.inFrame:
            cv2.drawContours(trackImg,contours[tObj.kID],-1,tObj.color,-1)
            cv2.circle(trackImg,tuple(tObj.xy),neighborDist,tObj.color)
    #cv2.imwrite("oFrame.png",liveframe)
    return trackImg

def updateTracking(fIdx,binIMG,minSize,minDist,currObjs,trackData):
    """updates the tracking information based on the binary threshold image and current list of tracked objects. Returns contours, updated tObj list, and updates tracking record"""
    contours,contourlist = DetectObjects(binIMG,minSize)
    TrackObjects(currObjs,contourlist,minDist)
    updateTrackData(currObjs,trackData,fIdx)
    return contours

def updateTrackData(currObjs,trackData,fIdx)
    """puts current xy coordinates into tracking record structure for each objID. If objID doesn't exist, initializes a new entry"""
    for obj in currObjs.keys():

def DetectObjects(binIMG,minSize):
    """finds the contours and returns those over minSize"""
    contourlist = np.empty((1000,3),dtype=int) 
    (contours,hierarchy)=cv2.findContours(np.array(binIMG),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    dCount = 0
    for n, cnt in enumerate(contours):
        if cv2.contourArea(cnt) > minSize:
            dCount+=1
            xyCoordinate = np.mean(cnt,axis=0)[0]
            contourlist[dCount-1,0] = n
            contourlist[dCount-1,1:]= xyCoordinate
    #return contours,np.delete(contourlist,np.s_[dCount:],axis=0)
    return contours, contourlist[:dCount,:].copy()

def TrackObjects(cObjects,ctrlist,minDist):
    """determines whether the contours in ctrlist correspond to the current tracked objects and updates cObjects with the new information. cObjects is a list of type namedtuple Obj"""
    dcr = lambda x : x-1 if x > 0 else 0

    for Obj in cObjects.itervalues():
        Obj.inFrame=False
        Obj.lostFrames+=1
    trObjects = cObjects.copy() #avoid changes to structure in loop

    for contour in ctrlist:
        smallest_distance=(minDist,-1) #keeps track of smallest distance and the associated ID; -1 is unassigned
        for Obj in trObjects.itervalues():
            d2Obj = np.sum((Obj.xy-contour[1:3])**2)**0.5 #current tracking based on closest distance only
            if d2Obj<smallest_distance[0]:
                smallest_distance = (d2Obj,Obj.objID)
        if smallest_distance[0]<minDist:
            cObjects[smallest_distance[1]].xy = contour[1:3]
            cObjects[smallest_distance[1]].kID = contour[0]
            cObjects[smallest_distance[1]].inFrame = True
            cObjects[smallest_distance[1]].lostFrames = dcr(cObjects[smallest_distance[1]].lostFrames)
            trObjects[smallest_distance[1]].inFrame = True
            trObjects[smallest_distance[1]].lostFrames = dcr(cObjects[smallest_distance[1]].lostFrames)
        else:
            currIDs = cObjects.keys()
            currIDs.append(-1)
            nObjID = np.max(currIDs)+1
            cObjects.update({nObjID:trackedObject(objID=nObjID,xy=contour[1:3],kID=contour[0])})

    #trObjects = cObjects.copy() #make a copy, since using del will alter a dict using iteration generator
    for key,tObj in trObjects.iteritems():
        if (not tObj.inFrame) & (tObj.lostFrames>60):
            del cObjects[key]

#def make_tObj(xy,kID,color):
#    """returns a named tuple of type tObj"""
#    if 'trackedObj' not in globals():
#        global trackedObj
#        trackedObj=namedtuple('trackedObj',['xy','kID','color','inFrame'],verbose=Falsep)
#    return trackedObj(xy=xy,kID=kID,color=color,inFrame=True) 

class trackedObject():
    """storage class for parameters associated with tracked objects"""
    def __init__(self,objID,kID,xy):
        self.objID=objID
        self.kID=kID
        self.xy=xy
        #self.color = tuple((np.random.random((3))*255).astype("int"))
        R,G,B = tuple(np.round(np.random.rand(3)*255))
        self.color = cv.RGB(R,G,B)
        self.inFrame=True
        self.lostFrames = 0
