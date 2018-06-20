from .measurement import register, AbstractMeasurement, Contacts, PlotRecommendation
from .measurement import StringValue, FloatValue, IntegerValue, DatetimeValue, AbstractValue, SignalInterface, GPIBPathValue

import numpy as np
from datetime import datetime
from threading import Event
import time
from typing import Dict, Tuple, List
from typing.io import TextIO

from visa import ResourceManager
import visa
#TODO: handle automagic Sourcemeter choice and write this info into the measurement file
from scientificdevices.keithley.sourcemeter2400 import Sourcemeter2400
from scientificdevices.keithley.sourcemeter2602A import Sourcemeter2602A
from scientificdevices.keithley.sourcemeter2636A import Sourcemeter2636A


@register('SourceMeter two probe voltage sweep')
class SMU2Probe(AbstractMeasurement):
    """Voltage driven 2-probe current measurement on a sourcemeter."""

    VISA_LIBRARY = "@py"
    QUERY_DELAY = 0.0

    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 v: float = 0.0, i: float = 1e-6, n: int = 100,
                 nplc: int = 1, comment: str = '', gpib:str='') -> None:
        super().__init__(signal_interface, path, contacts)
        self._max_voltage = v
        self._current_limit = i
        self._number_of_points = n
        self._nplc = nplc
        self._comment = comment

        resource_man = ResourceManager(self.VISA_LIBRARY)
        resource = resource_man.open_resource(gpib, query_delay=self.QUERY_DELAY)

        self._device = SMU2Probe._get_sourcemeter(resource)
        self._device.voltage_driven(0, i, nplc)


    @staticmethod
    def _get_sourcemeter(resource):
        identification = resource.query('*IDN?')
        if '2400' in identification:
            return Sourcemeter2400(resource)
        elif '2602' in identification:
            return Sourcemeter2602A(resource)
        elif '2636' in identification:
            return Sourcemeter2636A(resource)
        else:
            raise ValueError('Sourcemeter "{}" not known.'.format(identification))


    @staticmethod
    def number_of_contacts():
        return Contacts.TWO

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'n': IntegerValue('Number of Points', default=100),
                'nplc': IntegerValue('NPLC', default=1),
                'comment': StringValue('Comment', default=''),
                'gpib': GPIBPathValue('GPIB Address', default='GPIB0::10::INSTR')}

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Voltage'),
                'i': FloatValue('Current'),
                'datetime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self) -> List[PlotRecommendation]:
        return [PlotRecommendation('Voltage Sweep', x_label='v', y_label='i', show_fit=True)]

    def _measure(self, file_handle) -> None:
        """Custom measurement code lives here.
        """
        self.__write_header(file_handle)
        self.__initialize_device()
        time.sleep(0.5)
        voltages, currents = [], []

        for voltage in np.linspace(0, self._max_voltage, self._number_of_points):
            if self._should_stop.is_set():
                print("DEBUG: Aborting measurement.")
                self._signal_interface.emit_aborted()
                break

            self._device.set_voltage(voltage)
            voltage, current = self.__measure_data_point()
            voltages.append(voltage)
            currents.append(current)
            file_handle.write("{} {}\n".format(voltage, current))
            file_handle.flush()
            # Send data point to UI for plotting:
            self._signal_interface.emit_data({'v': voltage, 'i': current, 'datetime': datetime.now()})

        self.__deinitialize_device()
        
        resistance, _ = np.polyfit(currents, voltages, 1)
        self._write_overview(Resistance=resistance, Datetime=datetime.now().isoformat())

    def __initialize_device(self) -> None:
        """Make device ready for measurement."""
        self._device.arm()

    def __deinitialize_device(self) -> None:
        """Reset device to a safe state."""
        self._device.set_voltage(0)
        self._device.disarm()

    def __write_header(self, file_handle: TextIO) -> None:
        """Write a file header for present settings.

        Arguments:
            file_handle: The open file to write to
        """
        file_handle.write("# {0}\n".format(datetime.now().isoformat()))
        file_handle.write('# {}\n'.format(self._comment))
        file_handle.write("# maximum voltage {0} V\n".format(self._max_voltage))
        file_handle.write("# current limit {0} A\n".format(self._current_limit))
        file_handle.write('# nplc {}\n'.format(self._nplc))
        file_handle.write("Voltage Current\n")

    def __measure_data_point(self) -> Tuple[float, float]:
        """Return one data point: (voltage, current).

        Device must be initialised and armed.
        """
        return self._device.read()


@register("SIMULATED SourceMeter two probe voltage sweep")
class SMU2ProbeSimulation(SMU2Probe):
    """PyVisa-sim compatible adaptation of SMU2Probe for testing."""

    VISA_LIBRARY = "measurement/test_devices.yaml@sim"
    QUERY_DELAY = 0.1

    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 v: float = 0.0, i: float = 1e-6, n: int = 100,
                 nplc: int = 1, comment: str = '') -> None:
        super().__init__(signal_interface, path, contacts,
                         v, i, n, nplc, comment)

        # Set some things that are needed to get pyvisa-sim running:
        self._device._dev.write_termination = "\n"
        self._device._dev.read_termination = "\n"
        self._device._dev.set_visa_attribute(
            visa.constants.VI_ATTR_TERMCHAR_EN,
            visa.constants.VI_TRUE
        )
