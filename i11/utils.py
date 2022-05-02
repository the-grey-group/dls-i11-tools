#!/usr/bin/env jython
# -*- coding: utf-8 -*-

"""This module defines some useful classes for developing
scripts for the i11 beamline at Diamond Light Source."""

__all__ = (
    "LOG",
    "Beamline",
    "Beam",
    "Samples",
    "Spinner",
    "Cryostream",
    "Motor",
    "caput",
    "Table",
    "setSubDirectory",
    "variable_temp_psd",
)

import datetime
import logging
import time

TESTING = True


LOG = logging.getLogger("root")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.FileHandler(str(datetime.date.today()) + ".log", mode="a"))
LOG.addHandler(logging.StreamHandler())
for handler in LOG.handlers:
    handler.setFormatter(logging.Formatter("%(asctime)-15s %(levelname)-6s: %(message)s"))

FILE_LOG = logging.getLogger("file")
FILE_LOG.addHandler(logging.FileHandler(str(datetime.date.today()) + ".file.log", mode="a"))
FILE_LOG.setLevel(logging.DEBUG)
FILE_LOG.addHandler(logging.StreamHandler())
for handler in FILE_LOG.handlers:
    handler.setFormatter(logging.Formatter("%(message)s"))


def temperature_reached(start_temperature, end_temperature, current_temperature):
    if start_temperature < end_temperature and current_temperature >= end_temperature:
        return True
    if start_temperature > end_temperature and current_temperature <= end_temperature:
        return True
    return False


class _Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(_Singleton, cls).__new__(
                cls, *args, **kwargs
            )
        return cls._instance

class Beamline(_Singleton):
    def __init__(self):
        self.file_number = 0

    def getFileNumber(self):
        self.file_number += 1
        return self.file_number

class Beam(_Singleton):
    def __init__(self):
        self._on = False

    def on(self):
        self._on = True

    def off(self):
        self._on = False


class Table(_Singleton):

    def __call__(self, motor, position):
        LOG.debug("Moving motor %s from %s to %s" % (motor, motor.position, position))
        motor.position = position


class Motor(_Singleton):

    _name = None
    _position = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
    
    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos

    def __str__(self):
        return self.name


class Samples(Motor):

    _position = 0
    sample_in_position = None
    name = "sample"

    def start(self):
        if self.sample_in_position is None:
            self.sample_in_position = self.position

    def recover(self):
        if self.sample_in_position is not None:
            self.position = self.sample_in_position
            self.sample_in_position = None

    def clearSample(self):
        self.recover()

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        LOG.debug("Moving sample %s into position", value)
        time.sleep(1)
        self._position = value
        self.sample_in_position = self._position



class Spinner(_Singleton):
    def __init__(self):
        self.spinning = False

    def on(self):
        self.spinning = True

    def off(self):
        self.spinning = False


class Cryostream(_Singleton):
    _current_temperature = 21.0
    _set_point = 21.0
    _ramp_rate = 0.0
    _ramp_start_time = None

    @property
    def currentTemperature(self):
        return self.current_temperature

    @property
    def current_temperature(self):
        if self._ramp_start_time is None:
            return self._current_temperature

        if abs(self._current_temperature - self._set_point) < 1:
            self._current_temperature = self.set_point
            self._ramp_start_time = None
        else:
            self._current_temperature += self.ramp_rate * (time.time() - self._ramp_start_time)
        LOG.debug("🌡  Cryostream temperature is now %f °C" % self._current_temperature)

        return self._current_temperature

    @property
    def set_point(self):
        return self._set_point

    @set_point.setter
    def set_point(self, value):
        LOG.debug("🌡  Setting Cryostream set point to %s °C", value)
        caput("BL11I-EA-BLOW-02:LOOP1:SP", self._set_point)
        self._set_point = value

    @property
    def ramp_rate(self):
        return self._ramp_rate

    @ramp_rate.setter
    def ramp_rate(self, value):
        """Ramp rate in degrees per second."""
        LOG.debug("🌡  Setting Cryostream ramp rate to %s K/s", value)
        caput("BL11I-EA-BLOW-02:LOOP1:RR", self._ramp_rate)
        self._ramp_rate = value

    def start(self):
        self._ramp_start_time = time.time()
        if self.ramp_rate != 0:
            LOG.debug(
                "🌡  Initialising temperature ramp from %s °C to %s °C with ramp rate %s K/s. ETA: %s minutes.",
                self.current_temperature,
                self.set_point,
                self.ramp_rate,
                abs(self.set_point - self.current_temperature) / (self.ramp_rate * 60)
            )
            caput("BL11I-CG-CSTRM-02:RAMP.PROC")
        else:
            raise RuntimeError("No ramp rate set")


def setSubDirectory(path):
    import os
    if not os.path.isdir(path):
        os.makedirs(path)
    os.chdir(path)


def caput(parameter, value=None):
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
        "BL11I-CG-CSTRM-02:RRATE",  # cryostream ramp rate
        "BL11I-CG-CSTRM-02:RTEMP",  # cryostream target temperature
        "BL11I-CG-CSTRM-02:RAMP.PROC"  # start cryostream ramp
    )

    if parameter not in known_parameters:
        LOG.warn(
            "🖥️ Parameter %s not in known parameters for `caput`.", parameter
        )

    #if parameter == "BL11I-EA-BLOW-02:LOOP1:SP":
    #    csb2 = Cryostream()
    #    csb2.set_point = value
    #elif parameter == "BL11I-EA-BLOW-02:LOOP1:RR":
    #    csb2 = Cryostream()
    #    csb2.ramp_rate = value

    LOG.debug("🖥️  Executed caput with %s and value %s", parameter, value)



def variable_temp_psd(start_temperature, target_temperature, ramp_rate=0.2, max_scans=1000):
    """Perform multiple PSD scans during a temperature ramp from
    start to target temperature.

    Arguments:
        start_temperature (int): The starting temperature in degrees celsius.
        target_temperature (int): The target temperature in degrees celsius.
        ramp_rate (float): The ramp rate in degrees celsius per second.

    """

    csb2 = Cryostream()

    LOG.info(
        "🌡  Performing variable temperature PSD in range %s °C -> %s °C",
        start_temperature,
        target_temperature
    )
    csb2.set_point = start_temperature
    initial_temperature = csb2.current_temperature
    if initial_temperature > start_temperature and ramp_rate > 0:
        ramp_rate *= -1
    csb2.ramp_rate = ramp_rate
    csb2.start()

    while not temperature_reached(
        initial_temperature,
        start_temperature,
        csb2.current_temperature
    ):
        time.sleep(1)

    LOG.info(
        "🌡  Cryostream reached %s °C. Beginning ramp up to %s °C",
        csb2.current_temperature,
        target_temperature)

    csb2.set_point = target_temperature
    if target_temperature < start_temperature and ramp_rate > 0:
        ramp_rate *= -1
    csb2.ramp_rate = ramp_rate
    csb2.start()

    counter = 0
    while not temperature_reached(
        start_temperature,
        target_temperature,
        csb2.current_temperature
    ):
        counter += 1
        psd_scan(2, 2.25, 0.25, 6)

        if counter > max_scans:
            break

    else:
        LOG.info("🌡  Cryostream reached %s °C. Performing 5 final scans.", csb2.current_temperature)
        # 5 final scans after reaching temperature
        for _ in range(5):
            psd_scan(2, 2.25, 0.25, 6)


def psd_scan(start, stop, step, exposure_time, detector_name="smythen", _sleep=0):
    """Perform a PSD scan over the `delta` scannable with the `smythen` detector."""
    try:
        eval("scan delta %s %s %s %s %s"
             % (start, stop, step, detector_name, exposure_time)
        )
    except SyntaxError as exc:
        time.sleep(_sleep)
        if TESTING:
            pass
        else:
            LOG.error("Syntax error in scan command: %s", exc)

    beamline = Beamline()
    samples = Samples()
    csb2 = Cryostream()

    FILE_LOG.info(
        "%s %s %s",
        str(long(beamline.getFileNumber())),
        samples.sample_in_position,
        csb2.current_temperature
    )