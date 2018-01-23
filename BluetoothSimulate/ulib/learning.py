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
        self.gamma = 50 #amount of time to adjust and split between the movements.
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
                    if not key in self.fastest_tt[dir]: self.fastest_tt[dir][key] = movement["fflow"][0]/movement["fflow"][1]
                    elif self.fastest_tt[dir][key] > movement["fflow"][0]/movement["fflow"][1] and movement["fflow"][1] > 5: self.fastest_tt[dir][key] = movement["fflow"][0]/movement["fflow"][1] #update the fastest time if enough vehicles recorded
                    #calculate the overall average via weighting
                    a_del[dir][key] = movement["total"][0]/movement["total"][1] - self.fastest_tt[dir][key]                
                    system_tot_tt += movement["total"][0]
                    system_tot_v += movement["total"][1]
            
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
                    #movement -= 4 #to account for the liklihood that the "fastest" value is the extremities based on the polling rate. Temporary fix.
                    if dir == "NB" or dir == "SB":
                        if not movement <= 0:
                            saturation = (-(cycletime**2-2*cycletime*movement-2*cycletime*green_NB+green_NB**2)/(2*movement*green_NB))
                            if saturation < 0.1: saturation = 0.1 #enforce a floor for the saturation.
                            flowration = saturation*(green_NB/cycletime)
                            print("Movement " + str(key) + ": " + str(movement) + " Saturation: " + str(saturation) + " Flow Ration: " + str(flowration))
                            if flowration > NB_SB_crit: 
                                NB_SB_crit = flowration
                                NB_SB_crit_time = movement
                    elif dir == "EB" or dir == "WB":
                        if not movement <= 0:
                            saturation = (-(cycletime**2-2*cycletime*movement-2*cycletime*green_WB+green_WB**2)/(2*movement*green_WB))
                            if saturation < 0.1: saturation = 0.1 #enforce a floor for the saturation.
                            flowration = saturation*(green_WB/cycletime)
                            print("Movement " + str(key) + ": " + str(movement) + " Saturation: " + str(saturation) + " Flow Ration: " + str(flowration))
                            if flowration > EB_WB_crit: 
                                EB_WB_crit = flowration
                                EB_WB_crit_time = movement
            
            
            self.highest_delays["EBWB"].append(EB_WB_crit_time)
            self.highest_delays["NBSB"].append(NB_SB_crit_time)
            self.highest_saturation["EBWB"].append(EB_WB_crit)
            self.highest_saturation["NBSB"].append(NB_SB_crit)
            self.Xs.append(self.active_X)
            self.system_av_tt.append(system_av_tt)

            
        #self.VissimControl.Data.VehicleDetectors.ArchiveRecords(i, writeloc, False, False) #archive all the old data and erase it, restarting collection
        #self.VissimControl.Data.VehicleDetectors.DumpDirectionalTT(writeloc) #write the travel times
        #remove old travel times.
        self.VissimControl.Data.VehicleDetectors.PruneRecords(i)
        
        #re-allocate a block of time to the two movements to adjust and balance the delays.
        print("Original NS time is: " + str(time_NB) + " and for EW " + str(time_WB))
        Ideal_NB = ((NB_SB_crit / (NB_SB_crit + EB_WB_crit)) * (cycletime*10))
        print("Ideal NS time is: " + str(Ideal_NB) + " and for EW " + str(cycletime*10 - Ideal_NB))
        distance = time_NB - Ideal_NB
        span = self.gamma
        gradient = distance/span
        gradient = gradient / ((1+gradient**2)**0.5) * self.gamma + 5 #because we are going to round via floor division
        gradient = gradient // 10 
        gradient *= 10 #floor division to round.
        time_WB += gradient
        time_NB -= gradient
        if time_WB < 50:
            time_WB = 50
            time_NB -= 50 - (time_WB)
        elif time_NB < 50:
            time_NB = 50
            time_WB -= 50 - (time_NB)
        #if NB_SB_crit > EB_WB_crit and time_WB > 50:
            #time_NB += self.gamma
            #time_WB -= self.gamma
        #elif time_NB > 50:
            #time_NB -= self.gamma
            #time_WB += self.gamma
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
            