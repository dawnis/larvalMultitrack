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

txtlogfile = open("profileLastrun.txt",'w')
stats = pstats.Stats(logfile,stream=txtlogfile)
stats.sort_stats('time')
stats.print_stats()

stats_scrn_print = pstats.Stats(logfile)
stats.print_stats() #to show on screen as well
