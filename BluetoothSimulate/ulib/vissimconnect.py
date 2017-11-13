'''
Created on Mar 20, 2017

@author: Matthew Muresan

This file contains the class that interacts with VISSIM

THIS FILE IS MODIFIED FROM THE RLEARN Library AND IS DESIGNED TO INTERFACE WITH THIS BLUETOOTH SYSTEM.

Class Structure:
    Vissim Connect (Main Vissim Class)
        |- Vissim (Vissim COM object)
        |- UIFeedBack (Interaction with Users [Deprecated])
        |- Data (Data parsed from VISSIM via COM)
        |    |- Active Vehicles (Data from vehicles on network)
        |    |- Inactive Vehicles (Data from vehicles once on the network)
        |        |- Number (Vehicle Number in VISSIM)
        |        |- Position (Tuple of Vehicle Locations)
        |    |- Links (Not used now)
        |- Methods (Functions)
        |    |- advanceSimulation(): This is the most important method. When called, advances the simulation by one step. Actions with VISSIM are conducted at a rate equal to "actionInterval", this includes changing signals, polling vehicles, etc.
        |- RBC (Signal Control Class)
        |- Network Data (Methods to Extract data directly from Vissim)
        |- Vehicle Data (Class to house VISSIM vehicle data)
        |- VissimSignal (Class to push/pull signal timings from VISSIM)
        
'''

import win32com.client as com
import pythoncom
import os

#OTHER IMPORTS
import os
import json
import math
import random


class MessageRelay(object):
    def __init__(self):
        pass
    def StatusUpdate(self, message):
        print(message)



class VissimConnect(object):
    def __init__(self, foname, detectorfile, populatesteps=0):
        pythoncom.CoInitialize()
        self.MessageRelay = MessageRelay() #console interaction
        self.Vissim = None #Variable which will house the COM that interfaces with Vissim
        self.populateSteps = populatesteps #The number of steps we want VISSIM to run before we begin observing vehicles. Vissim starts with no vehicles on the network, this time allows cars to enter.
        self.step = 0 #current time-step. Each time we advance the simulation one step, VISSIM does calculations. By default, 1 step = 0.2 simulated seconds.
        self.startVissim(foname) #open vissim, opening the *.inpx file at foname
        self.actingInterval = 5 #polling through com is slow. This setting sets it to poll VISSIM every simulated second.
        self.Data = NetworkData(self.MessageRelay, detectorfile) #create the class that will house the data.
        
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
        self.Data.CheckControllers(self.step)
    
    def restartSimulation(self):
        self.Vissim.Simulation.stop()
        self.MessageRelay.StatusUpdate("Populating VISSIM with Cars by running some steps after restarting")   
        self._populateVissim() #Populate the network
        self.Data.ActivateSignals(self.Vissim, self.step)
    
    def doAction(self, selected_action):
        if selected_action > 0:
            last_times = "Doing an Action. Last Green Times: "
            for controller_num in self.Data.Signals:
                string_prepend = "{}-".format(controller_num)
                controller = self.Data.Signals[controller_num]
                for SG in sorted(controller.RBCLogicControl.LastGreenDuration):
                    last_times += string_prepend + "{}:{}s ".format(SG, controller.RBCLogicControl.LastGreenDuration[SG]//10) #print the last signal timing to screen
                
                print(last_times)
                controller.RBCLogicControl.ChooseNextPlan(selected_action)
                controller.RBCLogicControl.AdvancePhase(self.step)
                
    def ActionsAllowed(self, ActionMode):
        return_code = [0b00]
        if ActionMode == 0:
            for controller_num in self.Data.Signals:
                controller = self.Data.Signals[controller_num]
                RBC_ob = controller.RBCLogicControl
                ring_ready = [False, False]
                ring_lastphase = [False, False]
                for ring in range(0,2):
                    SG = RBC_ob.SignalPlan[ring][RBC_ob.PhaseIndex[0]][RBC_ob.PhaseIndex[ring + 1]]
                    ring_ready[ring] = controller.RBCLogicControl.CheckRules(SG, ring, self.step, "GREEN")
                    ring_lastphase[ring] = RBC_ob.PhaseIndex[ring + 1] + 1 >= len(RBC_ob.SignalPlan[ring][RBC_ob.PhaseIndex[0]])
                
                    
                if ring_ready[0]:
                    if not ring_lastphase[0]:
                        return_code.append(0b01) #allow advancing only ring 0 if it will not result in a phase change.
                    elif ring_ready[1] and ring_lastphase[1]:
                        return_code.append(0b01) #allow advancing only ring 0 if ring 1 can also undergo a phase change.
                if ring_ready[1]:
                    if not ring_lastphase[1]:
                        return_code.append(0b10) #allow advacing only ring 2
                    elif ring_ready[0] and ring_lastphase[0]:
                        return_code.append(0b10) #allow advancing only ring 2
                if ring_ready[0] & ring_ready[1]:
                    if ring_lastphase[0] == ring_lastphase[1]: #allow advancing both at the same time IF both not on last phase or both on last phase
                        return_code.append(0b11) #advance both rings
                    if ring_lastphase[0] & ring_lastphase[1]:
                        return_code.append(0b100) #allow advancing directly to final phases.
            #if len(return_code) > 1: print("ready_ring " + str(ring_ready) + " ring_lastphase " + str(ring_lastphase))
        elif ActionMode == 1:
            for controller_num in self.Data.Signals:
                controller = self.Data.Signals[controller_num]
                RBC_ob = controller.RBCLogicControl
                ring_ready = [False, False]
                ring_lastphase = [False, False]
                for ring in range(0,2):
                    SG = RBC_ob.SignalPlan[ring][RBC_ob.PhaseIndex[0]][RBC_ob.PhaseIndex[ring + 1]]
                    ring_ready[ring] = controller.RBCLogicControl.CheckRules(SG, ring, self.step, "GREEN")
                    ring_lastphase[ring] = RBC_ob.PhaseIndex[ring + 1] + 1 >= len(RBC_ob.SignalPlan[ring][RBC_ob.PhaseIndex[0]])
                    
                if ring_ready[0] & ring_ready[1]:
                    if ring_lastphase[0] & ring_lastphase[1]:
                        return_code.append(1) #allow advancing directly to final phases only.
            
        return return_code


class VissimLink(object):
    def __init__(self, Number):
        self.Number = Number
        self.Queue = 0
        self.QueueReward = 0
    
#Signal Control Logic Class.
#This class houses all methods that control the signal's logic and decision rules.
class RBC(object):
    def __init__(self, signal_rules, init_time, yellows=None, allreds=None):
        self.TimingRules = {"MinGreens":signal_rules["min-green"], "YellowTimes":{}, "AllRedTimes":{}}
        
        #self.RingWantPhaseChange = [False, False, False, False] #whether or not each ring wants a phase change.
        
        self.PhaseStart = [0, 0] #time the "phases" was started
        #self.Transitioning = True #indicating whether or not the signal is transitioning.
        self.NextRequestedPhase = [0, 0, 0] #new PHASE, ring 1 sub-phase, ring 2 sub-phase
        #self.PhaseChangePermitted = True #master boolean indicating whether or not the signal is allowed to change based on rules.
        
        self.PhaseIndex = [0, 0, 0] #PHASE, ring 1 sub-phase, ring 2 sub-phase. Init at 1,0,0 allows the first run of the program to start the 0,0,0 phase
        self.LastGreenDuration = {}
        
        #SignalPlan determines which signals can time together, in order of decisions. This is a dictionary.
        #Sample: ([{"desc":"Through Movements, N/S", "groups": (2,6)}], [{"desc":"Through Movements, E/W", "groups": (4,8)}])
        #First level is the phase, second level is the options that can be chosen. Theoretically could add option to allow choosing an "advance green".
        #for now, only one option per phase. but could be (("desc":plan 1, "groups": (2,3)), ("desc":plan 2 ...
        self.SignalPlan = signal_rules["plan"] 
        self.SGphaseState = {} #current phase states, GREEN, AMBER, RED
        
        #INIT PHASE, add them to the list
        for SG in signal_rules["min-green"]:
            self.SGphaseState[SG] = "RED"
        for ring in range(0,2): #set green the plan that starts the system
            SG = self.SignalPlan[ring][self.PhaseIndex[0]][self.PhaseIndex[ring + 1]]
            self.SGphaseState[SG["group"]] = "GREEN"
            

        #ASSIGN YELLOW VALUE
        if (yellows == None):
            for SG in self.TimingRules["MinGreens"]:
                self.TimingRules["YellowTimes"][SG] = 20 #give default of 3s ish yellows
        else:
            self.TimingRules["YellowTimes"] = yellows
        
        #ASSIGN RED TIME    
        if (allreds == None):
            for SG in self.TimingRules["MinGreens"]:
                self.TimingRules["AllRedTimes"][SG] = 15 #give default of 2s ish yellows
        else:
            self.TimingRules["AllRedTimes"] = allreds
            
        #self.TransitionSignal(init_time) #transition the signal to the first phase
        #self.AdvancePhase(init_time) #transition the signal to the first phase
        
    def ChooseNextPlan(self, action):
        #converts action into signal plan code.
        #for now, we have no advance lefts, so just do the next plan.
        #next_index = (self.PhaseIndex[0] + 1) % len(self.SignalPlan)
        #next_index = action    
        
        #self.NextRequestedPhase = (next_index, 0)
        
        ring_phase = self.NextRequestedPhase[0]
        ring_1_subphase = self.NextRequestedPhase[1]
        ring_2_subphase = self.NextRequestedPhase[2]
        
        if action == 4: #advance to next phase (directly to primary phase)
            ring_phase = (ring_phase + 1) % len(self.SignalPlan[0])
            ring_1_subphase = len(self.SignalPlan[0][ring_phase]) - 1
            ring_2_subphase = len(self.SignalPlan[1][ring_phase]) - 1
            self.NextRequestedPhase = [ring_phase, ring_1_subphase, ring_2_subphase]
        
        else:
            ring_1_subphase += action & 0b01
            ring_2_subphase += (action & 0b10) >> 1
            
            if ring_1_subphase >= len(self.SignalPlan[0][ring_phase]) or ring_2_subphase >= len(self.SignalPlan[1][ring_phase]):
                ring_phase = (ring_phase + 1) % len(self.SignalPlan[0]) #advance to next phase, triggering the first optional phase, all subphases complete.
                if ring_1_subphase < len(self.SignalPlan[0][ring_phase]): 
                    ring_1_subphase = len(self.SignalPlan[0][ring_phase]) - 1 #advance directly to last phase
                else:
                    ring_1_subphase = 0 #advance to first phase
                if ring_2_subphase < len(self.SignalPlan[1][ring_phase]): 
                    ring_2_subphase = len(self.SignalPlan[1][ring_phase]) - 1 #advance directly to last phase
                else:
                    ring_2_subphase = 0
                    
            self.NextRequestedPhase = [ring_phase, ring_1_subphase, ring_2_subphase]
    
    def AdvancePhase(self, timestep):
        #elapsed_time = time - self.PhaseStart #current time since the phase started.
        start_next_phase = True
        return_code = False
        elapsed_time = [0, 0]
        elapsed_time[0] = timestep - self.PhaseStart[0]
        elapsed_time[1] = timestep - self.PhaseStart[1]
        
        if self.PhaseIndex[0] != self.NextRequestedPhase[0]: #hard change in signals
            return_code = True
            for ring in range(0,2):
                SG = self.SignalPlan[ring][self.PhaseIndex[0]][self.PhaseIndex[ring + 1]]
                if not self.CheckRules(SG, ring, timestep): #only change if allowed
                     return return_code#not all signals ready to change (still changing to red).
                 
            for ring in range(0,2):
                SG = self.SignalPlan[ring][self.PhaseIndex[0]][self.PhaseIndex[ring + 1]]
                self.PhaseStart[ring] = timestep
                start_next_phase &= self._changeSGtoRed(SG["group"], elapsed_time[ring])
            
            if start_next_phase != False:
                for ring in range(0,2):
                    SG = self.SignalPlan[ring][self.NextRequestedPhase[0]][self.NextRequestedPhase[ring + 1]]
                    self.SGphaseState[SG["group"]] = "GREEN"
                    self.PhaseIndex = self.NextRequestedPhase
        
        else: #sub-phase change
            for ring in range(0,2):
                if self.PhaseIndex[ring + 1] != self.NextRequestedPhase[ring + 1]:
                    return_code = True
                    SG = self.SignalPlan[ring][self.PhaseIndex[0]][self.PhaseIndex[ring + 1]]
                    if self.CheckRules(SG, ring, timestep): #only change if allowed
                        self.PhaseStart[ring] = timestep
                        if self._changeSGtoRed(SG["group"], elapsed_time[ring]):
                            SG = self.SignalPlan[ring][self.NextRequestedPhase[0]][self.NextRequestedPhase[ring + 1]]
                            self.SGphaseState[SG["group"]] = "GREEN"
                            self.PhaseIndex[ring + 1] = self.NextRequestedPhase[ring + 1]
        return return_code
    #changes the SG between green->amber->red. Returns TRUE if signal was already red
    def _changeSGtoRed(self, SG, elapsed_time):
        if self.SGphaseState[SG] == "GREEN":
            self.LastGreenDuration[SG] = elapsed_time
            self.SGphaseState[SG] = "AMBER"
        elif self.SGphaseState[SG] == "AMBER":
            self.SGphaseState[SG] = "RED"
        elif self.SGphaseState[SG] == "RED":
            return True
        
        return False
    
    def CheckRules(self, SG, ring, step, restriction=None):
        elapsed_time = step - self.PhaseStart[ring]
        if restriction == "GREEN":
            if self.SGphaseState[SG["group"]] != "GREEN": 
                return False
        
        return self._CheckRules(elapsed_time, SG["group"])
    #returns true if a a phase change is permitted
    def _CheckRules(self, elapsed_time, SG):
        if self.SGphaseState[SG] == "GREEN":
            if elapsed_time < self.TimingRules["MinGreens"][SG]: return False
        elif self.SGphaseState[SG] == "RED":
            if elapsed_time < self.TimingRules["AllRedTimes"][SG]: return False
        elif self.SGphaseState[SG] == "AMBER":
            if elapsed_time < self.TimingRules["YellowTimes"][SG]: return False 
        
        return True
                
                   
#Class to pull/push signal data to/from vissim
class VissimSignal(object):
    def __init__(self, no, controller, time, SG_Locations, SGonWhichLinks):
        self.No = no #signal group number
        self.Groups = {} #in vissim signal heads are divided into groups, this houses the groups we will control.
        self.Controller = controller
        self.SignalLocations = SG_Locations
        self.SGsOnWhichLink = SGonWhichLinks
        self.PushSignal = True
        #DEFINE SIGNAL PARAMETERS        
        #which signals can time together, in order of decisions. First level is the phase, second level is the options that can be chosen.
        #for now, only one option per phase. but could be (("desc":plan 1, "groups": (2,3)), ("desc":plan 2 ...
        decision_subset = ([{"desc":"Through Movements, N/S", "groups": (2,6)}], [{"desc":"Through Movements, E/W", "groups": (4,8)}])
        
        #RBC is a re-implentation of RBC logic into the TBC controller. Here "Rank" describes the order of phases. The 0 rank phase is not skippable, and will be called if no other phase is asked for.
        '''
        RBC_plan = (([{"desc":"WL", "group": 5, "rank":1},{"desc":"E", "group": 6, "rank":0}], [{"desc":"NL", "group": 7, "rank":1},{"desc":"S", "group": 8, "rank":0}]),
                    ([{"desc":"EL", "group": 1, "rank":1},{"desc":"W", "group": 2, "rank":0}], [{"desc":"SL", "group": 3, "rank":1},{"desc":"N", "group": 4, "rank":0}]))
        
        '''
        RBC_plan = (([{"desc":"E", "group": 6, "rank":0}], [{"desc":"S", "group": 8, "rank":0}]),
                    ([{"desc":"W", "group": 2, "rank":0}], [{"desc":"N", "group": 4, "rank":0}]))
        signal_rules = {"plan":RBC_plan, "min-green":{1:450, 3:450, 5:450, 7:450, 2:450, 4:450, 6:450, 8:450}} #150 = 30 simulated seconds, 50 = 10 simulated seconds
        self.RBCLogicControl = RBC(signal_rules, time)
        
        #Add signals to the groups and the initialize their state
        self.UpdatePopulateSignalState()
        self._PushSignalPhase()
    
    #method to check the state of signals in VISSIM and init the signal group class. Should only be used sparingly, state should always be known.
    def UpdatePopulateSignalState(self):
        for group in self.Controller.SGs:
            group.SetAttValue("ContrByCom", True)
            sig_no = int(group.AttValue("No"))
            state = str(group.AttValue("State"))
            self.Groups[sig_no] = state
    
    #push signal phase timings according to the desired state.
    def _PushSignalPhase(self):
        self.PushSignal = False
        for group in self.Groups:
            desired_state = self.RBCLogicControl.SGphaseState[group] #check if the state desired and the state in VISSIM are different.
            state = self.Controller.SGs.ItemByKey(group).AttValue("State")
            if state != desired_state:
                self.Controller.SGs.ItemByKey(group).SetAttValue("State", desired_state) #update the state
                self.PushSignal = True
    
    #methods to individually check if signals can change
    def CheckFlagSignals(self, timestep):
        #self.RBCLogicControl.CheckIfChangePermitted(time)
        #if self.RBCLogicControl.Transitioning:
        #    self.RBCLogicControl.TransitionSignal(time)
        self.PushSignal = self.RBCLogicControl.AdvancePhase(timestep) #checks if phases can be advanced and advances them.
        self._PushSignalPhase() #re-push signal phases if VISSIM did not change them.
           
#collects statistics from VISSIM.
class NetworkPerformance():
    def __init__(self):
        self.DelayAvg = {}
        self.CurrentSimulationRun = 0  #actual VISSIM run number
        self.CurrentTimeInterval = 1 #actual VISSIM time interval number (results grouped into segments)
        self.CurrentSimulationSecond = 0 #actual VISSIM simulation second
        self.RunsCompleted = 0
        
        self.Queueing_Threshold = 15 #speed below-which vehicles are considered "queued"
        self.RewardVehicles = 0 #keeps track of the vehicles as they are discharged for reward
        
    def returnSimulationTimes(self, simulated_days=1):
        day = int(self.CurrentSimulationSecond // (3600*24))
        hour = int((self.CurrentSimulationSecond - ((self.CurrentSimulationSecond // (3600*24)) * 3600*24)) // 3600)
        day += self.RunsCompleted*simulated_days
        return (day, hour)
    def updatePerformanceMetrics(self, VISSIM):
        try:
            self.CurrentSimulationSecond = VISSIM.Simulation.SimulationSecond
            
            request_string = "DelayAvg({},{},{})".format(self.CurrentSimulationRun, self.CurrentTimeInterval, "All") 
            AVGDelayVisObj = VISSIM.Net.VehicleNetworkPerformanceMeasurement
            self.DelayAvg[self.CurrentTimeInterval] = float(AVGDelayVisObj.AttValue(request_string))
            request_string = "DelayAvg({},{},{})".format(self.CurrentSimulationRun, self.CurrentTimeInterval+1, "All")
            next_delay_check = AVGDelayVisObj.AttValue(request_string) #in vissim, the data is collected by time interval, check the next time interval.
        except:
            next_delay_check = None
        
        if next_delay_check != None:
            #write an image of the last segement.
            #self.savePlotToImg({"DelayAvg": self.DelayAvg})
            self.CurrentTimeInterval += 1
            self.DelayAvg[self.CurrentTimeInterval] = float(next_delay_check)
    
    #gets the reward for discharged vehicles and clears the count
    def getReward(self, scale_by):
        reward = self.RewardVehicles * scale_by
        self.RewardVehicles = 0
        return reward
             

class VehicleDetectors():
    def __init__(self, messagerelay, detectorfile):
        self.Detectors = {}  
        self.CurrentSimulationRun = 0
        self.MessageRelay = messagerelay
        self.detectorfile = detectorfile
        self.matchedTT = {}
        
        self._loadDetectors()  
            
    
    #VERSION 2 METHODS - Poll All Detectors
    def PollAllDetectors(self, time, ActiveVehicles):
        for detector in self.Detectors:
            if (time % detector["pollrate"] == 0):
                for veh in ActiveVehicles:
                    veh = ActiveVehicles[veh]
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
                            
    #VERSION 2 METHOD - loads detectors from the settings file
    def _loadDetectors(self):
        with open(self.detectorfile) as df:
            self.Detectors = json.load(df)
      
    #VERSION 2 METHOD - check if vehicle coord in detector                 
    def _CheckInCircle(self, veh_coord, detector):
        veh_x = float(veh_coord[0])
        veh_y = float(veh_coord[1])
        det_x = float(detector["coord"][0])
        det_y = float(detector["coord"][1])
        det_range = float(detector["range"])
        dist = math.pow((veh_x - det_x), 2) + math.pow((veh_y - det_y), 2)
        if (dist < math.pow(det_range, 2)): return True
        else: return False           
    
    #VERSION 2 METHOD - Dumps records to file    
    def DumpRecords(self, writeloc, prefix=""):
        self.MessageRelay.StatusUpdate("Dumping CSV File")
        for detector in self.Detectors:
            with open(writeloc + prefix + str(detector["id"]) + "_agg.csv", "w") as writefile:
                writefile.write("id,first,last,hits\n")
                for key, value in detector["detectrecord"].items():
                    writefile.write(str(key) + "," + str(value["first"]) + "," + str(value["last"]) + "," + str(value["detect"]) + "\n")
    
    def matchVehicles(self):
        records = {}
        #iterate through detector raw records and find matches for each combination
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
                        if (tt < 0): continue #skip this record if it is going the wrong direciton
                        keysave = str(detector["id"]) + "TO" + str(matchable["id"])
                        if not keysave in records: records[keysave] = {}
                        records[keysave][vnum] = tt
                        #save the total traveltime
                        if not "total_travel_time" in records[keysave]: records[keysave]["total_travel_time"] = tt
                        else: records[keysave]["total_travel_time"] += tt
                        if not "fastest_travel_time" in records[keysave]: records[keysave]["fastest_travel_time"] = tt
                        elif records[keysave]["fastest_travel_time"] > tt: records[keysave]["fastest_travel_time"] = tt
                
        self.matchedTT = records
        
    #returns the movement times and volumes 
    def ReturnMovementTimes(self, principle_key, rematch=False):
        if rematch: self.matchVehicles()
        records = self.matchedTT
        tt_vol = {}
        for key, record in records.items():
            if "middle" in key: continue
            if principle_key + "TO" in key:
                tt_vol[key] = [0,0,0]
                tt_vol[key][0] = record["total_travel_time"] #total travel time
                tt_vol[key][1] = len(record) - 2 #number of vehicles (exclude the two extra entries of fastest and total.
                tt_vol[key][2] = record["fastest_travel_time"]
        return tt_vol                
                
        
        
    #writes the existing records to file and then flushes the record. Use when implementing a new timing plan.
    def ArchiveRecords(self, time, writeloc, only_totaltt=False, rematch=False):
        prefix = "archive_to" + str(time)
        if rematch: self.matchVehicles()
        self.DumpDirectionalTT(writeloc, only_totaltt, prefix)
        self.DumpRecords(writeloc, prefix)
        
        #clear arcive records
        self._loadDetectors()
    
    #VERSION 2 Metohd - Dumps Directional Travle Times                
    def DumpDirectionalTT(self, writeloc, only_totaltt=False, prefix=""):
        self.matchVehicles()
        records = self.matchedTT
        for key, record in records.items():
            with open(writeloc + prefix + "tt_" + str(key) + ".csv", "w") as writefile:
                writefile.write("id,tt\n")
                if only_totaltt:
                    key = "total_travel_time"
                    value = record["total_travel_time"]
                    writefile.write(str(key) + "," + str(value) + "\n")
                else:
                    for key, value in record.items():
                        writefile.write(str(key) + "," + str(value) + "\n")      
    
class NetworkData():
    def __init__(self, messagerelay, detectorfile):
        self.ActiveVehicles = {}#dict to hold all the vehicles currently on the network
        self.InactiveVehicles = {} #dict to hold vehicles that have left the network
        self.Links = {} #dict to hold all the links in the network. 
        
        #Machine Learning Methods (Version 1)     
        self.Signals = {}
        self.Performance = NetworkPerformance()
        
        #Bluetooth Extension Methods (Version 2)
        self.VehicleDetectors = VehicleDetectors(messagerelay, detectorfile)  
 
    #VERSION 1 METHOD - Activates Signals
    def ActivateSignals(self, VISSIM, cur_time):
        for controller in VISSIM.Net.SignalControllers:
            s_num = int(controller.AttValue("No")) #get the controller number
            SignalLocations = {} #used to calculate queues
            SGonWhichLinks = {}
            if not s_num in self.Signals:
                for SGhead in VISSIM.Net.SignalHeads:
                    HeadSG = int(SGhead.SG.AttValue("No"))
                    HeadPos = float(SGhead.AttValue("Pos"))
                    HeadLink = int(SGhead.Lane.Link.AttValue("No"))
                    SignalLocations[HeadLink] = [HeadPos, "LINK " + str(HeadLink), 0]
                    if not HeadSG in SGonWhichLinks:
                        SGonWhichLinks[HeadSG] = [HeadLink]
                    elif not HeadLink in SGonWhichLinks[HeadSG]:
                        SGonWhichLinks[HeadSG].append(HeadLink)
                self.Signals[s_num] = VissimSignal(s_num, controller, cur_time, SignalLocations, SGonWhichLinks) #create a new signal controlling class that will interact with this signal.
                
        for link in VISSIM.Net.Links:
            link_no = int(link.AttValue("No")) #get the controller number
            self.Links[link_no] = VissimLink(link_no)
    
    #VERSION 1 METHOD - Checks Signal Controllers
    def CheckControllers(self, cur_time):
        for controller_num in self.Signals:
            self.Signals[controller_num].CheckFlagSignals(cur_time) #check each controller if it will advance.
        
    #VERSION 1 METHOD - Resets Queue's tracked on networks for MACHINE LEARNING
    def _ResetQueues(self):
        for link in self.Links:
            self.Links[link].Queue = 0
            self.Links[link].QueueReward = 0
        
    #VERSION 1 METHOD - Update Performance Measures
    def _UpdatePerformance(self, vehicle, controller=1):
        if vehicle.CurrentSpeed < self.Performance.Queueing_Threshold:
            self.Links[vehicle.CurrentLink].Queue += 1
            self.Links[vehicle.CurrentLink].QueueReward += vehicle.QueuePenalty
            vehicle.QueuePenalty += 5 #increase the penalty for repeatedly holding vehicles back.
        
        SignalLocations = self.Signals[controller].SignalLocations
        if not vehicle.Discharged:
            if vehicle.CurrentLink in SignalLocations and vehicle.LinkPos > SignalLocations[vehicle.CurrentLink][0]:
                self.Performance.RewardVehicles += 1
                vehicle.Discharged = True
 
    #VERSION 2 METHOD - Poll All Vehicles
    def PollAllVehicles(self, VISSIM):
        Veh_Attributes = VISSIM.Net.Vehicles.GetMultipleAttributes(["No", "Lane", "CoordFront", "Speed", "Pos", "SimRun"])
        self._ResetQueues()
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
                self._UpdatePerformance(vehicle)
            else:
                self.ActiveVehicles[v_num] = VehicleData(v_num, link_on, linkpos, None, None, coords, speed, self.VehicleDetectors.Detectors)

    #Passes the poll all detectors command to the detectors class
    def PollAllDetectors(self, step):   
        self.VehicleDetectors.PollAllDetectors(step, self.ActiveVehicles)                                
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
        
        self.Discharged = False #indicates if it has been rewarded.
        self.QueuePenalty = 1 #current penalty value for being in a queue
        
        self.DetectableBy = [] #indicates what devices the vehicle carries for detection 
        self.determineDetection(detectors) #calls a function to determine the detectability (randomize)
        
    #this method does a probability roll to determine which detectors are assigned to the car.
    def determineDetection(self, detectors):
        for detector in detectors:
            if detector["type"] in self.DetectableBy: continue
            val = random.random() * 100
            if val <= detector["detection-penr"]:
                self.DetectableBy.append(detector["type"])
        
