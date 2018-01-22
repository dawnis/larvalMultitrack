#Generates cProfile log of larvalMultitrack runtime
import os, cProfile
from wxGUI_Classes import *
import pstats

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

logfile = "larvalMultitrack.profile"
program = open("larvalMultitrack_main.py")
#app = wx.App(False)
#frame = vFrame(None, 'Larvae Multi Tracker -- Profiling Run')
cProfile.run(program,logfile)

stats = pstats.Stats(logfile)
stats.print_stats()
