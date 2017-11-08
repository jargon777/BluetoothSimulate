'''
Created on Apr 3, 2017

@author: Matthew Muresan
'''

class GradientDescentSelectTime():
    def __init__(self, VissimControl):
        self.VissimControl = VissimControl
        self.active_X = 0.5 #initial green split ratio
        self.Xs = []
        self.gamma = 1/10000 #step size multiplier. threshold for significant changes in delay. ratio is adjusted by 1/X * difference in av TT. If tt changes by 1s between successive tests, check vs precision!
        self.precision = 0.001
        self.previous_step_size = self.active_X
        self.system_av_tt = []
        self.current_step = 0 
        self.sigmoid_ceiling = 0.1 #a sigmoid function is used to prevent a large gradient. This is the maximum change that will be allowed to X
    
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
            for key, vol in vols.items():
                for key, movement in vol.items():
                    system_tot_tt += movement[0]
                    system_tot_v += movement[1]
            system_av_tt = system_tot_tt / system_tot_v
            gradient = 0
            if len(self.system_av_tt) == 0: gradient = self.precision*10 #go 10x the precision in the positive direction.
            else:
                distance = self.system_av_tt[-1] - system_av_tt
                span = (self.Xs[-1] - self.active_X) * -10 #multiply by 10 to more easily understand consequences. Single units are 0.1 of the ratio. Invert to get the negative ROC.
                if not span == 0:
                    gradient = distance/span * self.gamma * 10 #because we will apply the sigmoid
                    gradient = (gradient) / ((1 + gradient**2)**0.5) * 0.1 #apply a sigmoid function to the gradient limited to 0.1
                else:
                    gradient = 0
                      
            self.Xs.append(self.active_X)
            self.system_av_tt.append(system_av_tt)
            self.active_X += gradient
            if self.active_X < 0.1: self.active_X = 0.1
            if self.active_X > 0.9: self.active_X = 0.9
            print("Gradient is " + str(gradient))
            print("New X is " + str(self.active_X))
            print("Old X was" + str(self.Xs[-1]))
            
        self.VissimControl.Data.VehicleDetectors.ArchiveRecords(i, writeloc, True, False) #archive all the old data and erase it, restarting collection
        time_WB = time_WB + time_NB
        time_NB = time_WB
        time_NB = (time_NB*self.active_X + 5) // 10 * 10 #round by adding 5 and then floor division
        print("Resulting NS time is: " + str(time_NB))
        time_WB -= time_NB
        return [time_NB, time_WB]
        
        
    #VERSION 2 Metohd - Dumps Directional Travle Times                
    def DumpPerformanceMeasures(self, writeloc, prefix=""):
        i = 0
        with open(writeloc + prefix + "performance_measures" + ".csv", "w") as writefile:
            writefile.write("X,av_tt\n")
            print(self.Xs)
            print(self.system_av_tt)
            for X in self.Xs:
                writefile.write(str(X) + "," + str(self.system_av_tt[i]) + "\n")
                i += 1
            