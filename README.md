# dls-i11-tools

This repository contains some scripts for automating diffraction on the I11 beamline at Diamond Light Source.
I11 is targeted at high-angular resolution and time-resolved diffraction, with additional capability for variable temperature (VT) experiments across a temperature range of 80 - 1000 K (using cryostream and a hot air blower).

I11 has two types of detectors:

- PSD (position-sensitive detectors) for fast scans with good resolution (~ seconds per scan) (referred to as `delta` and `smythen` in GDA scripts).
- MAC (multi-analyzer crystal) for slower scans with high resolution (~ 20 minutes per scan) (referred to as `ttx` in GDA scripts).

I11 uses [GDA](http://www.opengda.org/OpenGDA/Documentation.html) server to control all apparatus.
GDA can be scripted with [Jython](https://www.jython.org/) (a Java implementation of Python 2.7) and uses [beamline-specific extensions](https://alfred.diamond.ac.uk/documentation/manuals/GDA_User_Guide/master/writing_scripts.html) (implemented as keywords, e.g., `pos <scannable> <position>`) to position samples, detectors, etc.


Test