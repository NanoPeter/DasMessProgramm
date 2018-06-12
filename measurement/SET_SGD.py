from .measurement import register, AbstractMeasurement, Contacts, PlotRecommendation
from .measurement import StringValue, FloatValue, IntegerValue, DatetimeValue, AbstractValue, SignalInterface

import numpy as np
from datetime import datetime
from threading import Event
import time
from typing import Dict, Tuple, List
from typing.io import TextIO

from visa import ResourceManager
import visa

from scientificdevices.keithley.sourcemeter2602A import SMUChannel
from scientificdevices.keithley.sourcemeter2636A import Sourcemeter2636A
from scientificdevices.lakeshore.model340 import Model340, Sensor

@register('SET voltage sweep')
class SETSGD(AbstractMeasurement):
    """Voltage driven 2-probe current measurement on a sourcemeter."""

    GPIB_RESOURCE = "GPIB::10::INSTR"
    TEMP_ADDR = 12
    VISA_LIBRARY = "@py"
    QUERY_DELAY = 0.0

    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 v: float = 0.0, i: float = 1e-6, n: int = 100,
                 nplc: int = 1, comment: str = '', gate_voltage: float=0.0,
                 sd_current_range: float = 0.0, 
                 gd_current_range: float = 0.0) -> None:
        super().__init__(signal_interface, path, contacts)
        self._max_voltage = v
        self._current_limit = i
        self._number_of_points = n
        self._nplc = nplc
        self._comment = comment
        self._gate_voltage = gate_voltage

        resource_man = ResourceManager(self.VISA_LIBRARY)
        resource = resource_man.open_resource(self.GPIB_RESOURCE, query_delay=self.QUERY_DELAY)
        
        self._device = Sourcemeter2636A(resource, sub_device=SMUChannel.channelA)
        self._device.voltage_driven(0, i, nplc, range=sd_current_range)
        
        self._gate = Sourcemeter2636A(resource, sub_device=SMUChannel.channelB)
        self._gate.voltage_driven(0, i, nplc, range=gd_current_range)
        
        self._temperature_controller = Model340(self.TEMP_ADDR)

    @staticmethod
    def number_of_contacts():
        return Contacts.THREE

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'n': IntegerValue('Number of Points', default=100),
                'nplc': IntegerValue('NPLC', default=1),
                'comment': StringValue('Comment', default=''),
                'gate_voltage': FloatValue('Gate Voltage', default=0.0),
                'sd_current_range': FloatValue('SD min. I-range', default=1e-8),
                'gd_current_range': FloatValue('GD min. I-range', default=1e-8),               
                }

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Voltage'),
                'i': FloatValue('Current'),
                'gate_voltage': FloatValue('Gate Voltage'),
                'gate_current': FloatValue('Gate Current'),
                'datetime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self) -> List[PlotRecommendation]:
        return [PlotRecommendation('Voltage Sweep', x_label='v', y_label='i', show_fit=False),
                PlotRecommendation('Gate Current', x_label='v', y_label='gate_current', show_fit=False)]

    def _measure(self, file_handle) -> None:
        """Custom measurement code lives here.
        """
        self.__write_header(file_handle)
        self.__initialize_device()
        time.sleep(0.5)

        for voltage in np.linspace(0, self._max_voltage, self._number_of_points):
            if self._should_stop.is_set():
                print("DEBUG: Aborting measurement.")
                self._signal_interface.emit_aborted()
                break

            self._device.set_voltage(voltage)
            (voltage, current), (gate_voltage, gate_current) = self.__measure_data_point()
            
            temperature_a, temperature_b, temperature_c = self._get_temperatures()
            
            file_handle.write("{} {} {} {} {} {} {} {}\n".format(datetime.now().isoformat(),
                                                           voltage, current,
                                                           gate_voltage, gate_current,
                                                           temperature_a,
                                                           temperature_b,
                                                           temperature_c))
            file_handle.flush()
            # Send data point to UI for plotting:
            self._signal_interface.emit_data({'v': voltage, 'i': current,
                                              'gate_voltage': gate_voltage, 'gate_current': gate_current,
                                               'datetime': datetime.now()})

        self.__deinitialize_device()

    def __initialize_device(self) -> None:
        """Make device ready for measurement."""
        self._device.arm()
        self._gate.set_voltage(self._gate_voltage)
        self._gate.arm()

    def __deinitialize_device(self) -> None:
        """Reset device to a safe state."""
        self._device.set_voltage(0)
        self._device.disarm()
        self._gate.set_voltage(0)
        self._gate.disarm()

    def __write_header(self, file_handle: TextIO) -> None:
        """Write a file header for present settings.

        Arguments:
            file_handle: The open file to write to
        """
        file_handle.write("# {0}\n".format(datetime.now().isoformat()))
        file_handle.write('# {}\n'.format(self._comment))
        file_handle.write("# maximum voltage {0} V\n".format(self._max_voltage))
        file_handle.write("# current limit {0} A\n".format(self._current_limit))
        file_handle.write("# gate voltage {0} V\n".format(self._gate_voltage))
        file_handle.write('# nplc {}\n'.format(self._nplc))
        file_handle.write("Datetime Voltage Current GateVoltage GateCurrent TemperatureA TemperatureB TemperatureC\n")

    def __measure_data_point(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Return one data point: (voltage, current).

        Device must be initialised and armed.
        """
        data_SD = self._device.read()
        data_GD = self._gate.read()
        return data_SD, data_GD
        
    def _get_temperatures(self):
        t_a = self._temperature_controller.get_temperature(Sensor.A)
        t_b = self._temperature_controller.get_temperature(Sensor.B)
        t_c = self._temperature_controller.get_temperature(Sensor.C) 
        return t_a, t_b, t_c
