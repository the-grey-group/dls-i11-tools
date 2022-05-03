#!/usr/bin/env jython

"""This script provides an example of how to perform batches of PSD scans 
automatically loaded from a CSV file, and manual variable temperature scans.

It was written for the BAG time in March 2022 at i11.

"""

import csv
import datetime

__author__ = "Joshua Bocarsly, Matthew Evans"

######################################################################
#                        UTILITY FUNCTIONS                           #
######################################################################

def hotairup(Ttemp, logfh):
    """Ramp hot air blower up to Ttemp target, writing the results to the log file handler."""
    caput("BL11I-EA-BLOW-02:LOOP1:SP",Ttemp)
    for i in range(1000):
        scan delta 2 2.25 0.25 smythen 6
        temp = csb2.currentTemperature
        line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
        logfh.write(line)
        logfh.flush()
        if csb2.currentTemperature > Ttemp - 0.5 :
            for j in range(5):
                print "last 5 scans"
                scan delta 2 2.25 0.25 smythen 6
                temp = csb2.currentTemperature
                line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
                logfh.write(line)
                logfh.flush()
            break

def hotairdown(Ttemp, logfh):
    """Ramp hot air blower down to Ttemp target, writing the results to the log file handler."""
    caput("BL11I-EA-BLOW-02:LOOP1:SP",Ttemp)
    for i in range(1000):
        scan delta 2 2.25 0.25 smythen 6
        temp = csb2.currentTemperature
        line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
        logfh.write(line)
        logfh.flush()
        if csb2.currentTemperature < Ttemp + 1 :
            for j in range(5):
                print "last 5 scans"
                scan delta 2 2.25 0.25 smythen 6
                temp = csb2.currentTemperature
                line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
                logfh.write(line)
                logfh.flush()
            break

############################################################################################################
           
# Turn on the beam
bm.on()

# Move the sample table
pos tlx 300

# Pick up the first sample
sample.start()
#sample.recover()

# Turn on the spinner
spin.on()

# Open the log file in append mode (replace the path with the corre
experiment_number = "cy28349-9"

fh = open('/dls/i11/data/2022/cy28349-9/processing/Grey_BAG_31Mar22.log','a')

print('Grey Sample start')
print('starting PSD scans')

# The CSV file that contains the list of samples to process in this run
# This should be copied to the relevant directory on the DLS filesytem
# The csv file can be found in the same directory as this script, if you are 
# viewing it in the the-grey-group/dls-i11-tools repo on GitHub
csv_filepath = '/dls/i11/data/2022/cy28349-9/processing/PSD_RT_MainBatch.csv'

fh.write('running PSD scans at room temp from %s:\n', csv_filepath)
fh.flush()

with open(csv_filepath, 'r') as csvfile:
    rowreader = csv.reader(csvfile)
    for count, row in enumerate(rowreader):
        # Skip header row
        if count > 0:
            # if row[0][0] == '#': continue
            position = int(row[0])
            sample_id = row[1]
            time = float(row[2])
            samplepos = float(row[3])

            pos sample position
            pos spos samplepos
            scan delta 2 2.25 0.25 smythen time
            fh.write('{} {} {} {} seconds PSD scan at room temperature, spos = {} mm, {} \n'.format(
                long(beamline.getFileNumber()), 
                sample_id, 
                position, 
                2*time,
                samplepos,
                datetime.datetime.now())
            )
            fh.flush()
            sleep(2)

sample.clearSample()


# run VT heating scans on some particular samples (here, 50, then 10, 11, 12 and 13)
fh.write('Running VT TEST on CC LNO-2\n')
fh.write('\tsample placed into HAB at 30C, and start ramping to 40 C\n')
fh.write('\tsee log file: CCLNO_heating_test.log\n')
fh.flush()

setSubdirectory('CCLNO_heating_test.log')
logfh = open('/dls/i11/data/2022/cy28349-9/processing/CCLNO_heating_test.log','a')
pos sample 50
pos tlx 0
caput("BL11I-EA-BLOW-02:LOOP1:RR", 0.2) #ramp rate ~12 deg/min
hotairup(40, logfh) # measure from 30 C to 600 C
hotairdown(30, logfh) # measure from 30 C to 600 C
logfh.close()
pos tlx 300

fh.write('Running VT on FHTO1\n')
fh.write('\tsample placed into HAB at 30C, and start ramping to 600 C\n')
fh.write('\tsee log file: FHT01_heating.log\n')
fh.flush()

setSubdirectory('FHT01_heating_30C-600C')
logfh = open('/dls/i11/data/2022/cy28349-9/processing/FHT01_heating_30C_to_600C.log','a')
pos sample 10
pos tlx 0
caput("BL11I-EA-BLOW-02:LOOP1:RR", 0.2) #ramp rate ~12 deg/min
hotairup(600, logfh) # measure from 30 C to 600 C
hotairdown(30, logfh) # measure from 30 C to 600 C
logfh.close()
pos tlx 300


fh.write('Running VT on FHTO2\n')
fh.write('\tsample placed into HAB at 30C, and start ramping to 600 C\n')
fh.write('\tsee log file: FHT02_heating.log\n')
fh.flush()

setSubdirectory('FHT02_heating_30C-600C')
logfh = open('/dls/i11/data/2022/cy28349-9/processing/FHT02_heating_30C_to_600C.log','a')
pos sample 11
pos tlx 0
caput("BL11I-EA-BLOW-02:LOOP1:RR", 0.2) #ramp rate ~12 deg/min
hotairup(600, logfh) # measure from 30 C to 600 C
hotairdown(30, logfh) # measure from 30 C to 600 C
logfh.close()
pos tlx 300


fh.write('Running VT on FHTO3\n')
fh.write('\tsample placed into HAB at 30C, and start ramping to 600 C\n')
fh.write('\tsee log file: FHT03_heating.log\n')
fh.flush()

setSubdirectory('FHT01_heating_30C-600C')
logfh = open('/dls/i11/data/2022/cy28349-9/processing/FHT03_heating_30C_to_600C.log','a')
pos sample 12
pos tlx 0
caput("BL11I-EA-BLOW-02:LOOP1:RR", 0.2) #ramp rate ~12 deg/min
hotairup(600, logfh) # measure from 30 C to 600 C
hotairdown(30, logfh) # measure from 30 C to 600 C
logfh.close()
pos tlx 300




fh.write('Running VT on FHTO4\n')
fh.write('\tsample placed into HAB at 30C, and start ramping to 600 C\n')
fh.write('\tsee log file: FHT04_heating.log\n')
fh.flush()

setSubdirectory('FHT04_heating_30C-600C')
logfh = open('/dls/i11/data/2022/cy28349-9/processing/FHT04_heating_30C_to_600C.log','a')
pos sample 13
pos tlx 0
caput("BL11I-EA-BLOW-02:LOOP1:RR", 0.2) #ramp rate ~12 deg/min
hotairup(600, logfh) # measure from 30 C to 600 C
hotairdown(30, logfh) # measure from 30 C to 600 C
logfh.close()
pos tlx 300

fh.close()
sample.clearSample()
spin.off()     