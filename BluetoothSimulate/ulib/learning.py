'''
Created on Apr 3, 2017

@author: Matthew Muresan
'''
from itertools import cycle
import copy
import math


class GoldenMethods():
    #for use in one version of the reward function
    def __init__(self, VissimControl):
        self.VissimControl = VissimControl
        self.vols = []
        self.cycles = []
        self.gamma = 1
        self.gammaC = 1 #gamma for cycle length
        self.beta = 1 #default is 1
        self.betaC = 1 #beta for cycle length
        self.mixmode = 1 #the mode for mixing the volume and delay. Setting 0 is delay only, setting 1 is volume only, setting 2 is mix
        self.vol_e_mode = 0 #0 error is count based, 1 error is % based
        self.delay_mode = 1 #0 to allow individual lanes, 1 to merge them.
        self.opt_mode = 0
        self.del_err_est = 0
        self.vol_err_est = 0 #estimates of the error standard deviation.
        self.cyclemode = 0 #controls if cycle length is modified.
        self.minG = 5 #minimum green time.
        self.maxG = 120
        self.maxC = 120
        self.minC = 60 #do not go below 60s cycle time
        self.minY = 0
        #"green_pl", "ideals","lngrevR","lngrevT","lngrevL","d1s","Caps","Xs","cycle","d1","d2s","dts","estvol","greens","time","totald", "vols", "lanegr", "lane_s", "lanltc", "phasen", "phaseo", "phases", "lane_g", "erv"
        #self.DNRLABS = ["green_pl","lanegr","lane_s","lanltc", "phasen", "phaseo", "phases", "lane_g", "erv"] #labels not to write as the logfile.
        self.DNRLABS = ["totald", "green_pl","ideals","lngrevR","lngrevT","lngrevL","d1s","Caps","Xs","cycle","d1","d2s","estvol","greens", "vols", "lanegr", "lane_s", "lanltc", "phasen", "phaseo", "phases", "lane_g", "erv"]
        self.f_q = (0,1,0.625,0.51,0.44) #conflict factor for left turns permissive used to calculate f_L
        
        
        
        #VOLUME SET 2 (real)
        self.vols.append({})
        self.vols[0]["lanegr"] = []
        #lane group defintion for phases
        self.vols[0]["lanegr"].append(["lan_1", "lan_2", "lan_3"]) #north side
        self.vols[0]["lanegr"].append(["lan_4", "lan_5", "lan_6", "lan_7"]) #east side
        self.vols[0]["lanegr"].append(["lan_8", "lan_9", "lan_10", "lan_11"]) #west side
        #gccnt.vols[0]["lanegr"].append(["lan_6", "lan_7", "lan_8"]) #west
        #phasing diagram
        self.vols[0]["phaseo"] = [[0],[1,2]]
        self.vols[0]["greens"] = [45,45]
        self.vols[0]["green_pl"] = [[0,[25,25]],[6,[35,15]],[10.5,[29,21]],[16.5,[25,25]],[17,[29,21]],[23,[25,25]]]
        self.vols[0]["cycle"] = 90
        
        #volume split of lane
        self.vols[0]["lane_s"] = {}
        self.vols[0]["lane_s"]["lan_1"] = {"L":1} #NL3
        self.vols[0]["lane_s"]["lan_2"] = {"L":1} #NL2
        self.vols[0]["lane_s"]["lan_3"] = {"L":1} #NL1
        self.vols[0]["lane_s"]["lan_4"] = {"L":1} #EU1, considered as left
        self.vols[0]["lane_s"]["lan_5"] = {"T":1} #ET2
        self.vols[0]["lane_s"]["lan_6"] = {"T":1} #ET1
        self.vols[0]["lane_s"]["lan_7"] = {"R":1} #ER1
        self.vols[0]["lane_s"]["lan_8"] = {"L":1} #WL1
        self.vols[0]["lane_s"]["lan_9"] = {"T":1} #WT1
        self.vols[0]["lane_s"]["lan_10"] = {"T":1} #WT3
        self.vols[0]["lane_s"]["lan_11"] = {"T":1} #WT2
        
        self.vols[0]["phasen"] = 2
        self.vols[0]["phases"] = {}
        self.vols[0]["phases"]["lan_1"] = [0]
        self.vols[0]["phases"]["lan_2"] = [0]
        self.vols[0]["phases"]["lan_3"] = [0]
        self.vols[0]["phases"]["lan_4"] = [1]
        self.vols[0]["phases"]["lan_5"] = [1]
        self.vols[0]["phases"]["lan_6"] = [1]
        self.vols[0]["phases"]["lan_7"] = [1]
        self.vols[0]["phases"]["lan_8"] = [1]
        self.vols[0]["phases"]["lan_9"] = [1]
        self.vols[0]["phases"]["lan_10"] = [1]
        self.vols[0]["phases"]["lan_11"] = [1]
        
        self.vols[0]["lane_g"] = {} #in order of occurance
        self.vols[0]["lane_g"]["lan_1"] = [0]
        self.vols[0]["lane_g"]["lan_2"] = [0]
        self.vols[0]["lane_g"]["lan_3"] = [0]
        self.vols[0]["lane_g"]["lan_4"] = [1]
        self.vols[0]["lane_g"]["lan_5"] = [1]
        self.vols[0]["lane_g"]["lan_6"] = [1]
        self.vols[0]["lane_g"]["lan_7"] = [1]
        self.vols[0]["lane_g"]["lan_8"] = [2]
        self.vols[0]["lane_g"]["lan_9"] = [2]
        self.vols[0]["lane_g"]["lan_10"] = [2]
        self.vols[0]["lane_g"]["lan_11"] = [2]
    
        #Left turn through conflict map. Map the lanegroup that conflicts
        self.vols[0]["lanltc"] = []
        self.vols[0]["lanltc"].append([])
        self.vols[0]["lanltc"].append([2])
        self.vols[0]["lanltc"].append([1])
        
        #total delay
        self.vols[0]["totald"] = 0
        
        
        self.vols[0]["time"] = 0
        
        self.cycles.append([copy.deepcopy(self.vols[0])])
        
    
    '''    
    def markov_run(self, e_del, e_vol, markovruns):
        #markov run zero is the optimal, with no error.

        new_entry = []
        
        #do the zero calculations
        new_entry.append(self.calculate_add_parms(0, 0, 0))
                
        for i in range(1, markovruns):
            new_entry.append(self.calculate_add_parms(i, e_del, e_vol))
        
        self.cycles.append(new_entry)
    '''
    
    def get_new_parms_real(self, viss_step, base_saturation=1950, t_e=15):
        i = 0 #because this code was adapted from markov runs, here only one run though.
        cycle = self.cycles[-1][i]["cycle"]
        newtime = round(self.cycles[-1][i]["time"] + cycle/60/60, 7)
        new_entry = {} #dict to return with all the data.
        new_entry["time"] = newtime
        new_entry["vis_step"] = viss_step
        #seed newentry with existing data
        new_entry["phases"] = self.cycles[-1][i]["phases"]
        new_entry["phaseo"] = self.cycles[-1][i]["phaseo"]
        new_entry["lane_g"] = self.cycles[-1][i]["lane_g"]
        new_entry["lane_s"] = self.cycles[-1][i]["lane_s"]
        new_entry["lanltc"] = self.cycles[-1][i]["lanltc"]
        new_entry["lanegr"] = self.cycles[-1][i]["lanegr"]
        new_entry["greens"] = self.cycles[-1][i]["greens"].copy()
        new_entry["green_pl"] = self.cycles[-1][i]["green_pl"]
        
        calcs = {} #intermediate holder.
        
        calcs["lgrpps"] = []
        calcs["lgrpvl"] = []
        calcs["lngrdl"] = []
        calcs["lngrde"] = []
        calcs["lngrdt"] = []
        calcs["lngrsa"] = []
        calcs["lngrev"] = []
        calcs["lngrlc"] = []
        
        calcs["prvdev"] = {}
        calcs["calc_Y"] = {}
        calcs["calc_X"] = {}
        calcs["estvol"] = {}
        calcs["prevgr"] = {}
        calcs["prvdle"] = {}
        
        #Assign green times to lanes based on phase
        for l_num in new_entry["phases"]:
            calcs["prvdle"][l_num] = {}
            for phase_i in self.cycles[-1][i]["phases"][l_num]:
                if not l_num in calcs["prevgr"]:
                    calcs["prevgr"][l_num] = self.cycles[-1][i]["greens"][phase_i]
                else: 
                    calcs["prevgr"][l_num] += self.cycles[-1][i]["greens"][phase_i]
        
        #seed the lanegroup stuff
        for lanegroup_i in range(0, len(new_entry["lanegr"])):
            calcs["lgrpvl"].append({"T":0, "R":0, "L":0})
            calcs["lngrdl"].append({"T":0, "R":0, "L":0})
            calcs["lngrde"].append({"T":0, "R":0, "L":0})
            calcs["lngrdt"].append({"T":0, "R":0, "L":0})
            calcs["lngrsa"].append({"T":0, "R":0, "L":0})
            calcs["lngrev"].append({"T":0, "R":0, "L":0})
            calcs["lngrlc"].append({"T":0, "R":0, "L":0})
            calcs["lgrpps"].append({"T":[], "R":[], "L":[]})
        
        #assigns and calculates the travle times and saturations based on obs.
        self.VissimControl.Data.VehicleDetectors.matchVehicles() #match vehilces in the TT record
        
        #obtain travel times / vols for NB etc
        matched_datas = {}
        matched_datas["FRN"] = self.VissimControl.Data.VehicleDetectors.ReturnMovementTimes("bluetoothnorth")
        matched_datas["FES"] = self.VissimControl.Data.VehicleDetectors.ReturnMovementTimes("bluetootheast")
        matched_datas["FWS"] = self.VissimControl.Data.VehicleDetectors.ReturnMovementTimes("bluetoothwest")
        
        #north side
        calcs["lngrdt"][0]["T"] = 0
        calcs["lngrsa"][0]["T"] = 0
        if "bluetoothnorthTObluetootheast" in matched_datas["FRN"]:
            calcs["lngrdt"][0]["L"] = matched_datas["FRN"]["bluetoothnorthTObluetootheast"]["delay"][0]/10
        else:
            calcs["lngrdt"][0]["L"] = 0
        calcs["lngrsa"][0]["L"] = 0
        if "bluetoothnorthTObluetoothwest" in matched_datas["FRN"]:
            calcs["lngrdt"][0]["L"] = matched_datas["FRN"]["bluetoothnorthTObluetoothwest"]["delay"][0]/10
        else:
            calcs["lngrdt"][0]["L"]
        calcs["lngrsa"][0]["R"] = 0
        
        #east side
        if "bluetootheastTObluetoothwest" in matched_datas["FES"]:
            calcs["lngrdt"][1]["T"] = matched_datas["FES"]["bluetootheastTObluetoothwest"]["delay"][0]/10
        else:
            calcs["lngrdt"][1]["T"] = 0
        calcs["lngrsa"][1]["T"] = base_saturation
        calcs["lngrdt"][1]["L"] = 0
        calcs["lngrsa"][1]["L"] = 0
        if "bluetootheastTObluetoothnorth" in matched_datas["FES"]:
            calcs["lngrdt"][1]["L"] = matched_datas["FES"]["bluetootheastTObluetoothnorth"]["delay"][0]/10
        else:
            calcs["lngrdt"][1]["L"] = 0
        calcs["lngrsa"][1]["R"] = 0
        
        #west side
        if "bluetoothwestTObluetootheast" in matched_datas["FWS"]:
            calcs["lngrdt"][2]["T"] = matched_datas["FWS"]["bluetoothwestTObluetootheast"]["delay"][0]/10
        else:
            calcs["lngrdt"][2]["T"] = 0
        calcs["lngrsa"][2]["T"] = base_saturation
        if "bluetoothwestTObluetoothnorth" in matched_datas["FWS"]:
            calcs["lngrdt"][2]["L"] = matched_datas["FWS"]["bluetoothwestTObluetoothnorth"]["delay"][0]/10
        else:
            calcs["lngrdt"][2]["L"] = 0
        calcs["lngrsa"][2]["L"] = 0
        calcs["lngrdt"][2]["L"] = 0
        calcs["lngrsa"][2]["R"] = 0
        
        #calculate the estimated volume of the through lane based on the estimated time
        for lanegroup_i in range(0, len(new_entry["lanegr"])):
            #find the corresponding phase for the lanegroup.
            for lk_phase_i in range(0, len(new_entry["phaseo"])):
                found_item = False
                for item in new_entry["phaseo"][lk_phase_i]:
                    if item == lanegroup_i:       
                        #assign the phase variable and break out
                        phase = new_entry["phaseo"][lk_phase_i]
                        found_item = True
                        break
                if found_item: break #double break
            
            #count the types of lanes
            through_lanes = 0
            right_lanes = 0
            left_lanes = 0
            for l_num in new_entry["lanegr"][lanegroup_i]:
                if "R" in new_entry["lane_s"][l_num]:
                    right_lanes += 1
                if "L" in new_entry["lane_s"][l_num]:
                    left_lanes += 1
                if "T" in new_entry["lane_s"][l_num]:
                    through_lanes += 1
            calcs["lngrlc"][lanegroup_i]["T"] = through_lanes
            calcs["lngrlc"][lanegroup_i]["R"] = right_lanes
            calcs["lngrlc"][lanegroup_i]["L"] = left_lanes
                    
            if not calcs["lngrlc"][lanegroup_i]["T"] == 0:
                calcs["lngrev"][lanegroup_i]["T"] = self.golden_section_flowrate(calcs["lngrsa"][lanegroup_i]["T"], t_e, new_entry["greens"][lk_phase_i], cycle, calcs["lngrdt"][lanegroup_i]["T"])
        
        #now estimate the volumes of other lanes according to the delayed estimates
        for lanegroup_i in range(0, len(new_entry["lanegr"])):
            self.EstimateVols_unit(new_entry, lanegroup_i, calcs, cycle, base_saturation, t_e)
        
        #adjust the split.
        if self.opt_mode == 0:
            cycle = self.SelectSplit(i, new_entry, calcs, cycle)
        elif self.opt_mode == 1:
            for item in new_entry["green_pl"]:
                if item[0] >= newtime:
                    break
                new_entry["greens"] = item[1]
        
        #choose what to save.
        #self.cycles[-1][i]["Xs"] = calcs["Xs"]
        #self.cycles[-1][i]["Caps"] = calcs["prvcap"]
        #self.cycles[-1][i]["d1s"] = calcs["prvdl1"]
        #self.cycles[-1][i]["d2s"] = calcs["prvdl2"]
        self.cycles[-1][i]["dts"] = calcs["lngrdt"]
        
        new_entry["cycle"] = cycle
        
        self.cycles.append([new_entry])
        
        return new_entry
        
    '''
    #generates the calcs based on saturation, which must be provided, and volume.
    #legacy method
    def GenerateCalcs(self, calcs, saturation, l_num, e_vol, e_dev, t_e, cycle, volval, direc):
        #calculate the delay and back-estimate the volume and saturation.
        if not l_num in calcs["satura"]: #create dict to hold direc-based
            calcs["satura"][l_num] = {}
            calcs["prvcap"][l_num] = {}
            calcs["errorv"][l_num] = {}
            calcs["errovo"][l_num] = {}
            calcs["errcap"][l_num] = {}
            calcs["errsrt"][l_num] = {}
            calcs["errint"][l_num] = {}
            calcs["Xs"][l_num] = {}
            calcs["prvdlt"][l_num] = {}
            calcs["prvdl2"][l_num] = {}
            calcs["prvdl1"][l_num] = {}
            if self.delay_mode == 0:
                calcs["errors"][l_num] = {}
                calcs["prvdle"][l_num] = {}
        
        calcs["satura"][l_num][direc] = saturation
        calcs["prvcap"][l_num][direc] = saturation * (calcs["prevgr"][l_num] + 1)/cycle
        calcs["Xs"][l_num][direc] = volval / calcs["prvcap"][l_num][direc]
        
        #generate volume errors depending on mode
        if self.vol_e_mode == 1 and not self.mixmode == 0:
            calcs["errorv"][l_num][direc] = numpy.random.normal(0, e_vol*volval, 1)[0]
        else:
            calcs["errorv"][l_num][direc] = numpy.random.normal(0, e_vol, 1) #generate the volume error. Estimate Y based on that error.
        
        #generate volume values depending on mixmode and get saturation.
        if not self.mixmode == 0:
            #generate associated values for the volume
            calcs["errovo"][l_num][direc] = volval + calcs["errorv"][l_num][direc]
            calcs["errcap"][l_num][direc] = saturation * (calcs["prevgr"][l_num] + 1)/cycle
            calcs["errsrt"][l_num][direc] = calcs["errovo"][l_num][direc] / calcs["errcap"][l_num][direc] #estimated X from volume counts.
            calcs["errint"][l_num][direc] = self.flowrate_estimate(saturation, t_e, calcs["prevgr"][l_num], cycle, 0, calcs["Xs"][l_num][direc])
        else:
            calcs["errint"][l_num][direc] = None
    
        
        #estimate the base delays if we need to
        
        res = self.flowrate_estimate(saturation, t_e, calcs["prevgr"][l_num], cycle, 0, calcs["Xs"][l_num][direc])
        calcs["prvdlt"][l_num][direc] = res["dt"]
        calcs["prvdl2"][l_num][direc] = res["d2"]
        calcs["prvdl1"][l_num][direc] = res["d1"]
        if self.delay_mode == 0: 
            calcs["errors"][l_num][direc] = numpy.random.normal(0, e_dev, 1) #generate the errors for delays.
            calcs["prvdle"][l_num][direc] = calcs["prvdlt"][l_num][direc] + calcs["errors"][l_num][direc]
    '''
    
    
    def EstimateVols_unit(self, new_entry, adjlanegroup_i, calcs, cycle, base_saturation, t_e):
        #find the corresponding phase for the lanegroup.
        for phase_i in range(0, len(new_entry["phaseo"])):
            found_item = False
            for item in new_entry["phaseo"][phase_i]:
                if item == adjlanegroup_i:       
                    #generate the true delays
                    phase = new_entry["phaseo"][phase_i]
                    found_item = True
                    break
            if found_item: break #double break
        
        for direc in calcs["lngrdt"][adjlanegroup_i]:
            if calcs["lngrlc"][adjlanegroup_i][direc] == 0: continue #skip those with no entry
            F_r = 0
            F_l = 0
            F_f = 0 #final
            RTOI = 0
            LTOI = 0
            if direc == "R":
                F_r = 1
            if direc == "L":
                LTOI = 1 #1 per lane
                #check if permissive
                left_permissive = False
                if len(new_entry["lanltc"][adjlanegroup_i]) > 0:
                    left_permissive = True
                
                if left_permissive:
                    q_o = 0
                    for lanegrpc_i in new_entry["lanltc"][adjlanegroup_i]:
                        #conflict is the through movement
                        q_o += calcs["lngrev"][lanegrpc_i]["T"]["Dem"] #add the estimated through volume
                        
                    prev_g_e = new_entry["greens"][phase_i] + 1
                    q_o = q_o * cycle / prev_g_e
                    F_l = 1.08*(math.exp(0.00121*self.f_q[len(new_entry["lanltc"])]*q_o)) - 0.05
                else:
                    F_l = 1
                    
            F_f = F_r + F_l
            S_f = base_saturation * F_f
            if direc == "R":
                calcs["lngrsa"][adjlanegroup_i]["R"] = S_f #per lane #* calcs["lngrlc"][adjlanegroup_i]["R"]
                calcs["lngrev"][adjlanegroup_i]["R"] = self.golden_section_flowrate(calcs["lngrsa"][adjlanegroup_i]["R"], t_e, new_entry["greens"][phase_i], cycle, calcs["lngrdt"][adjlanegroup_i]["R"])
            elif direc == "L":
                calcs["lngrsa"][adjlanegroup_i]["L"] = S_f #per lane #* calcs["lngrlc"][adjlanegroup_i]["L"]
                calcs["lngrev"][adjlanegroup_i]["L"] = self.golden_section_flowrate(calcs["lngrsa"][adjlanegroup_i]["L"], t_e, new_entry["greens"][phase_i], cycle, calcs["lngrdt"][adjlanegroup_i]["L"])
            else:
                continue #already estimated through movements.
            
        for l_num in new_entry["lanegr"][adjlanegroup_i]:
            if not l_num in calcs["prvdev"]:
                calcs["prvdev"][l_num] = {"T":{}, "R":{}, "L":{}, "F":{}}
                
            if "L" in new_entry["lane_s"][l_num]:
                direc = "L"
                TOI = LTOI
            elif "R" in new_entry["lane_s"][l_num]:
                direc = "R"
                TOI = RTOI
            else:
                direc = "T"
                TOI = 0
            
            
            calcs["prvdev"][l_num]["F"]["Dem"] = calcs["lngrev"][adjlanegroup_i][direc]["Dem"] / calcs["lngrlc"][adjlanegroup_i][direc]
            calcs["prvdev"][l_num]["F"]["Y"] = calcs["lngrev"][adjlanegroup_i][direc]["Y"]
            calcs["prvdev"][l_num]["F"]["X"] = calcs["lngrev"][adjlanegroup_i][direc]["X"]
            calcs["prvdle"][l_num]["F"] = calcs["lngrdt"][adjlanegroup_i][direc]
            #vol_val = new_entry["lane_s"][l_num][direc] * calcs["vols"][l_num]
            Sat_c = calcs["lngrsa"][adjlanegroup_i][direc]/calcs["lngrlc"][adjlanegroup_i][direc]
            #self.GenerateCalcs(calcs, Sat_c, l_num, e_vol, e_dev, t_e, cycle, vol_val, "F")
            self.GetEstimatedGoldens(Sat_c, t_e, calcs, cycle, l_num, "F", TOI) 
                    
    '''            
    #calculates the true delay, adds the error, the estimates the through volume based on the errored delay.
    def GetEstDelayThrough_unit(self, new_entry, adjlanegroup_i, calcs, cycle, base_saturation, t_e):        #calculate saturation, pre-seed with zero
        #find the corresponding phase for the lanegroup.
        for phase_i in range(0, len(new_entry["phaseo"])):
            found_item = False
            for item in new_entry["phaseo"][phase_i]:
                if item == adjlanegroup_i:       
                    #assign the phase variable and break out
                    phase = new_entry["phaseo"][phase_i]
                    found_item = True
                    break
            if found_item: break #double break
        
        weighted_delay_avg = {"T":0, "R":0, "L":0}
        weighted_delay_cnt = {"T":0, "R":0, "L":0}
        through_lanes = 0
        right_lanes = 0
        left_lanes = 0
        
        for l_num in new_entry["lanegr"][adjlanegroup_i]:
            F_r = 0
            F_l = 0
            F_f = 0 #final
            vol_val_l = 0
            vol_val_r = 0
            vol_val_t = 0
            RTOI = 0
            LTOI = 0
            #base factors
            if "R" in new_entry["lane_s"][l_num]:
                right_lanes += 1
                F_r = 1
            if "L" in new_entry["lane_s"][l_num]:
                left_lanes += 1
                LTOI = 1 #1 per lane
                #check if permissive
                left_permissive = False
                if l_num in new_entry["lanltc"]:
                    #can be permissive because a conflict is defined.
                    #go into lanegroup
                    for lanegroup_i in phase:
                        #check if the conflict lane is in any other lanegroup timing in this phase
                        if any(x in new_entry["lanltc"] for x in new_entry["lanegr"][lanegroup_i]):
                            #a conflict exists
                            left_permissive = True
                            break
                
                if left_permissive:
                    q_o = 0
                    for lanegrpc_i in new_entry["lanltc"][adjlanegroup_i]:
                        #conflict is the through movement
                        q_o += calcs["lgrpvl"][lanegrpc_i]["T"]
                        
                    prev_g_e = new_entry["greens"][phase_i] + 1
                    q_o = q_o * cycle / prev_g_e
                    F_l = 1.08*(math.exp(0.00121*self.f_q[len(new_entry["lanltc"])]*q_o)) - 0.05
                else:
                    F_l = 1
            if "T" in new_entry["lane_s"][l_num] and len(new_entry["lane_s"][l_num]) == 1:
                through_lanes += 1 #count exclusive through lanes.
            
            #determine the "TRUE" volumes and delays
            #this section is deprecated, as no shared lanes.
            if len(new_entry["lane_s"][l_num]) > 1:
                #no inter-green turns on shared lanes
                K_l = 0
                K_r = 0
                
                #shared lanes and we need to combine
                if "T" in new_entry["lane_s"][l_num] and "L" in new_entry["lane_s"][l_num] and "R" in new_entry["lane_s"][l_num]:
                    #in the triple case fold into the combination with the higher split
                    S_t = calcs["satura"][l_num]["T"]
                    S_l = base_saturation * F_l
                    S_r = base_saturation * F_r
                    K_l = S_t / S_l
                    K_r = S_t / S_r
                    
                    vol_val_r = new_entry["lane_s"][l_num]["R"] * calcs["vols"][l_num]
                    q_r = K_r * vol_val_r
                    vol_val_l = new_entry["lane_s"][l_num]["L"] * calcs["vols"][l_num]                    
                    q_l = K_l * vol_val_l
                    vol_val_t = new_entry["lane_s"][l_num]["T"] * calcs["vols"][l_num]
                    
                    if q_l >= q_r:
                        q_o = q_l
                        K_o = K_l
                        q_t = vol_val_r + vol_val_t
                    else:
                        q_o = q_r
                        K_o = K_r
                        q_t = vol_val_l + vol_val_t
                    q_pt = q_t + q_o * K_o
                    F_f = (q_t + q_o) / (q_pt)
                    S_f = base_saturation * F_f
                elif "R" in new_entry["lane_s"][l_num] and "T" in new_entry["lane_s"][l_num]:
                    S_t = calcs["satura"][l_num]["T"]
                    S_r = base_saturation * F_r
                    vol_val_r = new_entry["lane_s"][l_num]["R"] * calcs["vols"][l_num]
                    vol_val_t = new_entry["lane_s"][l_num]["T"] * calcs["vols"][l_num]
                    q_r = vol_val_r
                    q_t = vol_val_t
                    
                    K_r = S_t / S_r 
                    q_pt = q_t + q_r * K_r
                    F_f = (q_r + q_t) / (q_pt)
                    S_f = base_saturation * F_f
                    
                elif "R" in new_entry["lane_s"][l_num] and "L" in new_entry["lane_s"][l_num]:
                    S_l = base_saturation * F_l
                    S_r = base_saturation * F_r
                    S_t = base_saturation #use default for hypothetical through
                    vol_val_r = new_entry["lane_s"][l_num]["R"] * calcs["vols"][l_num]
                    vol_val_l = new_entry["lane_s"][l_num]["L"] * calcs["vols"][l_num]
                    q_r = vol_val_r
                    q_l = vol_val_l
                    K_r = S_t / S_r 
                    K_l = S_t / S_l
                    q_pt = q_l * K_l + q_r * K_r
                    F_f = (q_r + q_l) / (q_pt)
                    S_f = base_saturation * F_f
                    
                elif "L" in new_entry["lane_s"][l_num] and "T" in new_entry["lane_s"][l_num]:
                    S_t = calcs["satura"][l_num]["T"]
                    S_l = base_saturation * F_l
                    vol_val_l = new_entry["lane_s"][l_num]["L"] * calcs["vols"][l_num]
                    vol_val_t = new_entry["lane_s"][l_num]["T"] * calcs["vols"][l_num]
                    q_l = vol_val_l
                    q_t = vol_val_t
                    K_l = S_t / S_l
                    q_pt = q_t + q_l * K_l
                    F_f = (q_l + q_t) / (q_pt)
                    S_f = base_saturation * F_f
                else:
                    print("Some non-normal lane combination? Check!")
                    input()
                                                    
            else:
                F_f = F_r + F_l
                S_f = base_saturation * F_f
                if "R" in new_entry["lane_s"][l_num]:
                    vol_val_r = new_entry["lane_s"][l_num]["R"] * calcs["vols"][l_num]  
                    q_pt = vol_val_r
                elif "L" in new_entry["lane_s"][l_num]:
                    vol_val_l = new_entry["lane_s"][l_num]["L"] * calcs["vols"][l_num] - calcs["avol"][l_num]
                    if vol_val_l > S_f: #the left turn is over-saturated
                        if len(new_entry["lane_g"][l_num]) > 1:
                            calcs["avol"][l_num] = S_f
                            q_pt = S_f
                    q_pt = vol_val_l
                    calcs["avol"][l_num] = q_pt
                else:
                    #ordinary through lane, assign S_f
                    vol_val_t = new_entry["lane_s"][l_num]["T"] * calcs["vols"][l_num]
                    q_pt = vol_val_t
                    S_f = base_saturation

            weighted_delay_cnt["L"] += vol_val_l
            weighted_delay_cnt["T"] += vol_val_t
            weighted_delay_cnt["R"] += vol_val_r
            #determine true delay
            calcs["prevgr"][l_num] = new_entry["greens"][phase_i] #assign the green as this phase.
            self.GenerateCalcs(calcs, S_f, l_num, e_vol, e_dev, t_e, cycle, q_pt, "F")           
            weighted_delay_avg["L"] += calcs["prvdlt"][l_num]["F"] * vol_val_l
            weighted_delay_avg["T"] += calcs["prvdlt"][l_num]["F"] * vol_val_t
            weighted_delay_avg["R"] += calcs["prvdlt"][l_num]["F"] * vol_val_r
        
        if weighted_delay_cnt["L"] == 0: calcs["lngrdl"][adjlanegroup_i]["L"] = 0
        else: calcs["lngrdl"][adjlanegroup_i]["L"] = weighted_delay_avg["L"] / weighted_delay_cnt["L"]
        if weighted_delay_cnt["T"] == 0: calcs["lngrdl"][adjlanegroup_i]["T"] = 0
        else: calcs["lngrdl"][adjlanegroup_i]["T"] = weighted_delay_avg["T"] / weighted_delay_cnt["T"]
        if weighted_delay_cnt["R"] == 0: calcs["lngrdl"][adjlanegroup_i]["R"] = 0
        else: calcs["lngrdl"][adjlanegroup_i]["R"] = weighted_delay_avg["R"] / weighted_delay_cnt["R"]
        calcs["lngrde"][adjlanegroup_i]["L"] = numpy.random.normal(0, e_dev, 1)
        calcs["lngrde"][adjlanegroup_i]["T"] = numpy.random.normal(0, e_dev, 1)
        calcs["lngrde"][adjlanegroup_i]["R"] = numpy.random.normal(0, e_dev, 1)
        calcs["lngrdt"][adjlanegroup_i]["L"] = calcs["lngrdl"][adjlanegroup_i]["L"] + calcs["lngrde"][adjlanegroup_i]["L"]
        calcs["lngrdt"][adjlanegroup_i]["T"] = calcs["lngrdl"][adjlanegroup_i]["T"] + calcs["lngrde"][adjlanegroup_i]["T"]
        calcs["lngrdt"][adjlanegroup_i]["R"] = calcs["lngrdl"][adjlanegroup_i]["R"] + calcs["lngrde"][adjlanegroup_i]["R"]
        
        #total real delay
        calcs["totald"] += calcs["lngrdl"][adjlanegroup_i]["L"] * (weighted_delay_cnt["L"]/3600*cycle)
        calcs["totald"] += calcs["lngrdl"][adjlanegroup_i]["R"] * (weighted_delay_cnt["R"]/3600*cycle)   
        calcs["totald"] += calcs["lngrdl"][adjlanegroup_i]["T"] * (weighted_delay_cnt["T"]/3600*cycle)   
        calcs["lngrsa"][adjlanegroup_i]["T"] = base_saturation #*through_lanes
        calcs["lngrlc"][adjlanegroup_i]["T"] = through_lanes
        calcs["lngrlc"][adjlanegroup_i]["R"] = right_lanes
        calcs["lngrlc"][adjlanegroup_i]["L"] = left_lanes
        
        if not calcs["lngrlc"][adjlanegroup_i]["T"] == 0:
            calcs["lngrev"][adjlanegroup_i]["T"] = self.golden_section_flowrate(calcs["lngrsa"][adjlanegroup_i]["T"], t_e, new_entry["greens"][phase_i], cycle, calcs["lngrdt"][adjlanegroup_i]["T"])
          
    '''
    
    def ChangeCycle(self, cycle, times, effective_green_times, ratios):
        L = cycle - sum(effective_green_times.values())
        Y = sum(ratios.values())
        if Y > 1: Y = 0.99 #maximum cap. Oversaturated intersection
        min_c = L/(1-Y)
        opt_c = (1.5*L+5) / (1-Y)
        if opt_c < min_c: opt_c = min_c #use the minimum cycle if the opt is less.
        
        #determine new cycle
        distance = opt_c - cycle
        span = self.gammaC
        gradient = distance/span
        gradient = gradient / ((self.betaC+gradient**2)**0.5) * self.gammaC
        gradient = round(gradient)
        #prevent the cycle from exceeding limits
        if gradient + cycle > self.maxC:
            gradient = self.maxC - cycle
        elif gradient + cycle < self.minC:
            gradient = self.minC - cycle
        else:
            cycle += gradient
        
        #determine adjustments to green
        total_g = sum(times)
        alloc = gradient
        while alloc > 0:
            #allocate 1 second at a time to each phase that deviates the most.
            #recalculate the deviation after every second.
            max_dev = 999999
            max_dev_i = -1
            for item in range(0, len(times)):
                if times[item] == self.maxG: continue #skip max values
                optg_ei = ratios[item] / Y 
                optg_ei = optg_ei * total_g
                devg_ei = times[item] - optg_ei
                #only suggest phases that are below optimal.
                if devg_ei < max_dev:
                    max_dev = devg_ei
                    max_dev_i = item
                
            alloc -= 1
            times[max_dev_i] += 1
            total_g += 1
        
        while alloc < 0:
            #subtract 1 second at a time from the phase that deviates the most:
            max_dev = -999999
            max_dev_i = -1
            for item in range(0, len(times)):
                if times[item] == self.minG: continue #skip min values
                optg_ei = ratios[item] / Y 
                optg_ei = optg_ei * total_g
                devg_ei = times[item] - optg_ei
                #only suggest phases that are below optimal.
                if devg_ei > max_dev:
                    max_dev = devg_ei
                    max_dev_i = item
            
            alloc += 1
            times[max_dev_i] -= 1
            total_g -= 1
                
        
        return (cycle, times)
        
        
    #def SelectSplit(self, time_NB, time_WB, delay_NB, delay_WB, golden_volA, golden_volB, cycletime, saturation, t_e):
    def GetEstimatedGoldens(self, saturation, t_e, calcs, cycletime, l_num, direc, aux):
        if not l_num in calcs["calc_Y"]: #create dict to hold direc-based
            calcs["calc_Y"][l_num] = {}
            calcs["calc_X"][l_num] = {}
            calcs["estvol"][l_num] = {}
        #mixes Y if needed, otherwise returns the X and Y according to the values requested.
        golden_results = self.golden_section_flowrate(saturation, t_e, calcs["prevgr"][l_num], cycletime, calcs["prvdle"][l_num][direc], aux)
        calcs["calc_Y"][l_num][direc] = golden_results["Y"]
        calcs["calc_X"][l_num][direc] = golden_results["X"]
        calcs["estvol"][l_num][direc] = golden_results["Dem"]
        
    def SelectSplit(self, i, new_entry, calcs, cycletime):
        #(newgrs, self.cycles[-1][i]["Ys"], self.cycles[-1][i]["X_ests"], ideals, cycle) 
        #= self.SelectSplit(greents, prvdlvs, volervl, cycle, saturation, t_e)
        
        max_y = {}
        grees = {}
        
        for phase_i in range(0, len(self.cycles[-1][i]["phaseo"])):
            max_y[phase_i] = 0
            phase = self.cycles[-1][i]["phaseo"][phase_i]
            grees[phase_i] = new_entry["greens"][phase_i] + 1
            for lanegroup in phase:
                for lane in new_entry["lanegr"][lanegroup]:
                    if calcs["calc_Y"][lane]["F"] > max_y[phase_i]:
                        max_y[phase_i] = calcs["calc_Y"][lane]["F"]
        
        total_Y = sum(max_y.values())
        if total_Y < self.minY:
            return cycletime #shortturn, no modification if Y below threshold, there may not be enough volume to accurately estimate the delay.
        
        #check if we are changing the cycle length and adjust
        if self.cyclemode == 1:
            (cycletime, new_entry["greens"]) = self.ChangeCycle(cycletime, new_entry["greens"], grees, max_y)
        
        
        galloc = sum(new_entry["greens"])
        idealr = {} #ideal ratio
        idealt = {} #ideal time
        adjval = {} #adjustment
        graabs = {} #gradient score
        for phase_i in range(0, len(new_entry["greens"])):
            
            #calculate the ideal ratio and green times based on above
            idealr[phase_i] = max_y[phase_i] / total_Y
            
            idealt[phase_i] = round(idealr[phase_i] * galloc)
            distance = idealt[phase_i] - new_entry["greens"][phase_i]
            span = self.gamma
            gradient = distance/span
            graabs[phase_i] = gradient / ((self.beta+gradient**2)**0.5) * self.gamma #save unrounded for comparison
            gradient = round(graabs[phase_i])
            graabs[phase_i] = abs(graabs[phase_i]) #convert ot absolute value as score
            
            if new_entry["greens"][phase_i] + gradient < self.minG: #we cannot reduce below the min green
                adj_grad = self.minG - (new_entry["greens"][phase_i] + gradient)
                gradient += adj_grad
                graabs[phase_i] -= adj_grad #we have adjusted the gradient by this value

            adjval[phase_i] = gradient
            
        imbalance = sum(adjval.values())
        while imbalance > 0: #net increase
            #subtract until we arrive at the correct value.
            minkey= None
            minval = 99999
            for phase_i in range(0, len(new_entry["greens"])):
                #find the highest adjustment that had the worse rounding
                rounded = graabs[phase_i] - abs(adjval[phase_i])
                if rounded < minval and new_entry["greens"][phase_i] > self.minG:
                    minval = rounded
                    minkey = phase_i
                
            adjval[minkey] -= 1
            imbalance -= 1
        while imbalance < 0: #net decrease
            #add until we arrive at the correct value.
            minkey= None
            minval = -99999
            for phase_i in range(0, len(new_entry["greens"])):
                #find the highest adjustment that had the best rounding
                rounded = graabs[phase_i] - abs(adjval[phase_i])
                if rounded > minval:
                    minval = rounded
                    minkey = phase_i
                
            adjval[minkey] += 1
            imbalance += 1            
        
        #adjust the phase values.   
        for phase in adjval:
            new_entry["greens"][phase] += adjval[phase]
            
        self.cycles[-1][i]["ideals"] = idealr
        
        return cycletime
        
    
    def get_mixedY(self, golden_results_del, delay_meas, golden_results_vol):
        est_error_del_s = self.del_err_est
        est_error_vol_p = self.vol_err_est
        
        #combine according to the MLE 
        #determine what the standard deviation of the errors are in terms of Y
        sdev_del_int_p = self.golden_section_flowrate(golden_results_del["S"], golden_results_del["te"], golden_results_del["g"], golden_results_del["c"], delay_meas + est_error_del_s)
        sdev_del_int_m = self.golden_section_flowrate(golden_results_del["S"], golden_results_del["te"], golden_results_del["g"], golden_results_del["c"], delay_meas - est_error_del_s)
        if sdev_del_int_p["Dem"] * sdev_del_int_m["Dem"] == 0:
            #the measurement is unreliable as one of them is below the "zero" demand
            w_vol = 1
            w_del = 0
        else:
            del_int_r = (sdev_del_int_p["Dem"] - sdev_del_int_m["Dem"])/2 #the range across 1 standard deviation.
            if del_int_r == 0: #the calculation shows that the delay measurement has near no error
                w_del = 1
                w_vol = 0
            else:
                w_del = (del_int_r / (del_int_r + est_error_vol_p*golden_results_vol["Dem"]))**(-1)
                w_vol = (est_error_vol_p*golden_results_vol["Dem"] / (del_int_r + est_error_vol_p*golden_results_vol["Dem"]))**(-1)
        
        wei_y = (golden_results_del["Y"] * w_del + golden_results_vol["Y"] * w_vol) / (w_vol + w_del)
        wei_x = (golden_results_del["X"] * w_del + golden_results_vol["X"] * w_vol) / (w_vol + w_del)
        wei_dem = (golden_results_del["Dem"] * w_del + golden_results_vol["Dem"] * w_vol) / (w_vol + w_del)
        return wei_y, wei_x, wei_dem
        
        
    def write_results(self, fileloc):
        with open(fileloc + "results.csv", "w") as csvwrite, open(fileloc + "gtime.csv", "w") as timescsv, open(fileloc + "goptime.csv", "w") as timedcsv, open(fileloc + "ctimes.csv", "w") as timeccsv:
            #do the header first
            entry = self.cycles[0]
            first = True
            col = 0
            for column in entry:
                if not first:
                    timescsv.write(",")
                    timedcsv.write(",")
                    timeccsv.write(",")
                timescsv.write("sig_" + str(col))
                timedcsv.write("sig_" + str(col))
                timeccsv.write("sig_" + str(col))
                for item in sorted(column):
                    if item in self.DNRLABS:
                        continue #skip labels not interested in.
                    if isinstance(column[item],dict):
                        for sitem in sorted(column[item]):
                            if isinstance(column[item][sitem],dict):
                                for sitemu in sorted(column[item][sitem]):
                                    if first:
                                        first = False
                                    else:
                                        csvwrite.write(",")
                                    csvwrite.write(str(item) + "_" + str(sitem) + str(sitemu))
                            else:
                                if first:
                                    first = False
                                else:
                                    csvwrite.write(",")
                                csvwrite.write(str(item) + "_" + str(sitem))
                    elif isinstance(column[item],list):
                        for sitem in range(0, len(column[item])):
                            if first:
                                first = False
                            else:
                                csvwrite.write(",")
                            csvwrite.write(str(item) + "_" + str(sitem))
                    else:
                        if first:
                            first = False
                        else:
                            csvwrite.write(",")
                        csvwrite.write(str(item))
                        #csvwrite.write("_r" + str(col))
                col += 1
            csvwrite.write("\n")
            timescsv.write("\n")
            timedcsv.write("\n")
            timeccsv.write("\n")
            
            #write the data
            for entry in self.cycles:
                first = True
                for column in entry:
                    if not first:
                        timescsv.write(",")
                        timedcsv.write(",")
                        timeccsv.write(",")
                    timescsv.write(str(column["greens"][0]))
                    timedcsv.write(str(column["time"]))
                    timeccsv.write(str(column["cycle"]))
                    
                    for item in sorted(column):
                        if item in self.DNRLABS:
                            continue #skip labels not interested in.
                        if isinstance(column[item],dict):
                            for sitem in sorted(column[item]):
                                if isinstance(column[item][sitem],dict):
                                    for sitemu in sorted(column[item][sitem]):
                                        if first:
                                            first = False
                                        else:
                                            csvwrite.write(",")
                                        csvwrite.write(str(column[item][sitem][sitemu]))
                                else:
                                    if first:
                                        first = False
                                    else:
                                        csvwrite.write(",")
                                    csvwrite.write(str(column[item][sitem]))
                        elif isinstance(column[item],list):
                            for sitem in range(0, len(column[item])):
                                if first:
                                    first = False
                                else:
                                    csvwrite.write(",")
                                csvwrite.write(str(column[item][sitem]))
                        else:
                            if first:
                                first = False
                            else:
                                csvwrite.write(",")
                            csvwrite.write(str(column[item]))
                timescsv.write("\n")
                csvwrite.write("\n")
                timedcsv.write("\n")
                timeccsv.write("\n")
                
                
        
    def load_volumes(self, fileloc):
        with open(fileloc, "r") as csvread:
            lineat = -1
            for line in csvread:
                lineat += 1
                row_app = {}
                if lineat == 0: #skip header
                    continue
                line = line.strip("\n").split(",")
                row_app["time"] = float(line[1])
                row_app["vols"] = {}
                for i in range(2, len(line)):
                    str_app = "lan_" + str(i-1)
                    row_app["vols"][str_app] = int(line[i])
                self.vols.append(row_app)
    
    def flowrate_estimate(self, S, te, g, c, d, X, aux=0):
        #determine the saturation flow rate given some values
        #aux is LTOI, etc.
        ge = g+1
        X1 = X if X <= 1 else 1
        Cap = S * ge/c + aux
        d1 = c*((1-ge/c)**2)/((2*(1-X1*ge/c)))
        d2 = ((X-1)+(((X-1)**2)+(240*X)/(Cap*te))**0.5)*15*te
        dt = d1+d2
        dem =  Cap * X
        return {"X": X, "Y":dem/S, "dt": dt, "Cap": Cap, "Dev": dt-d, "Dem": dem, "d1":d1, "d2":d2, "c":c, "g":g, "te":te, "S":S, "ge":ge}
    def golden_section_flowrate(self, S, te, g, c, d, aux=0):
        tol = 0.0001 # delay inaccuracy tolerance, seconds
        X = 0 #we vary X to find a matching d value
        p_a = self.flowrate_estimate(S, te, g, c, d, X, aux)
        
        #short turn if demand is lower than the zero value
        if d <= p_a["dt"]: 
            p_a["X"] = 0.1
            p_a["Y"] = (0.1*p_a["Cap"])/S
            return p_a
        
        #short turn if X is really high
        X = 2        
        p_b = self.flowrate_estimate(S, te, g, c, d, X, aux)
        if d >= p_b["dt"]: 
            return p_b
        
        gr = (5**0.5 + 1) / 2
        
        X = p_b["X"] - (p_b["X"] - p_a["X"]) / gr
        p_c = self.flowrate_estimate(S, te, g, c, d, X, aux)
        
        X = p_a["X"] + (p_b["X"] - p_a["X"]) / gr
        p_d = self.flowrate_estimate(S, te, g, c, d, X, aux)
        while abs(p_d["Dev"]) > tol:
            if abs(p_c["Dev"]) < abs(p_d["Dev"]):
                p_b = p_d
            else:
                p_a = p_c
            
            X = p_b["X"] - (p_b["X"] - p_a["X"]) / gr
            p_c = self.flowrate_estimate(S, te, g, c, d, X, aux)
        
            X = p_a["X"] + (p_b["X"] - p_a["X"]) / gr
            p_d = self.flowrate_estimate(S, te, g, c, d, X, aux)
        
        return p_d #return the overestimated value of the tolerance bound.


'''
DEPRECATED METHODS
'''
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
        
    def golden_section_flowrate(self, S, te, g, c, d):
        tol = 0.05 # delay inaccuracy tolerance, seconds
        X = 0 #we vary X to find a matching d value
        p_a = self.flowrate_estimate(S, te, g, c, d, X)
        #short turn if demand is lower than the zero value
        if d <= p_a["dt"]: return {"X": 0.1, "Y":(0.1*p_a["Cap"])/S}
        X = 2
        p_b = self.flowrate_estimate(S, te, g, c, d, X)
        if d >= p_b["dt"]: return {"X": 2.0, "Y":(2.0*p_b["Cap"])/S}
        
        gr = (5**0.5 + 1) / 2
        
        X = p_b["X"] - (p_b["X"] - p_a["X"]) / gr
        p_c = self.flowrate_estimate(S, te, g, c, d, X)
        
        X = p_a["X"] + (p_b["X"] - p_a["X"]) / gr
        p_d = self.flowrate_estimate(S, te, g, c, d, X)
        while abs(p_d["Dev"]) > tol:
            if abs(p_c["Dev"]) < abs(p_d["Dev"]):
                p_b = p_d
            else:
                p_a = p_c
            
            X = p_b["X"] - (p_b["X"] - p_a["X"]) / gr
            p_c = self.flowrate_estimate(S, te, g, c, d, X)
        
            X = p_a["X"] + (p_b["X"] - p_a["X"]) / gr
            p_d = self.flowrate_estimate(S, te, g, c, d, X)
        
        return p_d #return the overestimated value of the tolerance bound.
        
    
    def flowrate_estimate(self, S, te, g, c, d, X):
        #determine the saturation flow rate given some values
        ge = g+1
        X1 = X if X <= 1 else 1
        Cap = S * ge/c
        d1 = c*((1-ge/c)**2)/((2*(1-X1*ge/c)))
        d2 = ((X-1)+(((X-1)**2)+(240*X)/(Cap*te))**0.5)*15*te
        dt = d1+d2
        dem =  Cap * X
        return {"X": X, "Y":dem/S, "dt": dt, "Cap": Cap, "Dev": dt-d, "Dem": dem}
    
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
                            #saturation = (-(cycletime**2-2*cycletime*movement-2*cycletime*green_NB+green_NB**2)/(2*movement*green_NB))
                            #if saturation < 0.1: saturation = 0.1 #enforce a floor for the saturation.
                            #flowration = saturation*(green_NB/cycletime)
                            golden_results = self.golden_section_flowrate(1950, 10, green_NB, cycletime, movement)
                            saturation = golden_results["X"]
                            flowration = golden_results["Y"]
                            print("Movement " + str(key) + ": " + str(movement) + " Saturation: " + str(saturation) + " Flow Ration: " + str(flowration))
                            if flowration > NB_SB_crit: 
                                NB_SB_crit = flowration
                                NB_SB_crit_time = movement
                    elif dir == "EB" or dir == "WB":
                        if not movement <= 0:
                            #saturation = (-(cycletime**2-2*cycletime*movement-2*cycletime*green_WB+green_WB**2)/(2*movement*green_WB))
                            #if saturation < 0.1: saturation = 0.1 #enforce a floor for the saturation.
                            #flowration = saturation*(green_WB/cycletime)
                            golden_results = self.golden_section_flowrate(1950, 10, green_WB, cycletime, movement)
                            saturation = golden_results["X"]
                            flowration = golden_results["Y"]
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
            