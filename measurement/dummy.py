from .measurement import register, AbstractMeasurement, Contacts, SignalInterface
from .measurement import AbstractValue, FloatValue, IntegerValue, DatetimeValue

from random import random
from datetime import datetime
from time import sleep
from typing import Tuple, Dict
from typing.io import TextIO


@register('Dummy Measurement')
class DummyMeasurement(AbstractMeasurement):
    """This is a Dummy Measurement"""
    def __init__(self, signal_interface: SignalInterface, path: str, contacts:Tuple[str, str], n:int=10) -> None:
        super().__init__(signal_interface, path, contacts)
        self._number_of_contacts = Contacts.TWO
        self._n = n

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'n': IntegerValue('Number of Points', default=10)}

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'random1': FloatValue('Random Value 1 [a.u.]'),
                'random2': FloatValue('Random Value 2 [a.u.]'),
                'datetime': DatetimeValue('Timestamp')}

    @staticmethod
    def number_of_contacts() -> Contacts:
        return Contacts.TWO

    @property
    def recommended_plots(self) -> Dict[str, Tuple[str, str]]:
        return {'Some Time-dep': ('datetime', 'random1'),
                'Random Correlation': ('random1', 'random2')}

    def _measure(self, file_handle) -> None:
        self.__print_header(file_handle)

        for i in range(self._n):
            print('{} {} {}'.format(datetime.now().isoformat(), random(), random()), file=file_handle)
            file_handle.flush()
            self._signal_interface.emit_data({'datetime': datetime.now(),
                                              'random1': random(),
                                              'random2': random()})
            sleep(1)
            if self._should_stop.is_set():
                self._signal_interface.emit_aborted()
                break

        self._signal_interface.emit_finished(self._recommended_plot_file_paths)

    def __print_header(self, fil: TextIO) -> None:
        print('#WAZAUP?', file=fil)
        print('datetime random1 random3', file=fil)
