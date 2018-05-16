from .measurement import register, AbstractMeasurement, Contacts
from .measurement import FloatValue, IntegerValue, DatetimeValue, BooleanValue

import numpy as np
import datetime
from threading import Event
import time

from visa import ResourceManager
from sourcemeter2400 import Sourcemeter2400


@register('SourceMeter two probe voltage sweep')
class SMU2Probe(AbstractMeasurement):
    """Voltage driven 2-probe current measurement on a sourcemeter."""
    
    GPIB_RESOURCE = "GPIB::10::INSTR"
    
    def __init__(self, signal_interface):
        super().__init__(signal_interface)
        self._number_of_contacts = Contacts.TWO
        self._path = str()
        self._contacts = tuple()
        self._resource_man = None
        self._device = None
        self._max_voltage = float()
        self._current_limit = float()
        self._number_of_points = float()
        self._should_run = Event()
        self._should_run.clear()

    @property
    def inputs(self):
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'n': IntegerValue('Number of Points', default=100),
                'nplc': IntegerValue('NPLC', default=1)}

    @property
    def outputs(self):
        return {'v': FloatValue('Voltage'),
                'i': FloatValue('Current'),
                'DateTime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self):
        return {'dummy': ('v', 'i')}

    def initialize(self, path, contacts, v=0.0, i=1e-6, n=100, nplc=3):
        """

        :param path: Location where all the measurements shall be saved
        :param contacts: contact pair as tuple
        :param v: maximum voltage
        :param i: current limit
        :param n: number of data points to acquire
        :param nplc: number of cycles over which to average
        :return:
        """
        self._path = path
        self._contacts = contacts
        self._max_voltage, self._current_limit = v, i
        self._number_of_points = n
        self._resource_man = ResourceManager("@py")
        resource = self._resource_man.open_resource(self.GPIB_RESOURCE)
        self._device = Sourcemeter2400(resource)
        self._device.voltage_driven(0, i, nplc)
        self._should_run.set()

    def abort(self):
        """Stop the measurement before the next data point."""
        self._should_run.clear()
        
    def run(self):
        self._signal_interface.emit_started()

        with open(self._path, "w") as outfile:
            outfile.write("# {0}\n".format(datetime.now().isoformat()))
            outfile.write("# maximum voltage {0} V\n".format(self._max_voltage))
            outfile.write("# current limit {0} A\n".format(self._current_limit))
            outfile.write("Voltage Current\n")

            self._device.arm()  # Initialise GPIB.
            time.sleep(0.5)

            for voltage in np.linspace(0, self._max_voltage, self._number_of_points):
                if not self._should_run.is_set():
                    print("DEBUG: Aborting measurement.")
                    break
                
                self._device.set_voltage(voltage)
                voltage_str, current_str = self._device.read().split(",")  # type: Tuple[str, str]
                voltage, current = float(voltage), float(current)
                outfile.write("{} {}".format(voltage_str, current_str))

                self._signal_interface.emit_data((voltage, current))

                # De-initialise GPIB:
                self._device.set_voltage(0)
                self._device.disarm()
        
        self._signal_interface.emit_finished()

