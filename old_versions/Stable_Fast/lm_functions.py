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

def CalculateBGDiff(bgIMG,currFrame,trckThrsh,trckPara):
    """Calculates and thresholds the difference between the threshold image and the background. Returns 255 for all pixels above the threshold"""
#    diffImg = bgIMG.astype(float)-currFrame.astype(float)
#    diffImg[diffImg<0]=0
    #bgMask = currFrame>bgIMG
    #diffImg = bgIMG-currFrame
    #diffImg[bgMask] = 0
    diffImg = cv2.subtract(bgIMG,currFrame)
    diffImg = cv2.medianBlur(diffImg,ksize=3)
    #cv2.imshowp("output",diffImg)
    (thresh,binIMG)=cv2.threshold(diffImg,trckThrsh,255,cv.CV_THRESH_BINARY)
    #binIMG=cv2.adaptiveThreshold(diffImg,255,cv.CV_ADAPTIVE_THRESH_MEAN_C,cv.CV_THRESH_BINARY,5,0)
    #binIMG = cv2.medianBlur(binIMG,ksize=3)
    if trckPara["Erosion"]:
        binIMG = cv2.erode(binIMG,cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3)),iterations=trckPara["Erosion"])
    #binIMG = cv2.erode(binIMG,cv2.getStructuringElement(cv2.MORPH_ERODE,(3,3)))
    if trckPara["Dilation"]:
        binIMG = cv2.dilate(binIMG,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)),iterations=trckPara["Dilation"])
    return binIMG 

def BGUpdateFnc(bgIMG,currFrame,currObjs,contours,alpha):
    """updates background image based on alpha"""
    alpha = alpha/1000.
    #oBG=cv2.convertScaleAbs(bgIMG,alpha=1.-alpha,beta=0)
    #nBG=cv2.convertScaleAbs(currFrame,alpha=alpha)
    #uBG = nBG+oBG
    gNoise = np.random.normal(0,0.25) #noise necessry to add a varying signal upon which small increments in intensity can be accumulated.
    uBG = cv2.addWeighted(src1=bgIMG,alpha=1.-alpha,src2=currFrame,beta=alpha,gamma=gNoise)
    for tObj in currObjs.itervalues():
        if tObj.fishProb > 0.5:
            ly = tObj.xy[1]-tObj.boundBx[1]
            uy = tObj.xy[1]+tObj.boundBx[1]
            lx = tObj.xy[0]-tObj.boundBx[0]
            rx = tObj.xy[0]+tObj.boundBx[0]
            uBG[ly:uy,lx:rx] = bgIMG[ly:uy,lx:rx]  
    return uBG

def draw_tObjs(liveframe,contours,currObjs,neighborDist):
    """returns the current live frame with contours from currObjs drawn"""
    trackImg=np.empty((liveframe.shape[0], liveframe.shape[1], 3), dtype="uint8")
    for c in range(trackImg.shape[2]):
        trackImg[:,:,c] = liveframe

    for tObj in currObjs.itervalues():
        if tObj.inFrame:
            cv2.drawContours(trackImg,contours[tObj.kID],-1,tObj.color,-1)
#        trackImg[tObj.xy[1]-tObj.boundBx[1]:tObj.xy[1]+tObj.boundBx[1],
#                 tObj.xy[0]-tObj.boundBx[0]:tObj.xy[0]+tObj.boundBx[0]] = 0
        cv2.circle(trackImg,tuple(tObj.xy),neighborDist,tObj.color)
        cv2.putText(trackImg,
                    "P:%2.2f"%(tObj.fishProb),
                    tuple(tObj.xy+15),
                    cv.CV_FONT_HERSHEY_PLAIN,
                    fontScale=1,
                    color=tObj.color)
    #cv2.imwrite("oFrame.png",liveframe)
    return trackImg

def updateTracking(fIdx,binIMG,minSize,minDist,currObjs,trackData):
    """updates the tracking information based on the binary threshold image and current list of tracked objects. Returns contours, updated tObj list, and updates tracking record"""
    contours,contourlist = DetectObjects(binIMG,minSize)
    TrackObjects(currObjs,trackData.keys(),contourlist,minDist)
    updateTrackData(currObjs,trackData,fIdx)
    return contours

def updateTrackData(currObjs,trackData,fIdx):
    """puts current xy coordinates into tracking record structure for each objID. If objID doesn't exist, initializes a new entry"""
    for objKy,obj in currObjs.iteritems():
        if objKy in trackData.keys():
            trackData[objKy][fIdx,:] = obj.xy
        else:
            trackData.update({objKy:np.zeros((9000,2),dtype=float)+np.nan})#initialize with nan to signify empty spots

def DetectObjects(binIMG,minSize):
    """finds the contours and returns those over minSize"""
    contourlist = np.empty((1000,5),dtype=int) 
    (contours,hierarchy)=cv2.findContours(np.array(binIMG),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    dCount = 0
    for n, cnt in enumerate(contours):
        if cv2.contourArea(cnt) > minSize:
            dCount+=1
            xyCoordinate = np.mean(cnt,axis=0)[0]
            contourlist[dCount-1,0] = n
            contourlist[dCount-1,1:3]= xyCoordinate
            x,y,w,h = cv2.boundingRect(cnt)
            contourlist[dCount-1,3:] = [w,h]
    #return contours,np.delete(contourlist,np.s_[dCount:],axis=0)
    return contours, contourlist[:dCount,:].copy()

def TrackObjects(cObjects,trackKeys,ctrlist,minDist):
    """determines whether the contours in ctrlist correspond to the current tracked objects and updates cObjects with the new information. cObjects is a list of type namedtuple Obj"""
    dcr = lambda x : x-1 if x > 0 else 0
    icr = lambda x : x+0.02 if x < 1 else 1

    for Obj in cObjects.itervalues():
        Obj.inFrame=False
        Obj.lostFrames+=1
    trObjects = cObjects.copy() #avoid changes to structure in loop
    
    if len(trackKeys)>0:
        currID_mx = np.max(trackKeys)
    else:
        currID_mx = -1

    for contour in ctrlist:
        smallest_distance=(minDist,-1) #keeps track of smallest distance and the associated ID; -1 is unassigned
        for Obj in trObjects.itervalues():
            d2Obj = np.sum((Obj.xy-contour[1:3])**2)**0.5 #current tracking based on closest distance only
            if d2Obj<smallest_distance[0]:
                smallest_distance = (d2Obj,Obj.objID)
        if smallest_distance[0]<minDist:
            cObjects[smallest_distance[1]].xy = contour[1:3]
            cObjects[smallest_distance[1]].boundBx = contour[3:]
            cObjects[smallest_distance[1]].kID = contour[0]
            cObjects[smallest_distance[1]].inFrame = True
            cObjects[smallest_distance[1]].lostFrames = dcr(cObjects[smallest_distance[1]].lostFrames)
            cObjects[smallest_distance[1]].fishProb = icr(cObjects[smallest_distance[1]].fishProb)
            trObjects[smallest_distance[1]].inFrame = True
            trObjects[smallest_distance[1]].lostFrames = dcr(cObjects[smallest_distance[1]].lostFrames)
        else:
            currID_mx+=1
            nObjID = currID_mx
            #print nObjID
            cObjects.update({nObjID:trackedObject(objID=nObjID,xy=contour[1:3],boundBx=contour[3:],kID=contour[0])})

    #trObjects = cObjects.copy() #make a copy, since using del will alter a dict using iteration generator
    for key,tObj in trObjects.iteritems():
        if (not tObj.inFrame) & (tObj.lostFrames>10):
            del cObjects[key]

#def make_tObj(xy,kID,color):
#    """returns a named tuple of type tObj"""
#    if 'trackedObj' not in globals():
#        global trackedObj
#        trackedObj=namedtuple('trackedObj',['xy','kID','color','inFrame'],verbose=Falsep)
#    return trackedObj(xy=xy,kID=kID,color=color,inFrame=True) 

class trackedObject():
    """storage class for parameters associated with tracked objects"""
    def __init__(self,objID,kID,xy,boundBx):
        self.objID=objID
        self.kID=kID
        self.xy=xy
        self.boundBx = boundBx
        #self.color = tuple((np.random.random((3))*255).astype("int"))
        R,G,B = tuple(np.round(np.random.rand(3)*255))
        self.color = cv.RGB(R,G,B)
        self.inFrame=True
        self.lostFrames = 0
        self.fishProb = 0 #probability of being a fish!
