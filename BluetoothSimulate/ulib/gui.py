'''
Created on Apr 6, 2017

@author: Matthew Muresan

This is a simple Tkinter app that loads two images and displays them. It re-loads the image every second.
'''

import tkinter as tk
import tkinter.ttk as ttk
import os
import png
import numpy
from PIL import Image, ImageTk

from ulib import vissimconnect
from ulib import learning
#from ulib import learning

import numpy as np

import threading
import queue

from msilib import Control
import matplotlib.pyplot as plt
from ulib.learning import GradientDescentSelectTime



class VissimThread(threading.Thread):
    def __init__(self, foname, guiQ, guiQLock, startDay, resetDay, detectorfile, populatesteps=500):
        threading.Thread.__init__(self)
        
        self.guiQ = guiQ
        self.guiQLock = guiQLock
        self.foname = foname
        self.populatesteps = populatesteps
        self.startDay = startDay
        self.resetDay = resetDay
        self.detectorfile = detectorfile
        
        self.start()
    
    def run(self):
        self.VissimControl = None 
        try:
            self.VissimControl = vissimconnect.VissimConnect(self.foname, self.detectorfile, self.populatesteps) #main class to interact with VISSIM. See imported ulib/vissimconnect.
            self.VissimControl.Data.ActivateSignals(self.VissimControl.Vissim, self.VissimControl.step) #activate the signals which we are controlling.
            self.Optimiser = GradientDescentSelectTime(self.VissimControl)
            #learning.runLearning(self.VissimControl, self.guiQ, self.guiQLock, self.startDay, self.resetDay)
            
            i = 1
            STEPS = 99999999
            WRITELOC = "out/"
            ACTIONINTERVAL = 25000
            ACTIONMODE = 1 #two actions only for the learning signal control
            while i < STEPS:
                self.VissimControl.advanceSimulation()
                ActionsAllowed = self.VissimControl.ActionsAllowed(ACTIONMODE)
                if 1 in ActionsAllowed:
                    self.VissimControl.doAction(1) #advance the signals.
                if i % ACTIONINTERVAL == 0:
                    #times = self.VissimControl.Data
                    self.VissimControl.restartSimulation()
                    NB_time = self.VissimControl.Data.Signals[1].RBCLogicControl.TimingRules["MinGreens"][6]
                    WB_time = self.VissimControl.Data.Signals[1].RBCLogicControl.TimingRules["MinGreens"][8]
                    times = self.Optimiser.SelectSplit(i, WRITELOC, NB_time, WB_time)
                    self.VissimControl.Data.Signals[1].RBCLogicControl.TimingRules["MinGreens"][6] = times[0]
                    self.VissimControl.Data.Signals[1].RBCLogicControl.TimingRules["MinGreens"][2] = times[0]
                    self.VissimControl.Data.Signals[1].RBCLogicControl.TimingRules["MinGreens"][8] = times[1]
                    self.VissimControl.Data.Signals[1].RBCLogicControl.TimingRules["MinGreens"][4] = times[1]
                    self.Optimiser.DumpPerformanceMeasures(WRITELOC)
                    
                if i % 250 == 0:
                    print("Step " + str(i) + " completed")
                    
                i += 1
            
            print("Program End... dumping records...")
            self.VissimControl.Data.DumpRecords(WRITELOC)
            self.VissimControl.Data.DumpDirectionalTT(WRITELOC)
        
        except:
            raise
        finally:
            if (self.VissimControl != None and self.VissimControl.Vissim != None):
                self.VissimControl.Vissim.Exit() #exit vissim after everything.
'''
Default GUI class,
foname is the location of the vissim file,
mode is for the GUI to show or not show the debug tools
startDay tells the algorithm which day to encode into the matrix when vissim starts
resetDay tells the algorithm which day to reset the timer at
Days are order as 0 = Monday... 6 = Sunday
Day is calculated using mod(resetDay), so resetDay should be one greater than the day you want (6 mod 7 = 6, 7 mod 7 = 0)
'''
class TkinterGUI(object):
    def __init__(self, foname, detectorfile, writeloc, mode="debug", startDay=0, resetDay=7):
        self.guiQ = queue.Queue(1)
        self.guiQLock = threading.Lock()
        self.mode = mode
        
        self.dataFileHeaderWritten = False
        
        self.logFile = "logs_" + "vissim" + "/results.txt"
        try:
            os.remove(self.logFile) #erase old file if there
        except:
            pass
        
        
        self.MainWindow = tk.Tk()
        self.MainWindow.title("Display VISSIM Interact")
        
        self.notetiming = ttk.Label(self.MainWindow, text="Corridor Signal Timing", justify=tk.CENTER, padding=(5,5,5,0), font=(None, 15))
        self.notetiming.grid(row=1, column=1, columnspan = 2, rowspan = 1)
        self.canvas_timing = tk.Canvas(self.MainWindow, width=300, height=20)
        self.canvas_timing.grid(row=2, column=1, columnspan = 2, rowspan = 1, sticky=(tk.W), padx=10, pady=0)
        
        self.corridor_green_lab = ttk.Label(self.MainWindow, text="Corridor Last Green:", justify=tk.RIGHT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_green_lab.grid(row=3, column=1, columnspan = 1, rowspan = 1, sticky=(tk.E))
        self.corridor_green_time = ttk.Label(self.MainWindow, text="10 s", justify=tk.LEFT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_green_time.grid(row=3, column=2, columnspan = 1, rowspan = 1, sticky=(tk.W))
        
        self.corridor_red_lab = ttk.Label(self.MainWindow, text="Corridor Last Red:", justify=tk.RIGHT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_red_lab.grid(row=4, column=1, columnspan = 1, rowspan = 1, sticky=(tk.E))
        self.corridor_red_time = ttk.Label(self.MainWindow, text="10 s", justify=tk.LEFT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_red_time.grid(row=4, column=2, columnspan = 1, rowspan = 1, sticky=(tk.W))
       
        self.notegraph = ttk.Label(self.MainWindow, text="System Average Delay", justify=tk.CENTER, padding=(5,5,5,0), font=(None, 15))
        self.notegraph.grid(row=11, column=1, columnspan = 2, rowspan = 1)
        self.canvas_figure = tk.Canvas(self.MainWindow, width=300, height=300)
        self.canvas_figure.grid(row=12, column=1, columnspan = 2, rowspan = 1, sticky=(tk.W), padx=10, pady=0)
        
        self.corridor_NBQ = ttk.Label(self.MainWindow, text="EB Queue:", justify=tk.RIGHT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_NBQ.grid(row=13, column=1, columnspan = 1, rowspan = 1, sticky=(tk.E))
        self.corridor_NBQLen = ttk.Label(self.MainWindow, text="10 veh", justify=tk.LEFT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_NBQLen.grid(row=13, column=2, columnspan = 1, rowspan = 1, sticky=(tk.W))
        
        self.corridor_SBQ = ttk.Label(self.MainWindow, text="WB Queue:", justify=tk.RIGHT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_SBQ.grid(row=14, column=1, columnspan = 1, rowspan = 1, sticky=(tk.E))
        self.corridor_SBQLen = ttk.Label(self.MainWindow, text="10 veh", justify=tk.LEFT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_SBQLen.grid(row=14, column=2, columnspan = 1, rowspan = 1, sticky=(tk.W))
        
        self.corridor_EBQ = ttk.Label(self.MainWindow, text="NB Queue:", justify=tk.RIGHT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_EBQ.grid(row=15, column=1, columnspan = 1, rowspan = 1, sticky=(tk.E))
        self.corridor_EBQLen = ttk.Label(self.MainWindow, text="10 veh", justify=tk.LEFT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_EBQLen.grid(row=15, column=2, columnspan = 1, rowspan = 1, sticky=(tk.W))
        
        self.corridor_WBQ = ttk.Label(self.MainWindow, text="SB Queue:", justify=tk.RIGHT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_WBQ.grid(row=16, column=1, columnspan = 1, rowspan = 1, sticky=(tk.E))
        self.corridor_WBQLen = ttk.Label(self.MainWindow, text="10 veh", justify=tk.LEFT, padding=(0,0,0,0), font=(None, 13))
        self.corridor_WBQLen.grid(row=16, column=2, columnspan = 1, rowspan = 1, sticky=(tk.W))
        
        if self.mode == "debug":
            self.notematrix = ttk.Label(self.MainWindow, text="System State", justify=tk.CENTER, padding=(5,5,5,0), font=(None, 15))
            self.notematrix.grid(row=11, column=11, columnspan = 2, rowspan = 1)
            self.canvas = tk.Canvas(self.MainWindow, width=300, height=300)
            self.canvas.grid(row=12, column=11, columnspan = 2, rowspan = 1, sticky=(tk.W), padx=10, pady=0)
        

        
        
        matrix = numpy.zeros([80,80]) 
        png.from_array(matrix, 'L', {"bitdepth":1}).save("matrix.png")
        
        matrix = numpy.zeros([80,80]) 
        png.from_array(matrix, 'L', {"bitdepth":1}).save("figure.png")
        
        matrix = numpy.zeros([5,250]) 
        png.from_array(matrix, 'L', {"bitdepth":1}).save("timing.png")
        
        self.updateMatrixImage()
        self.startWorkThreads(foname, startDay, resetDay, detectorfile)
        
        self.MainWindow.resizable(width=False, height=False)
        self.MainWindow.mainloop()
            
    def startWorkThreads(self, foname, startDay, resetDay, detectorfile):
        self.VissimThread = VissimThread(foname, self.guiQ, self.guiQLock, startDay, resetDay, detectorfile)
    
    def checkQueue(self):
        test1 = self.guiQ.empty()
        if not self.guiQ.empty() and self.guiQLock.acquire(blocking=False):
            data = self.guiQ.get()
            self.guiQLock.release() #release the lock.
            self._saveMatrixToImage(data["matrix"]) #matrix image
            
            timing = np.zeros([5,250,3])
            EBG = 0 if not "EB_LG" in data else data["EB_LG"]
            NBG = 0 if not "NB_LG" in data else data["NB_LG"]
            
            self.corridor_green_time["text"] = EBG
            self.corridor_red_time["text"] = NBG
            
            #build timing image
            for x in range (0, 250):
                if  x < EBG: 
                    timing[0,x,1] = 1
                    timing[1,x,1] = 1
                    timing[2,x,1] = 1
                    timing[3,x,1] = 1
                    timing[4,x,1] = 1
                elif x <= EBG + 3:
                    timing[0,x,2] = 1
                    timing[1,x,2] = 1
                    timing[2,x,2] = 1
                    timing[3,x,2] = 1
                    timing[4,x,2] = 1
                elif x <= EBG + NBG + 3:
                    timing[0,x,0] = 1
                    timing[1,x,0] = 1
                    timing[2,x,0] = 1
                    timing[3,x,0] = 1
                    timing[4,x,0] = 1
                elif x <= EBG + NBG + 6:
                    timing[0,x,2] = 1
                    timing[1,x,2] = 1
                    timing[2,x,2] = 1
                    timing[3,x,2] = 1
                    timing[4,x,2] = 1
            png.from_array(timing, 'RGB', {"bitdepth":1}).save("timing.png") #signal timing image   
            self._savePlotToImg(data["DelayAvg"])
            
            self.corridor_NBQLen["text"] = int(data["NB_QUEUE"])
            self.corridor_SBQLen["text"] = int(data["SB_QUEUE"])
            self.corridor_EBQLen["text"] = int(data["EB_QUEUE"])
            self.corridor_WBQLen["text"] = int(data["WB_QUEUE"])
            
            #save data to logfile
            del data["matrix"] #we don't want to save the matrix
            #del data["DelayAvg"] #don't save historical delay
            with open(self.logFile, "a") as a_file:
                if not self.dataFileHeaderWritten:
                    for key in sorted(data):
                        a_file.write(str(key) + ",")
                    self.dataFileHeaderWritten = True
                    a_file.write("\n")
                for key in sorted(data):
                    a_file.write(str(data[key]) + ",")
                a_file.write("\n")
            
    
    def updateMatrixImage(self):
        self.checkQueue() #check for updates
        try:            
            self.img_timing = Image.open("timing.png", "r")
            self.img_timing = self.img_timing.resize((300, 20), Image.ANTIALIAS)
            self.tk_img_timing = ImageTk.PhotoImage(self.img_timing)
            self.canvas_timing.create_image(0,0, image=self.tk_img_timing, anchor=tk.NW)
            
            self.img_figure = Image.open("figure.png", "r")
            self.img_figure = self.img_figure.resize((300, 300), Image.ANTIALIAS)
            self.tk_img_figure = ImageTk.PhotoImage(self.img_figure)
            self.canvas_figure.create_image(0,0, image=self.tk_img_figure, anchor=tk.NW)
            
            if self.mode == "debug":
                self.img = Image.open("matrix.png", "r")
                self.img = self.img.resize((300, 300), Image.ANTIALIAS)
                self.tk_img = ImageTk.PhotoImage(self.img)
                self.canvas.create_image(0,0, image=self.tk_img, anchor=tk.NW)
        except:
            return
        finally:
            self.MainWindow.after(1000, self.updateMatrixImage)
            
    
    #keyfactor is the factor used to convert the key (in this case from quarter hours to minutes)
    def _savePlotToImg(self, data, key_factor_mins=15):
        x = []
        y = []
        for key in sorted(data):
            key_val = key * key_factor_mins
            key_val /= 60 #convert to hours
            x.append(key_val)
            y.append(data[key])
        
        plt.clf()
        plt.xlabel("Hours since Simulation Start (h)")
        plt.ylabel("Average Delay per Vehicle (mins)")
        plt.plot(x, y, '-o')
        plt.savefig("figure.png")
    
    def _saveMatrixToImage(self, matrix):
    #matrix *= 255
        #Update GUI
        png.from_array(matrix, 'L', {"bitdepth":1}).save("matrix.png")
