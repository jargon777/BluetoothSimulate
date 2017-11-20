'''
Created on Apr 3, 2017

@author: Matthew Muresan
'''
from itertools import cycle

class GradientDescentSelectTime():
    def __init__(self, VissimControl):
        self.VissimControl = VissimControl
        self.active_X = 0.5 #initial green split ratio
        self.Xs = []
        self.gamma = 10 #amount of time to adjust and split between the movements.
        self.precision = 0.001
        self.previous_step_size = self.active_X
        self.system_av_tt = []
        self.current_step = 0 
        self.fastest_tt = {}
        
        self.highest_delays = {"EBWB": [], "NBSB": []}
        self.highest_saturation = {"EBWB": [], "NBSB": []}
    
    def SelectSplit(self, i, writeloc, time_NB, time_WB):
        self.VissimControl.Data.VehicleDetectors.matchVehicles() #match vehilces in the TT record
        
        #obtain travel times / vols for NB etc
        vols = {}
        vols["NB"] = self.VissimControl.Data.VehicleDetectors.ReturnMovementTimes("bluetoothsouth")
        vols["SB"] = self.VissimControl.Data.VehicleDetectors.ReturnMovementTimes("bluetoothnorth")
        vols["EB"] = self.VissimControl.Data.VehicleDetectors.ReturnMovementTimes("bluetoothwest")
        vols["WB"] = self.VissimControl.Data.VehicleDetectors.ReturnMovementTimes("bluetoothwest")
        
        #choose a direction to modify the split times
        if self.previous_step_size > self.precision:
            system_tot_tt = 0
            system_tot_v = 0
            a_del = {}
            t_tt = {}
            t_vol = {}
            #temporarily identify critical movements by grouping to movement
            for dir, vol in vols.items():
                a_del[dir] = {}
                if not dir in self.fastest_tt: self.fastest_tt[dir] = {}
                for key, movement in vol.items():
                    if not key in self.fastest_tt[dir]: self.fastest_tt[dir][key] = movement[2]
                    elif self.fastest_tt[dir][key] > movement[2]: self.fastest_tt[dir][key] = movement[2]
                    a_del[dir][key] = (movement[0] - (self.fastest_tt[dir][key] * movement[1])) / movement[1] #compute weighted average for average delay
                    system_tot_tt += movement[0]
                    system_tot_v += movement[1]
            
            if system_tot_tt == 0: return [time_NB, time_WB] #short circuit if no detections    
            system_av_tt = system_tot_tt / system_tot_v 
            #identify the critical movements
            NB_SB_crit = 0
            EB_WB_crit = 0
            NB_SB_crit_time = 0
            EB_WB_crit_time = 0
            cycletime = time_NB/10 + time_WB/10 + 10 #/10 because vissim reports in 100ths of seconds, and add back on the lost time.
            green_NB = time_NB/10
            green_WB = time_WB/10
            for dir, delays in a_del.items():
                for key, movement in delays.items():
                    movement = movement/10 #times are in hundredth seconds.
                    movement -= 4 #to account for the liklihood that the "fastest" value is the extremities based on the polling rate. Temporary fix.
                    if dir == "NB" or dir == "SB":
                        if not movement <= 0:
                            saturation = (-(cycletime**2-2*cycletime*movement-2*cycletime*green_NB+green_NB**2)/(2*movement*green_NB)) * (cycletime/green_NB)
                            if saturation < 0.1: saturation = 0.1 #enforce a floor for the saturation.
                            print("Movement " + str(key) + ": " + str(movement) + " Saturation: " + str(saturation))
                            if saturation > NB_SB_crit: 
                                NB_SB_crit = saturation
                                NB_SB_crit_time = movement
                    elif dir == "EB" or dir == "WB":
                        if not movement <= 0:
                            saturation = (-(cycletime**2-2*cycletime*movement-2*cycletime*green_WB+green_WB**2)/(2*movement*green_WB))  * (cycletime/green_WB)
                            if saturation < 0.1: saturation = 0.1 #enforce a floor for the saturation.
                            print("Movement " + str(key) + ": " + str(movement) + " Saturation: " + str(saturation))
                            if saturation > EB_WB_crit: 
                                EB_WB_crit = saturation
                                EB_WB_crit_time = movement
            
            
            self.highest_delays["EBWB"].append(EB_WB_crit_time)
            self.highest_delays["NBSB"].append(NB_SB_crit_time)
            self.highest_saturation["EBWB"].append(EB_WB_crit)
            self.highest_saturation["NBSB"].append(NB_SB_crit)
            self.Xs.append(self.active_X)
            self.system_av_tt.append(system_av_tt)
            #self.active_X = NB_SB_crit / (NB_SB_crit + EB_WB_crit)

            #if self.active_X < 0.1: self.active_X = 0.1
            #if self.active_X > 0.9: self.active_X = 0.9
            #print("New X is " + str(self.active_X))
            #print("Old X was" + str(self.Xs[-1]))
            
        #self.VissimControl.Data.VehicleDetectors.ArchiveRecords(i, writeloc, False, False) #archive all the old data and erase it, restarting collection
        #remove old travel times.
        self.VissimControl.Data.VehicleDetectors.PruneRecords(i)
        
        #re-allocate a block of time to the two movements to adjust and balance the delays.
        print("Original NS time is: " + str(time_NB) + " and for EW " + str(time_WB))
        if NB_SB_crit > EB_WB_crit and time_WB > 50:
            time_NB += self.gamma
            time_WB -= self.gamma
        elif time_NB > 50:
            time_NB -= self.gamma
            time_WB += self.gamma
        self.active_X = time_NB / (time_NB + time_WB)
        
        print("Resulting NS time is: " + str(time_NB) + " and for EW " + str(time_WB))
        return [time_NB, time_WB]
        
        
    #VERSION 2 Metohd - Dumps Directional Travle Times                
    def DumpPerformanceMeasures(self, writeloc, prefix=""):
        i = 0
        with open(writeloc + prefix + "performance_measures" + ".csv", "w") as writefile:
            writefile.write("X,av_tt,maxdelay_NBSB,saturation_NBSB,maxdelay_EBWB,saturation_EBWB\n")
            print(self.Xs)
            print(self.system_av_tt)
            for X in self.Xs:
                writefile.write(str(X) + "," + str(self.system_av_tt[i]) + "," 
                                + str(self.highest_delays["NBSB"][i]) + "," + str(self.highest_saturation["NBSB"][i]) + "," 
                                + str(self.highest_delays["EBWB"][i]) + "," + str(self.highest_saturation["EBWB"][i]) + "\n")
                i += 1
            