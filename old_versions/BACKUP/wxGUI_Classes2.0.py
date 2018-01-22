import wx
import cv2.cv as cv, cv2
import time
from lm_functions import *
from videoControl_functions import *

class vFrame(wx.Frame):
    TIMER_PLAY_ID=101
    TIMER_PROCESS_ID=201
    """window for video display"""
    def __init__(self, parent, title):
        self.dirname=''
        ###########################################Set Default Values and other permanent properties that need to be shared across functions
        SetImg_Globals((1000,1000))

        global GlProp
        cvCheckBoxDict={"BackgroundWindow":0,"LiveStream":1,"DifferenceWindow":2,"TrackWindow":[3,4,5]} #defines the index of each window in cFrame
        GlProp = GlobalProperty(TrackingThreshold=20, SizeThreshold=1., alpha=50, fps=1000., neighborDist = 10, cvCheckBoxDict=cvCheckBoxDict)
        #NOTES
        #alpha is in thousandths; the max value on the slider is 0.15

        global tObjList
        tObjList={} #ObjDictionary has {ObjID: tracked Obj} structure
        ############################################

        wx.Frame.__init__(self, parent, title=title, size=(400,600))
        self.Panel = wx.Panel(self,-1,size=(400,600))
        #self.bmp = wx.BitmapFromBuffer(img.shape[1],img.shape[0],img)
        #sbmp=wx.StaticBitmap(self,-1,bitmap=self.bmp)
        
        #menu
        filemenu=wx.Menu()
        f_open=filemenu.Append(wx.ID_OPEN, "&Open","Open a video file")
        self.Bind(wx.EVT_MENU,self.OnOpen,f_open) 
        f_exit=filemenu.Append(wx.ID_EXIT,"E&xit","Exit Program")
        self.Bind(wx.EVT_MENU,self.OnExit,f_exit)
        #menubar
        menuBar=wx.MenuBar()
        menuBar.Append(filemenu,"&File")
        self.SetMenuBar(menuBar)
        
        ############################################Panel Controls Code
        #positioning of buttons and button generation
        self.LayoutSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.PlayBackSizer = wx.BoxSizer(wx.VERTICAL)
        self.CBSizer = wx.BoxSizer(wx.VERTICAL) 
        self.SelSizer = wx.BoxSizer(wx.VERTICAL)

        #buttons
        playctrlbuttons = []
        playctrlbuttons.append(iterFrameButt(self.Panel,"Play",1,True))
        playctrlbuttons.append(iterFrameButt(self.Panel,"Pause",1,False))
        playctrlbuttons.append(iterFrameButt(self.Panel,"Rewind",-1,True))
        for button in playctrlbuttons:
            self.PlayBackSizer.Add(button,1,wx.EXPAND)

        #display checkboxes
        checkBxWindow=[]
        for cvWindow in GlProp.cvCB:
            checkBxWindow.append(cvWindowCheckBox(self.Panel,cvWindow,cvWindow))
            self.CBSizer.Add(checkBxWindow[-1])

        #frame timer
        GlProp.frametimer = wx.Timer(self,self.TIMER_PLAY_ID)
        wx.EVT_TIMER(self,self.TIMER_PLAY_ID,self.onNextFrame)
        GlProp.processratetimer = wx.Timer(self,self.TIMER_PROCESS_ID)
        wx.EVT_TIMER(self,self.TIMER_PROCESS_ID,self.update_processRate)

        #Process Rate Display
        self.pRate = wx.StaticText(self.Panel,-1,"Processing Rate: 0 Hz")
        self.PlayBackSizer.Add(self.pRate,1,wx.EXPAND)

        #slider selector controls for tracking parameters
        diffThrsh_slider, diffSlider_obj = makeGl_Slider(self.Panel,GlProp.trckThrsh,(0,255),"trckThrsh","Differencing Threshold")
        alpha_slider, alphaSlider_obj = makeGl_Slider(self.Panel,GlProp.alpha,(0,200),"alpha","BGUpdateValue")
        size_slider,sizeSlider_obj = makeGl_Slider(self.Panel,GlProp.szThrsh,(0,10),"szThrsh","Size Threshold")
        self.SelSizer.Add(diffSlider_obj,1,wx.EXPAND)
        self.SelSizer.Add(alphaSlider_obj,1,wx.EXPAND)
        self.SelSizer.Add(sizeSlider_obj,1,wx.EXPAND)

        ############################################
        self.LayoutSizer.Add(self.PlayBackSizer)
        self.LayoutSizer.Add(self.CBSizer)
        self.LayoutSizer.Add(self.SelSizer)

        #Sizers layout
        self.SetSizer(self.LayoutSizer)
        self.SetAutoLayout(1)
        self.LayoutSizer.Fit(self)

        self.Show(True)

    def onNextFrame(self,e):
        frPrStart = time.time()
        #print [tObj.kID for tObj in tObjList.itervalues()]
        #ret,frame=GlProp.vidstream.read()
        ret,frame=GetGSFrame(GlProp.vidstream)
        #print GlProp.fIdx
        setpos=GlProp.vidstream.set(cv.CV_CAP_PROP_POS_FRAMES,GlProp.fIdx+GlProp.fDir)
        GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
        if ret & setpos:
            cFrame[:,:,GlProp.cvFrame["LiveStream"]] = frame
            cFrame[:,:,GlProp.cvFrame["BackgroundWindow"]] = BGUpdateFnc(cFrame[:,:,0],cFrame[:,:,1],GlProp.alpha)
            cFrame[:,:,GlProp.cvFrame["DifferenceWindow"]]=CalculateBGDiff(cFrame[:,:,0],cFrame[:,:,1],GlProp.trckThrsh)
            CurContours = updateTracking(cFrame[:,:,2],minSize=GlProp.szThrsh,minDist=50.,currObjs=tObjList)
            #if GlProp.cvCB["TrackWindow"]:
            cFrame[:,:,GlProp.cvFrame["TrackWindow"]] = draw_tObjs(cFrame[:,:,1],CurContours,tObjList,GlProp.neighborDist)
            #cv2.imshow("trackFrame",trackFrame)
            for cvWindow in GlProp.cvCB:
                if GlProp.cvCB[cvWindow]:
                    cv2.imshow(cvWindow,cFrame[:,:,GlProp.cvFrame[cvWindow]])
        #if (not ret) | (GlProp.fIdx == 0):
        else:
            GlProp.frametimer.Stop()
        GlProp.processRate = GlProp.processRate + np.array([1, time.time()-frPrStart])
        e.Skip()

    def update_processRate(self,e):
        processRate = GlProp.processRate[0]/GlProp.processRate[1]
        GlProp.processRate = np.array([0.,0.])
        self.pRate.SetLabel("Process rate: %2.2f Hz" % processRate)

    def OnExit(self,e):
        cv.DestroyAllWindows()
        GlProp.frametimer.Stop()
        self.Close(True)

    def OnOpen(self,e):
        """ choose a video file and load first frame"""
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            GlProp.vidstream=cv2.VideoCapture(self.dirname+'\\'+self.filename)
            GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
            ret,frame1GS = GetGSFrame(GlProp.vidstream)
            #ret,frame1 = GlProp.vidstream.read()
            SetImg_Globals(frame1GS.shape)
            #frame1GS = cv2.cvtColor(frame1,cv.CV_RGB2GRAY)
            cFrame[:,:,0] = frame1GS
            cFrame[:,:,1] = frame1GS.copy()
            #sbmp=wx.StaticBitmap(self,-1,bitmap=self.bmp)
            self.Refresh()
        dlg.Destroy()

class cvWindowCheckBox(wx.CheckBox):
    """cvWindowCheckbox(self,checkbox_label, cvWindowName)
    a checkbox that opens an opencv new window and returns the name chLabel is passsed in as the label"""
    #global GlProp
    def __init__(self, parent, label, chLabel):
        chb=wx.CheckBox.__init__(self,parent=parent,id=wx.ID_ANY,label=label)
        self.Bind(wx.EVT_CHECKBOX,lambda evt, label=chLabel : self.EvtCheckBox(evt,label))

    def EvtCheckBox(self,e,chLabel):
        """creates window when checked, destroys it when unchecked"""
        for cvWindow in GlProp.cvCB:
            if cvWindow is chLabel:
                GlProp.cvCB[cvWindow]=e.IsChecked()
        if e.IsChecked():
            cv2.namedWindow(chLabel)
            cv2.imshow(chLabel,cFrame[:,:,GlProp.cvFrame[chLabel]])
        else:
            cv.DestroyWindow(chLabel)

class iterFrameButt(wx.Button):
    """iterFrameButt(parent,label,iterDir,startTimer)
    play,pause,rewind button"""
    def __init__(self, parent, label, iterDir, startTimer):
        wx.Button.__init__(self, parent=parent, id=wx.ID_ANY, label=label)
        self.Bind(wx.EVT_BUTTON, lambda evt, iterDir=iterDir, stT=startTimer : self.BtnFncn(evt,iterDir,stT))

    def BtnFncn(self,e,iterDir,stT):
        GlProp.processratetimer.Stop()
        GlProp.frametimer.Stop()
        GlProp.fDir = iterDir
        if stT:
            GlProp.frametimer.Start(1000./GlProp.fps)
            GlProp.processratetimer.Start(500.)
        #e.skip() #skip is used to search for further handlers for this event

def makeGl_Slider(parent,defaultValue,(minVal,maxVal),GlProp2Set,slider_name):
    """Returns a sizer object containing a slider label and a slider that controls a given property."""
    slider_sizer = wx.BoxSizer(wx.VERTICAL)
    slider_label = wx.StaticText(parent,-1,slider_name)
    slider_handle = setGlProp_Slider(parent,defaultValue,(minVal,maxVal),GlProp2Set,slider_name)
    slider_sizer.Add(slider_label)
    slider_sizer.Add(slider_handle)
    return slider_handle,slider_sizer

class setGlProp_Slider(wx.Slider):
    """Generates a slider element that sets an item in GlProp"""
    def __init__(self,parent, defaultValue, (minVal,maxVal), GlProp2Set, slider_name):
        wx.Slider.__init__(self,parent=parent,id=wx.ID_ANY, 
                           value=defaultValue,minValue=minVal,maxValue=maxVal,pos=(-1,-1),size=(-1,-1),
                           style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS,
                           name=slider_name)
        self.Bind(wx.EVT_SCROLL_CHANGED,lambda evt, setProp=GlProp2Set: self.AdjustProperty(evt,setProp))
        self.SetTickFreq(maxVal/10,1)

    def AdjustProperty(self,e,setProp):
        setattr(GlProp,setProp,e.EventObject.GetValue())

class GlobalProperty:
    """A class structure for storing global parameters in the GUI. Note that cvCheckBoxDictionary is a dictionary of the checkboxname and the global image frame variable corresponding to each opencv window"""
    def __init__(self, TrackingThreshold, SizeThreshold, alpha, fps, neighborDist, cvCheckBoxDict):
        self.trckThrsh=TrackingThreshold
        self.szThrsh=SizeThreshold
        self.processRate = np.zeros(2,dtype=float) #frame processing rate [nCycles, elapsedTime]
        self.fIdx = 0 #frame index
        self.fDir = 1 #play direction
        self.cvCB = {CheckBoxName:0 for CheckBoxName in cvCheckBoxDict}
        self.cvFrame = cvCheckBoxDict
        self.alpha = alpha
        self.fps = fps
        self.neighborDist = neighborDist
        self.vidstream = []
        self.frametimer = []
        self.processratetimer = []

def SetImg_Globals((width,height)):
    """Defines globals for containing the frames"""
    global cFrame
    cFrame = np.empty((width,height,6),dtype="uint8")
    #SetLmFnc_Globals((width,height))
