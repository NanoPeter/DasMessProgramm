from .measurement import register, AbstractMeasurement, Contacts
from .measurement import StringValue, FloatValue, IntegerValue, DatetimeValue, AbstractValue, SignalInterface

import numpy as np
from datetime import datetime
from threading import Event
import time
from typing import Dict, Tuple
from typing.io import TextIO

from visa import ResourceManager
#TODO: handle automagic Sourcemeter choice and write this info into the measurement file
from scientificdevices.keithley.sourcemeter2400 import Sourcemeter2400


@register('SourceMeter two probe voltage sweep')
class SMU2Probe(AbstractMeasurement):
    """Voltage driven 2-probe current measurement on a sourcemeter."""

    GPIB_RESOURCE = "GPIB::10::INSTR"

    def __init__(self, signal_interface: SignalInterface) -> None:
        super().__init__(signal_interface)
        self._number_of_contacts = Contacts.TWO
        self._path = str()
        self._contacts = tuple()  # type: Tuple[str, str]
        self._resource_man = None  # type: visa.ResourceManager
        self._device = None  # type: visa.Resource
        self._file_prefix = str()
        self._max_voltage = float()
        self._current_limit = float()
        self._number_of_points = int()
        self._nplc = int()
        self._comment = str()
        self._should_run = Event()
        self._should_run.clear()

    @property
    def inputs(self) -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'n': IntegerValue('Number of Points', default=100),
                'nplc': IntegerValue('NPLC', default=1),
                'comment': StringValue('Comment', default='')}

    @property
    def outputs(self) -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Voltage'),
                'i': FloatValue('Current'),
                'datetime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self) -> Dict[str, Tuple[str, str]]:
        return {'Voltage Sweep': ('v', 'i')}

    def initialize(self, path: str, contacts: Tuple[str, str],
                   v: float = 0.0, i: float = 1e-6, n: int = 100,
                   nplc: int = 3, comment: str = '') -> None:
        """Should be called BEFORE 'call()' is executed.

        :param path: Directory into which all the measurements will be saved
        :param contacts: Contact pair as tuple
        :param v: Maximum voltage
        :param i: Current limit
        :param n: Number of data points to acquire
        :param nplc: Number of cycles over which to average
        :param comment: this comment will be written into the data file
        """
        self._path = self._get_next_file(path)  # TODO: Generate a file path from directory path at runtime.
        self._contacts = contacts
        self._max_voltage, self._current_limit = v, i
        self._number_of_points = n
        self._comment = comment
        self._nplc = nplc
        self._resource_man = ResourceManager("@py")
        resource = self._resource_man.open_resource(self.GPIB_RESOURCE)
        self._device = Sourcemeter2400(resource)
        self._device.voltage_driven(0, i, nplc)
        self._should_run.set()

        self._file_prefix = self._generate_file_name_prefix()

    def __call__(self) -> None:
        """Custom measurement code lives here.

        This method implements the '()' operator.
        """
        self._signal_interface.emit_started()  # Tell the UI that measurement has begun

        with open(self._path, "w") as outfile:
            print("DEBUG: Writing to file", self._path)
            self.__write_header(outfile)

            self.__initialize_device()
            time.sleep(0.5)

            for voltage in np.linspace(0, self._max_voltage, self._number_of_points):
                if not self._should_run.is_set():
                    print("DEBUG: Aborting measurement.")
                    break

                self._device.set_voltage(voltage)
                voltage, current = self.__measure_data_point()
                outfile.write("{} {}".format(voltage, current))

                # Send data point to UI for plotting:
                self._signal_interface.emit_data({'v': voltage, 'i': current, 'datetime': datetime.now()})

            self.__deinitialize_device()

        self._signal_interface.emit_finished(None)  # Tell the UI that measurement is done
        # We are not passing any additional data back to the UI, hence the 'None' argument.

    def abort(self) -> None:
        """Stop the measurement before the next data point."""
        self._should_run.clear()

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
        voltage_str, current_str = self._device.read().split(",")  # type: Tuple[str, str]
        return (float(voltage_str), float(current_str))

