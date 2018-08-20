from .measurement import register, AbstractMeasurement, Contacts, PlotRecommendation
from .measurement import StringValue, FloatValue, IntegerValue, DatetimeValue, AbstractValue, SignalInterface, GPIBPathValue

from typing import Dict, Tuple, List
from typing.io import TextIO

from visa import ResourceManager
from scientificdevices.keithley.sourcemeter2400 import Sourcemeter2400
from scientificdevices.keithley.sourcemeter2602A import Sourcemeter2602A
from scientificdevices.keithley.sourcemeter2636A import Sourcemeter2636A

from datetime import datetime
from time import sleep
from threading import Event


@register('SourceMeter two probe current vs. time')
class SMU2ProbeIvt(AbstractMeasurement):


    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 v: float = 0.0, i: float = 1e-6,
                 nplc: int = 3, comment: str = '', time_difference: float=0, gpib: str='GPIB0::10::INSTR'):
        super().__init__(signal_interface, path, contacts)
        self._max_voltage = v
        self._current_limit = i
        self._nplc = nplc
        self._comment = comment
        self._time_difference = time_difference
        self._gpib = gpib

        resource_man = ResourceManager('@py')
        resource = resource_man.open_resource(self._gpib)

        self._device = SMU2ProbeIvt._get_sourcemeter(resource)
        self._device.voltage_driven(0, i, nplc)

    @staticmethod
    def number_of_contacts():
        return Contacts.TWO

    @staticmethod
    def _get_sourcemeter(resource):
        identification = resource.query('*IDN?')
        print('DEBUG', identification)
        if '2400' in identification:
            return Sourcemeter2400(resource)
        elif '2602' in identification:
            return Sourcemeter2602A(resource)
        elif '2636' in identification:
            return Sourcemeter2636A(resource)
        else:
            raise ValueError('Sourcemeter "{}" not known.'.format(identification))

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'nplc': IntegerValue('NPLC', default=1),
                'comment': StringValue('Comment', default=''),
                'gpib': GPIBPathValue('GPIB Address', default='GPIB0::10::INSTR')}

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'g': FloatValue('Conductance'),
                'datetime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self) -> List[PlotRecommendation]:
        return [PlotRecommendation('Conductance Monitoring', x_label='datetime', y_label='g', show_fit=False)]

    def _measure(self, file_handle):
        """Custom measurement code lives here.
        """
        self.__write_header(file_handle)
        self.__initialize_device()
        sleep(0.5)

        self._device.set_voltage(self._max_voltage)

        switched_to_current_driven = False

        while not self._should_stop.is_set():
            voltage, current = self.__measure_data_point()
            if not switched_to_current_driven and current > 0.9 * self._current_limit:
                self._device.disarm()
                self._device.set_voltage(0)
                self._device.current_driven(self._current_limit, 
                                            voltage_limit=self._max_voltage, 
                                            nplc = self._nplc)
                self._device.set_current(self._current_limit)
                self._device.arm()
                switched_to_current_driven = True
                sleep(2)
                
            timestamp = datetime.now()
            file_handle.write("{} {} {}\n".format(timestamp.isoformat(), voltage, current))
            file_handle.flush()
            # Send data point to UI for plotting:
            g = float('nan') if voltage == 0 else current / voltage
            self._signal_interface.emit_data({'g': g, 'datetime': timestamp})

        self.__deinitialize_device(switched_to_current_driven)

                             
    def __initialize_device(self) -> None:
        """Make device ready for measurement."""
        self._device.arm()

    def __deinitialize_device(self, current_driven=False) -> None:
        """Reset device to a safe state."""
        if current_driven:
            self._device.set_current(0)
        else:
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
        file_handle.write("Datetime Voltage Current\n")

    def __measure_data_point(self) -> Tuple[float, float]:
        """Return one data point: (voltage, current).

        Device must be initialised and armed.
        """
        return self._device.read()
