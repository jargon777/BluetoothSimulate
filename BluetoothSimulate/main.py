'''
Created on Aug 30, 2017

@author: Matthew Muresan

Main script file. This file organizes and uses the various modules we will develop
'''

VISSIMFILE = "viss/1.inpx"

#VISSIM REQUIRED IMPORTS
import win32com.client as com
import pythoncom

#OTHER IMPORTS
import os
import json
import math
import random

VISSIMFILE = "viss/1.inpx"
WRITELOC = "out/"
POPULATESTEPS = 1000
DETECTORFILE = "detectors.json"
STEPS = 37000
BACKUPSTEPS = 99999

def main():
    print("Main Loop Running...")
    VissimControl = VissimConnect(VISSIMFILE, POPULATESTEPS) #main class to interact with VISSIM. See imported ulib/vissimconnect.
    print("  ...Done.")
    print("Running Loop Forever")
    i = 0
    try:
        while i < STEPS:
            VissimControl.advanceSimulation()
            if i % BACKUPSTEPS == 0:
                VissimControl.Data.DumpRecords()
                VissimControl.Data.DumpDirectionalTT()
            
            if i % 250 == 0:
                print("Step " + str(i) + " completed")
                
            i += 1
    except:
        raise
    finally:
        print("Program End... dumping records...")
        VissimControl.Data.DumpRecords()
        VissimControl.Data.DumpDirectionalTT()
        

class MessageRelay(object):
    def __init__(self):
        pass
    def StatusUpdate(self, message):
        print(message)

class VissimConnect(object):
    def __init__(self, foname, populatesteps=0):
        pythoncom.CoInitialize()
        self.MessageRelay = MessageRelay() #console interaction
        self.Vissim = None #Variable which will house the COM that interfaces with Vissim
        self.populateSteps = populatesteps #The number of steps we want VISSIM to run before we begin observing vehicles. Vissim starts with no vehicles on the network, this time allows cars to enter.
        self.step = 0 #current time-step. Each time we advance the simulation one step, VISSIM does calculations. By default, 1 step = 0.2 simulated seconds.
        self.startVissim(foname) #open vissim, opening the *.inpx file at foname
        self.actingInterval = 5 #polling through com is slow. This setting sets it to poll VISSIM every simulated second.
        self.Data = NetworkData(self.MessageRelay) #create the class that will house the data.
        
    #function that loads VISSIM. After loading VISSIM, it starts runs a function to populate the network for the steps saved before.
    def startVissim(self, foname):
        foname = os.path.abspath(foname) #convert the relative path into an absolute one
        
        self.Vissim = com.Dispatch("Vissim.Vissim.700") #open Vissim (program)
        self.Vissim.LoadNet(foname) #load the specified .inpx file
        self.Vissim.SaveNetAs(foname) #configure where to save VISSIM diagnostics (requireD)
        self.MessageRelay.StatusUpdate("Vissim Loaded")
        
        self.MessageRelay.StatusUpdate("Populating VISSIM with Cars by running some steps")   
        self._populateVissim() #Populate the network
        self.MessageRelay.StatusUpdate("Done.")
        
    #Vissim starts with an empty network, this (private) function fills the network with cars..
    #Runs the number of steps requested 
    def _populateVissim(self):
        while (self.step <= self.populateSteps):
            self.step += 1
            self.Vissim.Simulation.RunSingleStep()
    
    #main function that retrieves data from VISSIM
    def advanceSimulation(self):
        #update the records of all the vehicles
        self.Vissim.Simulation.RunSingleStep() #advances the simulation by one step. Vissim will do new calculations.
        self.step += 1
        self.Data.PollAllVehicles(self.Vissim)
        self.Data.PollAllDetectors(self.step)
    
 
class NetworkData():
    def __init__(self, messagerelay):
        self.ActiveVehicles = {}#dict to hold all the vehicles currently on the network
        self.InactiveVehicles = {} #dict to hold vehicles that have left the network
        self.Links = {} #dict to hold all the links in the network. 
        self.Detectors = {}  
        self.CurrentSimulationRun = 0
        self.MessageRelay = messagerelay
        self._loadDetectors()        
    
    def PollAllDetectors(self, time):
        for detector in self.Detectors:
            if (time % detector["pollrate"] == 0):
                for veh in self.ActiveVehicles:
                    veh = self.ActiveVehicles[veh]
                    if detector["type"] in veh.DetectableBy:
                        if self._CheckInCircle(veh.Coord, detector):
                            #raw detections stores the list of detections as they happen
                            detector["rawdetections"].append([time, veh.Number])
                            
                            #an aggregated record is also stored
                            if not veh.Number in detector["detectrecord"]:
                                detector["detectrecord"][veh.Number] = {}
                                detector["detectrecord"][veh.Number]["first"] = time
                                detector["detectrecord"][veh.Number]["detect"] = 0
                            detector["detectrecord"][veh.Number]["last"] = time
                            detector["detectrecord"][veh.Number]["detect"] += 1
    def PollAllVehicles(self, VISSIM):
        Veh_Attributes = VISSIM.Net.Vehicles.GetMultipleAttributes(["No", "Lane", "CoordFront", "Speed", "Pos", "SimRun"])
        self.InactiveVehicles = self.ActiveVehicles
        self.ActiveVehicles = {}
        for veh in Veh_Attributes:
            v_num = int(veh[0])
            link_on = int(veh[1].split("-")[0])
            coord = str(veh[2])
            coords = coord.split() #split the coordinates into X Y Z array.
            speed = float(veh[3])
            linkpos = float(veh[4])
            self.CurrentSimulationRun = int(veh[5])   
            if (v_num in self.InactiveVehicles):
                vehicle = self.InactiveVehicles.pop(v_num)
                vehicle.Number = v_num
                vehicle.CurrentLink = link_on
                vehicle.Coord = coords
                vehicle.LinkPos = linkpos
                vehicle.CurrentSpeed = speed
                self.ActiveVehicles[v_num] = vehicle
            else:
                self.ActiveVehicles[v_num] = VehicleData(v_num, link_on, linkpos, None, None, coords, speed, self.Detectors)

    #loads detectors from the se
    def _loadDetectors(self):
        with open(DETECTORFILE) as df:
            self.Detectors = json.load(df)
                            
    def _CheckInCircle(self, veh_coord, detector):
        veh_x = float(veh_coord[0])
        veh_y = float(veh_coord[1])
        det_x = float(detector["coord"][0])
        det_y = float(detector["coord"][1])
        det_range = float(detector["range"])
        dist = math.pow((veh_x - det_x), 2) + math.pow((veh_y - det_y), 2)
        if (dist < math.pow(det_range, 2)): return True
        else: return False           
        
    def DumpRecords(self):
        self.MessageRelay.StatusUpdate("Dumping CSV File")
        for detector in self.Detectors:
            with open(WRITELOC + str(detector["id"]) + "_agg.csv", "w") as writefile:
                writefile.write("id,first,last,hits\n")
                for key, value in detector["detectrecord"].items():
                    writefile.write(str(key) + "," + str(value["first"]) + "," + str(value["last"]) + "," + str(value["detect"]) + "\n")
                    
    def DumpDirectionalTT(self):
        records = {}
        for detector in self.Detectors:
            for vnum in detector["detectrecord"]:
                for matchable in self.Detectors:
                    if matchable["id"] == detector["id"]: continue
                    if vnum in matchable["detectrecord"]:
                        origt = detector["detectrecord"][vnum]["first"] + detector["detectrecord"][vnum]["last"]
                        origt = origt / 2
                        destt = matchable["detectrecord"][vnum]["first"] + matchable["detectrecord"][vnum]["last"]
                        destt = destt / 2
                        tt = destt - origt
                        keysave = str(detector["id"]) + str(matchable["id"])
                        if not keysave in records: records[keysave] = {}
                        records[keysave][vnum] = tt
        for key, record in records.items():
            with open(WRITELOC + "tt_" + str(key) + ".csv", "w") as writefile:
                writefile.write("id,tt\n")
                for key, value in record.items():
                    writefile.write(str(key) + "," + str(value) + "\n")
                        
                
#Class to interact with individual vehicles in VISSIM.
class VehicleData(object):
    def __init__(self, number, currentlink, linkpos, routedesc, nextlink, coord, curspeed, detectors):
        self.Number = number
        self.CurrentLink = currentlink
        self.RouteDesc = routedesc
        self.NextLink = nextlink
        self.Coord = coord
        self.LinkPos = linkpos
        self.CurrentSpeed = curspeed
        self.DetectableBy = []    
        self.determineDetection(detectors)
        
    #this method does a probability roll to determine which detectors are assigned to the car.
    def determineDetection(self, detectors):
        for detector in detectors:
            if detector["type"] in self.DetectableBy: continue
            val = random.random() * 100
            if val <= detector["detection-penr"]:
                self.DetectableBy.append(detector["type"])
        


if __name__ == "__main__":
    main()