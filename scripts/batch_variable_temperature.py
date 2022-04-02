"""This script contains routines for running PSD and MAC scans at
the I11 beamline at Diamond Light Source.

"""

import csv
import datetime
import logging

TESTING = True

LOG = logging.getLogger()


if TESTING:

    class Beamline:
        def __init__(self):
            self.file_number = 0

        def getFileNumber(self):
            self.file_number += 1
            return self.file_number

    class Beam:
        def __init__(self):
            self._on = False

        def on(self):
            self._on = True

        def off(self):
            self._on = False

    class Samples:
        def __init__(self):
            self.carousel_position = 0
            self.sample_in_position = None

        def start(self):
            if not self.sample_in_position:
                self.sample_in_position = self.carousel_position

        def recover(self):
            if self.sample_in_position:
                self.carousel_position = self.sample_in_position
                self.sample_in_position = None

        def clearSample(self):
            self.recover()

    class Spinner:
        def __init__(self):
            self.spinning = False

        def on(self):
            self.spinning = True

        def off(self):
            self.spinning = False

    class Cryostream:
        def __init__(self):
            self.current_temperature = 300.0
            self.set_point = 300.0
            self.ramp_rate = 0.0

        @property
        def currentTemperature(self):
            self.current_temperature += self.ramp_rate
            if (
                self.set_point < self.current_temperature and self.ramp_rate > 0
                or self.set_point > self.current_temperature and self.ramp_rate < 0
            ):
                self.current_temperature = self.set_point
            else:
                self.current_temperature += self.ramp_rate 

            return self.current_temperature

    beamline = Beamline()
    csb2 = Cryostream()
    bm = Beam()
    sample = Samples()
    spin = Spinner()
    
    def setSubDirectory(path):
        pass
    
    def caput(parameter, value):
        """Controls an instrument over EPICS via Channel Access (CA),
        hence `caput`.
        
        Parameters:
            parameter: A string indicating the parameter to control,
                e.g., 'BL11I-EA-BLOW-02:LOOP1:SP' indicates the temperature
                set point (SP) of the 2nd hot air blower at beamline I11, 
                on loop 1.
            value: The value to set the parameter to.
    
        """

        known_parameters = (
            "BL11I-EA-BLOW-02:LOOP1:SP",  # air blower set point
            "BL11I-EA-BLOW-02:LOOP1:RR",  # air blower ramp rate
            "BL11I-CG-CSTRM-02:RRATE") # cryostream ramp rate 
            "BL11I-CG-CSTRM-02:RTEMP" # cryostream target temperature
            "BL11I-CG-CSTRM-02:RAMP.PROC", 1) # start cryostream ramp
        )

        if parameter not in known_parameters:
            logging.warn(
                "Parameter %s not in known parameters for `caput`.", parameter
            )

        if parameter == "BL11I-EA-BLOW-02:LOOP1:SP":
            csb2.set_point = value
        elif parameter == "BL11I-EA-BLOW-02:LOOP1:RR":
            csb2.ramp_rate = value

######################################################################

#Hot air blower ramp up and ramp down functions

def hotairup(Ttemp, logfh):
    """Ramp up hot air blower to target temperature
    and take periodically take PSD scans.
    
    Parameters:
        Ttemp: The target temperature.
        logfh: A file handle for log writing.
        
    """
    caput("BL11I-EA-BLOW-02:LOOP1:SP",Ttemp)
    for _ in range(1000):
        scan delta 2 2.25 0.25 smythen 6 # type: ignore
        temp = csb2.currentTemperature
        line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
        logfh.write(line)
        logfh.flush()
        if csb2.currentTemperature > Ttemp - 0.5:
            for _ in range(5):
                print "last 5 scans"
                scan delta 2 2.25 0.25 smythen 6 # type: ignore
                temp = csb2.currentTemperature
                line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
                logfh.write(line)
                logfh.flush()
            break


def hotairdown(Ttemp, logfh):
    """Ramp down hot air blower to target temperature
    and take periodically take PSD scans.
    
    Parameters:
        Ttemp: The target temperature.
        logfh: A file handle for log writing.
        
    """
    caput("BL11I-EA-BLOW-02:LOOP1:SP",Ttemp)
    for _ in range(1000):
        scan delta 2 2.25 0.25 smythen 6 # type: ignore
        temp = csb2.currentTemperature
        line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
        logfh.write(line)
        logfh.flush()
        if csb2.currentTemperature < Ttemp + 1 :
            for _ in range(5):
                print "last 5 scans"
                scan delta 2 2.25 0.25 smythen 6 # type: ignore
                temp = csb2.currentTemperature
                line = str(long(beamline.getFileNumber())) + ' ' + str(temp) + '\n'    
                logfh.write(line)
                logfh.flush()
            break


def run_csv_batch(csv_filepath):
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
                pos sample position # type: ignore
                pos spos samplepos # type: ignore
                scan delta 2 2.25 0.25 smythen time
                fh.write('{} {} {} {} seconds PSD scan at room temperature, spos = {} mm, {} \n'.format(long(beamline.getFileNumber()), 
                                                    sample_id, 
                                                    position, 
                                                    2*time,
                                                    samplepos,
                                                    datetime.datetime.now()))
                fh.flush()
                sleep(2)

bm.on()

pos tlx 300 # type: ignore
sample.start()
#sample.recover()
spin.on()
fh = open('/dls/i11/data/2022/cy28349-9/processing/Grey_BAG_31Mar22.log','a')

print('Grey Sample start')


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