#!/usr/bin/env jython

"""A more advanced example script that uses classes from the `i11.utils` module 
for logging and control.

This script and the `i11.utils` module have not been tested at the beamline and are
unlikely to work (yet!)

"""

__author__ = "Matthew Evans"

import logging
import csv

from i11 import *

beamline = Beamline()
csb2 = Cryostream()
bm = Beam()
sample = Samples()
spin = Spinner()
pos = Table()
 
tlx = Motor()
tlx.name = "tlx"
tlx.position = 300

fh = logging.FileHandler('./test.log', 'a')
LOG.addHandler(fh)

# sample_table = csv.read("samples.csv")
sample_table = {
    "FHT02": 11,
    "FHT01": 12,
    "FHT04": 13,
}

pos(tlx, 300)

sample.start()
#sample.recover()
spin.on()

bm.on()

for sample_id in ["FHT02", "FHT01", "FHT04"]:
    setSubDirectory("%s_heating_30C-600C" % sample_id)
    sample_number = sample_table[sample_id]
    pos(sample, sample_number)
    pos(tlx, 0)
    LOG.debug("Starting PSD")
    variable_temp_psd(30, 600, ramp_rate=0.2)  # measure from 30 C to 600 C
    variable_temp_psd(600, 30, ramp_rate=0.2)  # measure from 600 C to 30 C
    pos(tlx, 300)

sample.clearSample()
spin.off()
bm.off()