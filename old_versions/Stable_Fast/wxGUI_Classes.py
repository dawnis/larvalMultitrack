import wx
import cv2.cv as cv, cv2
import os, sys, re, time, cPickle, gc
from lm_functions import *
from videoControl_functions import *
from lMulti_IO import *

class vFrame(wx.Frame):
    TIMER_PLAY_ID=101
    TIMER_PROCESS_ID=201
    """window for video display"""
    def __init__(self, parent, title):
        self.dirname=''
        ###########################################Set Default Values and other permanent properties that need to be shared across functions
        SetImg_Globals((1000,1000))

        global GlProp
        cvCheckBoxDict={"BackgroundWindow":0,"LiveStream":1,"DifferenceWindow":2,"TrackWindow":3} #defines the index of each window in cFrame
        GlProp = GlobalProperty(TrackingThreshold=20, SizeThreshold=15., alpha=20, fps=1000., mDist = 20, bgRatio=5, cvCheckBoxDict=cvCheckBoxDict)
        #NOTES
        #alpha is in thousandths; the max value on the slider is 0.15

        global tObjList
        tObjList={} #ObjDictionary has {ObjID: tracked Obj} structure
        ############################################

        wx.Frame.__init__(self, parent, title=title, size=(1000,500))
        self.Panel = wx.Panel(self,-1,size=(1000,500))
        #self.bmp = wx.BitmapFromBuffer(img.shape[1],img.shape[0],img)
        #sbmp=wx.StaticBitmap(self,-1,bitmap=self.bmp)
        
        #menu
        filemenu=wx.Menu()
        f_open=filemenu.Append(wx.ID_OPEN, "&Open","Open a video file")
        self.Bind(wx.EVT_MENU,self.OnOpen,f_open) 

        f_liveacquire=filemenu.Append(wx.ID_ANY,"&Acquire Live!","Acquire Live Video Stream")
        self.Bind(wx.EVT_MENU,self.AcqLive,f_liveacquire)

        f_batchTracking=filemenu.Append(wx.ID_ANY, "Setup &Batch Tracking", "Batch Tracking Setup")
        self.Bind(wx.EVT_MENU,self.setupBatch,f_batchTracking)

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
        self.playctrlbuttons = []
        self.playctrlbuttons.append(iterFrameButt(self.Panel,"Play",1,True))
        self.playctrlbuttons.append(iterFrameButt(self.Panel,"Pause",1,False))
        self.playctrlbuttons.append(iterFrameButt(self.Panel,"Rewind",-1,True))
        for button in self.playctrlbuttons:
            self.PlayBackSizer.Add(button,1,wx.EXPAND)

        #Process Rate Display
        self.pRate = wx.StaticText(self.Panel,-1,"Processing Rate: 0 Hz")
        self.PlayBackSizer.Add(self.pRate,1,wx.EXPAND)
        
        #Button that generates output logfile
        self.trackButton = wx.Button(self.Panel,-1,"Track!")
        self.Bind(wx.EVT_BUTTON, self.onTrack, self.trackButton)
        #self.Bind(wx.EVT_BUTTON, lambda evt, vidN=GlProp.vidN : self.onTrack(evt,vidN), self.trackButton)
        self.PlayBackSizer.Add(self.trackButton,1,wx.EXPAND)
        bgUpdate_sLider, bgUpdateSl_obj = makeGl_Slider(self.Panel,GlProp.bgRatio,(1,120),"bgRatio","BG Update Ratio")
        self.PlayBackSizer.AddSpacer(25)
        self.PlayBackSizer.Add(bgUpdateSl_obj)

        #display checkboxes
        checkBxWindow=[]
        for cvWindow in GlProp.cvCB:
            checkBxWindow.append(cvWindowCheckBox(self.Panel,cvWindow,cvWindow))
            self.CBSizer.Add(checkBxWindow[-1])

#        #video input selector
#        Input_Types = ['File', 'Live Cam']
#        inSelector = wx.RadioBox(self.Panel,-1,"Video Input Selection",wx.DefaultPosition,wx.DefaultSize,
#                                 Input_Types,1,wx.RA_SPECIFY_COLS)
#        self.CBSizer.AddSpacer(15)
#        self.CBSizer.Add(inSelector,1,wx.EXPAND)

        #frame timer
        GlProp.frametimer = wx.Timer(self,self.TIMER_PLAY_ID)
        wx.EVT_TIMER(self,self.TIMER_PLAY_ID,self.onNextFrame)
        GlProp.processratetimer = wx.Timer(self,self.TIMER_PROCESS_ID)
        wx.EVT_TIMER(self,self.TIMER_PROCESS_ID,self.update_processRate)

        #selector controls for tracking parameters
        diffThrsh_slider, diffSlider_obj = makeGl_Slider(self.Panel,GlProp.trckThrsh,(2,255),"trckThrsh","Differencing Threshold")
        alpha_slider, alphaSlider_obj = makeGl_Slider(self.Panel,GlProp.alpha,(0,200),"alpha","BGUpdateValue")
        size_slider,sizeSlider_obj = makeGl_Slider(self.Panel,GlProp.szThrsh,(5,150),"szThrsh","Size Threshold")
        neighborhood_slider,neighborhoodSlider_obj = makeGl_Slider(self.Panel,GlProp.mDist,(5,75),"mDist","Tracking Neighborhood")
        self.SelSizer.Add(diffSlider_obj,1,wx.EXPAND)
        self.SelSizer.Add(neighborhoodSlider_obj,1,wx.EXPAND)
        self.SelSizer.Add(sizeSlider_obj,1,wx.EXPAND)
        self.SelSizer.Add(alphaSlider_obj,1,wx.EXPAND)
        
        trckParameterCBlist = []
        #trckParameterCBlist.append(trckParameterCheckBox(self.Panel,"Erosion"))
        #trckParameterCBlist.append(trckParameterCheckBox(self.Panel,"Dilation"))
        trckParameterCBlist.append(make_trckCB(self.Panel,"Erosion"))
        trckParameterCBlist.append(make_trckCB(self.Panel,"Dilation"))

        
        for CB in trckParameterCBlist:
            self.SelSizer.Add(CB)

        #output and error log
        self.log = wx.TextCtrl(self.Panel,wx.ID_ANY, size=(400,300), style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH2)
        redir=RedirectText(self.log) #from blog.pythonlibrary.org; redirecting stdout to log 
        sys.stdout=redir
        sys.stderr=redir
        sys.excepthook = log_uncaught_exceptions
        
        ############################################
        self.LayoutSizer.Add(self.PlayBackSizer)
        self.LayoutSizer.Add(self.CBSizer)
        self.LayoutSizer.Add(self.SelSizer)
        self.LayoutSizer.Add(self.log)

        #Sizers layout
        self.SetSizer(self.LayoutSizer)
        self.SetAutoLayout(1)
        self.LayoutSizer.Fit(self)

        self.Show(True)

    def onNextFrame(self,e):
        frPrStart = time.time()
        frameImg=[]
        frameImg.append(cFrame[:,:,0])#0
        #print [tObj.kID for tObj in tObjList.itervalues()]
        ret,frame=GetGSFrame(GlProp.vidstream)
        frameImg.append(frame)#1
        if len(GlProp.vidfile)>0:
            setpos=GlProp.vidstream.set(cv.CV_CAP_PROP_POS_FRAMES,GlProp.fIdx+GlProp.fDir)
            GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
        else:
            setpos=True
        if ret & setpos & (GlProp.fIdx+GlProp.fDir > -1):
            dFrame=CalculateBGDiff(cFrame[:,:,0],frame,GlProp.trckThrsh,GlProp.TrckParameter)
            frameImg.append(dFrame)#2
            CurContours = updateTracking(GlProp.fIdx,dFrame,minSize=GlProp.szThrsh,minDist=GlProp.mDist,currObjs=tObjList,trackData=GlProp.trackData)
            if GlProp.fIdx % GlProp.bgRatio == 0: #only update background if the frame # is a multiple of the bgRatio
                cFrame[:,:,0] = BGUpdateFnc(cFrame[:,:,0],frame,tObjList,CurContours,GlProp.alpha)
            if GlProp.cvCB["TrackWindow"]:
                frameImg.append(draw_tObjs(frame,CurContours,tObjList,GlProp.mDist))#3
            for cvWindow in GlProp.cvCB:
                if GlProp.cvCB[cvWindow]:
                    cv2.imshow(cvWindow,frameImg[GlProp.cvFrame[cvWindow]])
        else:
            GlProp.frametimer.Stop()
            GlProp.processratetimer.Stop()
            if GlProp.trackingON:
                self.stopTracking()
        GlProp.processRate = GlProp.processRate + np.array([1, time.time()-frPrStart])
        #sys.stderr.flush() #attempt to draw out error messages
        e.Skip()

    def onTrack(self,e):
        GlProp.frametimer.Stop()
        GlProp.processratetimer.Stop()
        GlProp.fDir=1
#        self.playctrlbuttons[0].Disable()
        self.playctrlbuttons[2].Disable()
#        for button in self.playctrlbuttons:
#            button.Disable()
        GlProp.vidstream=cv2.VideoCapture(self.dirname+'\\'+GlProp.vidfile[GlProp.vidN])
        setpos=GlProp.vidstream.set(cv.CV_CAP_PROP_POS_FRAMES,0) #rewind vid to beginning for analysis
        #logfile = self.dirname +"\\"+re.split('\.', GlProp.vidfile[vidN])[0]+".pickle"
        GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
        #GlProp.output = open(logfile,'wb')
        GlProp.trackingON = True
        tObjList.clear() #prevents data from pre-track button hit to go in
        GlProp.trackData.clear()
        gc.collect()
        print "Tracking "+GlProp.vidfile[GlProp.vidN]+" ..."
#        ret,frame1GS = GetGSFrame(GlProp.vidstream)
#        cFrame[:,:,0] = frame1GS#background updated for each track on batch tracking
        GlProp.frametimer.Start(1000./GlProp.fps)
        GlProp.processratetimer.Start(500.)
        
    def stopTracking(self):
        GlProp.frametimer.Stop()
        GlProp.processratetimer.Stop()
        GlProp.trackingON = False
        trckParameters = {"Contrast_Difference_Threshold":GlProp.trckThrsh,
                          "MinimumSize":GlProp.szThrsh,
                          "BackgroundUpdateAlpha":GlProp.alpha/1000.,
                          "NeighborDistance":GlProp.mDist,
                          "ImageProcessing":GlProp.TrckParameter}
        writeMatlab(GlProp.trackData,trckParameters,self.dirname+'\\'+'mtD_'+os.path.splitext(GlProp.vidfile[GlProp.vidN])[0]+".mat")
        print "done saving data for "+GlProp.vidfile[GlProp.vidN]
        #cPickle.dump(GlProp.trackData,GlProp.output,-1)
        #tObjList.clear()
        #GlProp.trackData.clear()
        #gc.collect()
        for button in self.playctrlbuttons:
            button.Enable()
        if GlProp.vidN+1 < len(GlProp.vidfile):
            GlProp.vidN += 1
            self.onTrack(None)
        else:
            GlProp.vidN = 0

    def update_processRate(self,e):
        processRate = GlProp.processRate[0]/GlProp.processRate[1]
        GlProp.processRate = np.array([0.,0.])
        self.pRate.SetLabel("Process rate: %2.2f Hz" % processRate)

    def OnExit(self,e):
        cv.DestroyAllWindows()
        GlProp.frametimer.Stop()
        self.Close(True)

    def AcqLive(self,e):
        """currently data is not saved, as fIdx always is 0 in trackData; only new IDs get generated"""
        GlProp.vidstream = cv2.VideoCapture(-1)
        if GlProp.vidstream.isOpened():
            print "Video Stream is Open"
        GlProp.fps = 30.
        GlProp.fIdx = 0
        ret,frame1GS = GetGSFrame(GlProp.vidstream)
        SetImg_Globals(frame1GS.shape)
        cFrame[:,:,0] = frame1GS
        GlProp.vidfile = []
        #self.filename = ''

    def OnOpen(self,e):
        """ choose a video file and load first frame"""
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            GlProp.vidfile = []
            GlProp.vidfile.append(dlg.GetFilename())
            GlProp.vidN = 0
            print "Video File: "+GlProp.vidfile[0]
            self.dirname = dlg.GetDirectory()
            GlProp.vidstream=cv2.VideoCapture(self.dirname+'\\'+GlProp.vidfile[0])
            GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
            GlProp.fps = 1000.
            ret,frame1GS = GetGSFrame(GlProp.vidstream)
            #ret,frame1 = GlProp.vidstream.read()
            SetImg_Globals(frame1GS.shape)
            #frame1GS = cv2.cvtColor(frame1,cv.CV_RGB2GRAY)
            cFrame[:,:,0] = frame1GS
            #cFrame[:,:,1] = frame1GS.copy()
            #sbmp=wx.StaticBitmap(self,-1,bitmap=self.bmp)
            self.Refresh()
        dlg.Destroy()

    def setupBatch(self,e):
        """Selects a directory containing multiple videos to track"""
        dlg = wx.DirDialog(self,"Select directory containing sequential video files:",
                            style = wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname = dlg.GetPath()
            print "Batch Tracking Set for Directory: "+self.dirname
            GlProp.vidfile = [file for file in os.listdir(self.dirname) if file.endswith(".avi")]
            print '\n'.join(GlProp.vidfile)        
            GlProp.vidstream=cv2.VideoCapture(self.dirname+'\\'+GlProp.vidfile[0])
            GlProp.fIdx = GlProp.vidstream.get(cv.CV_CAP_PROP_POS_FRAMES)
            GlProp.fps = 1000.
            GlProp.vidN = 0
            ret,frame1GS = GetGSFrame(GlProp.vidstream)
            if frame1GS.shape != cFrame.shape[0:2]:
                SetImg_Globals(frame1GS.shape)
                cFrame[:,:,0] = frame1GS
            else:
                print("Remember to set BG conditions before tracking...")
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

def make_trckCB(parent,ParameterName):
    """returns a sizer object with a track parameter checkbox and a choice array with 1 or 2 iterations"""
    trckCB_sizer = wx.BoxSizer(wx.HORIZONTAL)
    trckCB_handle = trckParameterCheckBox(parent,ParameterName)
    trckCB_choicebx = trckParameterComboBox(parent,ParameterName)
    trckCB_sizer.Add(trckCB_handle)
    trckCB_sizer.Add(trckCB_choicebx)
    return trckCB_sizer

class trckParameterComboBox(wx.ComboBox):
    """Combo box having two choice, iterate 1 or 2, which determines the value of trckParameter of a given name"""
    def __init__(self,parent,ParameterName):
        wx.ComboBox.__init__(self,parent=parent,id=wx.ID_ANY,value="Iterate 1",choices=["Iterate 1", "Iterate 2", "Iterate 3"], style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, lambda evt,ParameterName=ParameterName : self.EvtComboBox(evt,ParameterName))

    def EvtComboBox(self,e,ParameterName):
        cb = e.GetEventObject()
        if GlProp.TrckParameter[ParameterName]>0:
            GlProp.TrckParameter[ParameterName] = cb.GetSelection()+1
        #print GlProp.TrckParameter[ParameterName]

class trckParameterCheckBox(wx.CheckBox):
    """trckParameterCheckBox(self,ParameterName)
    Default true checkboxes which tell the background differencing function whether or not to use the parameter"""
    def __init__(self,parent,ParameterName):
        wx.CheckBox.__init__(self,parent=parent,id=wx.ID_ANY,label=ParameterName)
        GlProp.TrckParameter.update({ParameterName:True})
        self.SetValue(True)
        self.Bind(wx.EVT_CHECKBOX, lambda evt,ParameterName=ParameterName : self.EvtCheckBox(evt,ParameterName))

    def EvtCheckBox(self,e, ParameterName):
        cb = e.GetEventObject()
        GlProp.TrckParameter[ParameterName] = cb.GetValue()

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
        e.Skip() #skip is used to search for further handlers for this event

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
    def __init__(self, TrackingThreshold, SizeThreshold, alpha, fps, mDist, bgRatio, cvCheckBoxDict):
        self.trckThrsh=TrackingThreshold
        self.szThrsh=SizeThreshold
        self.processRate = np.zeros(2,dtype=float) #frame processing rate [nCycles, elapsedTime]
        self.bgRatio = bgRatio #1:x ratio of bg frame update
        self.fIdx = 0 #frame index
        self.fDir = 1 #play direction
        self.cvCB = {CheckBoxName:0 for CheckBoxName in cvCheckBoxDict}
        self.cvFrame = cvCheckBoxDict
        self.alpha = alpha
        self.fps = fps
        self.mDist = mDist #minimum tracking distance
        self.vidstream = []
        self.vidfile = [] #can be one file for single video, or a list for tracking
        self.vidN = 0 #which video is currently tracked
        self.frametimer = []
        self.processratetimer = []
        #self.output = []
        self.trackingON = False
        self.TrckParameter = {} #keeps track of whether erosion and dilation are checked
        self.trackData = {} #track data is a dictionary with structure ObjID:np.array([9000,2],dtype=float)

def SetImg_Globals((width,height)):
    """Defines globals for containing the frames"""
    global cFrame
    cFrame = np.empty((width,height,4),dtype="uint8")
    #SetLmFnc_Globals((width,height))
