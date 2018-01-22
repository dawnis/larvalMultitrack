from wxGUI_Classes import *
from scipy import all
import numpy as np
#import os
#import cv2.cv as cv

#abspath = os.path.abspath(__file__)
#dname = os.path.dirname(abspath)
#os.chdir(dname)
#bgimg=cv2.imread("C:\Users\Cornell\Dropbox\Python\larvalMultitrack\\tbgImg.png")
#bgimg=cv2.imread("tbgImg.png")
#bgimg = cv2.cvtColor(bgimg,cv.CV_RGB2GRAY)

app = wx.App(redirect=True)
frame = vFrame(None, 'Larvae Multi Tracker')
app.MainLoop()
