'''
Created on Aug 30, 2017

@author: Matthew Muresan

Main script file. This file organizes and uses the various modules we will develop
'''

VISSIMFILE = "viss/1.inpx"

from ulib.gui import TkinterGUI



VISSIMFILE = "viss/1.inpx"
WRITELOC = "out/"
POPULATESTEPS = 1000
DETECTORFILE = "detectors.json"
STEPS = 37000
BACKUPSTEPS = 99999

def main():
    try:
        gui = TkinterGUI(VISSIMFILE, DETECTORFILE, WRITELOC, "debug", 0, 4)
    except:
        raise
    finally:
        pass
    
    
    '''
    print("Main Loop Running...")
    VissimControl = vissimconnect.VissimConnect(VISSIMFILE, DETECTORFILE, POPULATESTEPS) #main class to interact with VISSIM. See imported ulib/vissimconnect.
    VissimControl.Data.ActivateSignals(VissimControl.Vissim, VissimControl.step) #activate the signals which we are controlling.
    print("  ...Done.")
    print("Running Loop Forever")
    i = 0
    try:
        while i < STEPS:
            VissimControl.advanceSimulation()
            if i % BACKUPSTEPS == 0:
                VissimControl.Data.DumpRecords(WRITELOC)
                VissimControl.Data.DumpDirectionalTT(WRITELOC)
            
            if i % 250 == 0:
                print("Step " + str(i) + " completed")
                
            i += 1
    except:
        raise
    finally:
        print("Program End... dumping records...")
        VissimControl.Data.DumpRecords(WRITELOC)
        VissimControl.Data.DumpDirectionalTT(WRITELOC)
        

    '''
if __name__ == "__main__":
    main()