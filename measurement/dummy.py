from .measurement import register, AbstractMeasurement, Contacts, SignalInterface
from .measurement import AbstractValue, FloatValue, IntegerValue, DatetimeValue

from random import random
from datetime import datetime
from time import sleep
from typing import Tuple, Dict
from typing.io import TextIO


@register('Dummy Measurement')
class DummyMeasurement(AbstractMeasurement):
    def __init__(self, signal_interface: SignalInterface) -> None:
        super().__init__(signal_interface)
        self._number_of_contacts = Contacts.TWO

        self._n = 10
        self._contacts = ()  # type: Union[Tuple[str, str], Tuple[str, str, str, str]]

        self._recommended_plot_file_paths = {}  # type: Dict[Tuple[str, str], str]
        self._file_path = str()

    @property
    def inputs(self) -> Tuple[str, AbstractValue]:
        return {'n': IntegerValue('Number of Points', default=10)}

    @property
    def outputs(self) -> Tuple[str, AbstractValue]:
        return {'random1': FloatValue('Random Value 1 [a.u.]'),
                'random2': FloatValue('Random Value 2 [a.u.]'),
                'datetime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self) -> Dict[str, Tuple[str, str]]:
        return {'Some Time-dep': ('datetime', 'random1'),
                'Random Correlation': ('random1', 'random2')}

    def initialize(self, path, contacts, n=10) -> None:
        """
        :param path:
        :param contacts:
        :param n:
        :return:
        """
        self._n = n
        self._path = path
        self._contacts = contacts

        #print(self._path)

        file_prefix = self._generate_file_name_prefix()
        self._file_path = self._get_next_file(file_prefix)

        self._recommended_plot_file_paths = {}

        for title, pair in self.recommended_plots.items():
            plot_file_name_prefix = self._generate_plot_file_name_prefix(pair)
            self._recommended_plot_file_paths[pair] = self._get_next_file(plot_file_name_prefix, file_suffix='.pdf')

    def __call__(self) -> None:
        self._signal_interface.emit_started()
        self._should_stop.clear()

        print('writing to {}'.format(self._file_path))
        with open(self._file_path, 'w') as fil:

            self.__print_header(fil)

            for i in range(self._n):
                print('{} {} {}'.format(datetime.now().isoformat(), random(), random()), file=fil)
                fil.flush()
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
