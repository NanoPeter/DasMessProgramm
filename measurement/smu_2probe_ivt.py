from .measurement import register, SignalInterface, AbstractValue, AbstractMeasurement
from .measurement import FloatValue, IntegerValue, StringValue, DatetimeValue, GPIBPathValue

from typing import Dict, Tuple, Union

from visa import ResourceManager
from scientificdevices.keithley.sourcemeter2400 import Sourcemeter2400


@register('SourceMeter two probe current vs. time')
class SMU2ProbeIvt(AbstractMeasurement):

    GPIB_RESOURCE = 'GPIB0::10::INSTR'

    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 v: float = 0.0, i: float = 1e-6,
                 nplc: int = 3, comment: str = '', time_difference: float=0):
        super().__init__(signal_interface, path, contacts)
        self._max_voltage = v
        self._current_limit = i
        self._nplc = nplc
        self._comment = comment
        self._time_difference = time_difference

        resource_man = ResourceManager('@py')
        resource = resource_man.open_resource(self.GPIB_RESOURCE)

        self._device = Sourcemeter2400(resource)
        self._device.voltage_driven(0, i, nplc)

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'nplc': IntegerValue('NPLC', default=1),
                'comment': StringValue('Comment', default=''),
                'gpib': GPIBPathValue('GPIB Address', default='GPIB0::10::INSTR')}

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Voltage'),
                'i': FloatValue('Current'),
                'datetime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self) -> Dict[str, Tuple[str, str]]:
        return {'Current vs. Time': ('datetime', 'i')}

    def _measure(self, file_handle):
        #TODO: has to be filled with life
        pass