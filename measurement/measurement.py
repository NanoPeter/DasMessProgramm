"""

"""
from enum import Enum
from threading import Thread
from datetime import datetime

from threading import Event
from typing import Dict, List, Tuple, Union

from abc import ABC, abstractmethod

from dateutil import parser

from os import listdir
from os.path import join as join_path

import numpy as np

from typing import List
from overview import Overview

REGISTRY = {}


def register(name):
    """Decorator to register new measurement methods and give them global names.

    This function should only be used as a decorator for measurement classes
    which inherit the AbstractMeasurement class.

    :usage:
    @register('My Measurement')
    class MyMeasurement(AbstractMeasurement):
        ....

    :param name: name of the measurement class
    :return: another decorator to register the class
    """
    def register_wrapper(cls):
        """
        :param cls: measurement class to be registered
        :return: the class which was given by the input
        """
        if issubclass(cls, AbstractMeasurement):
            REGISTRY[name] = cls
            cls.__str__ = lambda self: name
        return cls
    return register_wrapper


class AbstractValue(object):
    """Represents a generic input which the measurement class will return
    """

    def __init__(self, fullname: str, default: Union[int, float, bool, str, datetime]) -> None:
        """
        :param fullname: name which should be displayed
        :param default: default value
        """
        self.__default = default
        self.__fullname = fullname

    @property
    def default(self) -> Union[int, float, bool, str, datetime]:
        return self.__default

    @property
    def fullname(self) -> str:
        return self.__fullname

    def convert_from_string(self, value: str) -> Union[int, float, bool, str, datetime]:
        NotImplementedError()


class IntegerValue(AbstractValue):
    def __init__(self, fullname: str, default: int = 0) -> None:
        super().__init__(fullname, default)

    def convert_from_string(self, value: str) -> int:
        return int(value)


class FloatValue(AbstractValue):
    def __init__(self, fullname: str, default: float = 0.0) -> None:
        super().__init__(fullname, default)

    def convert_from_string(self, value: str) -> float:
        return float(value)


class BooleanValue(AbstractValue):
    def __init__(self, fullname: str, default: bool = False) -> None:
        super().__init__(fullname, default)

    def convert_from_string(self, value: str) -> bool:
        return bool(value)


class StringValue(AbstractValue):
    def __init__(self, fullname: str, default: str = '') -> None:
        super().__init__(fullname, default)

    def convert_from_string(self, value: str) -> str:
        return str(value)


class DatetimeValue(AbstractValue):
    def __init__(self, fullname: str) -> None:
        super().__init__(fullname, datetime.now())

    def convert_from_string(self, value) -> datetime:
        return parser.parse(value)


class Contacts(Enum):
    """Gives 
    """
    NONE = 0
    TWO = 2
    THREE = 3
    FOUR = 4


class SignalInterface:
    """An typical
    """
    def emit_finished(self, data: Dict[str, Union[int, float, bool, str, datetime]]) -> None:
        NotImplementedError()

    def emit_data(self, data: Dict[str, Union[int, float, bool, str, datetime]]) -> None:
        NotImplementedError()

    def emit_started(self) -> None:
        NotImplementedError()

    def emit_aborted(self) -> None:
        NotImplementedError()

    def emit_status_message(self, message: str) -> None:
        NotImplementedError()


class PlotRecommendation:
    def __init__(self, title: str, x_label: str, y_label: str, show_fit: bool=False):
        self._title = title
        self._xlabel = x_label
        self._ylabel = y_label
        self._show_fit = show_fit

    @property
    def show_fit(self):
        return self._show_fit

    @property
    def title(self):
        return self._title

    @property
    def x_label(self):
        return self._xlabel

    @property
    def y_label(self):
        return self._ylabel

    def fit(self, x_data: List[float], y_data: List[float]):
        """
        calculates a linear fit and returns the fit parameters and the fit data to plot
        :param x_data: list of x data
        :param y_data:  list of y data
        :return: A Dictionary with the fitted Data and tuple with xs and ys of the fit
        """

        m, b = np.polyfit(x_data, y_data, 1)

        x = np.array([np.min(x_data), np.max(x_data)])
        y = x * m + b

        return {'m': m, 'b': b}, np.array([x, y]).T



class AbstractMeasurement(ABC):
    """

    """
    def __init__(self,
                 signal_interface: SignalInterface,
                 path: str,
                 contacts: Union[Tuple, Tuple[str, str], Tuple[str, str, str, str]],
                 **kwargs) -> None:
        """
        :param signal_interface: An object which is derived from SignalInterface
        """
        super().__init__()
        self._signal_interface = signal_interface
        self._path = path
        self._contacts = contacts
        self._should_stop = Event()
        self._recommended_plot_file_paths = {}

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {}

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {}

    @property
    def recommended_plots(self) -> List[PlotRecommendation]:
        return []

    @staticmethod
    def number_of_contacts() -> Contacts:
        return Contacts.TWO

    def _get_next_file(self, file_prefix: str, file_suffix: str = '.dat') -> str:
        """
        Looks for existing files and generates a suitable successor
        :param file_prefix: the beginning of the file name
        :param file_suffix: the end of the file name, normally '.dat
        :return: full path of new file
        """
        file_list = listdir(self._path)

        # filename has the form  {prefix}DDD{suffix}
        filtered_file_list = [file_name
                              for file_name in file_list
                              if file_name.startswith(file_prefix) and file_name.endswith(file_suffix)
                              and len(file_name[len(file_prefix):-len(file_suffix)]) == 3
                              and file_name[len(file_prefix):-len(file_suffix)].isdigit()
                              ]

        if len(filtered_file_list) == 0:
            new_file_name = '{prefix}001{suffix}'.format(prefix=file_prefix, suffix=file_suffix)
            return join_path(self._path, new_file_name)

        last_file_name = sorted(filtered_file_list)[-1]

        last_number = int(last_file_name[len(file_prefix):-len(file_suffix)])

        new_file_name = '{prefix}{number:03d}{suffix}'.format(prefix=file_prefix,
                                                              number=last_number + 1,
                                                              suffix=file_suffix)

        print(self._path, new_file_name)

        return join_path(self._path, new_file_name)

    def _generate_file_name_prefix(self) -> str:
        return 'contacts_{}_'.format('--'.join(self._contacts))

    def _generate_plot_file_name_prefix(self, pair) -> str:
        return 'contacts_{}_plot-{}-{}_'.format('--'.join(self._contacts), pair[0], pair[1])

    def _generate_all_file_names(self) -> None:
        file_prefix = self._generate_file_name_prefix()
        self._file_path = self._get_next_file(file_prefix)

        self._recommended_plot_file_paths = {}
        for recommendation in self.recommended_plots:
            pair = (recommendation.x_label, recommendation.y_label)
            plot_file_name_prefix = self._generate_plot_file_name_prefix(pair)
            self._recommended_plot_file_paths[pair] = self._get_next_file(plot_file_name_prefix, file_suffix='.pdf')


    def abort(self) -> None:
        self._should_stop.set()

    def __call__(self) -> None:
        self._signal_interface.emit_started()
        self._should_stop.clear()
        self._generate_all_file_names()
        print('writing to {}'.format(self._file_path))
        with open(self._file_path, 'w') as file_handle:
            self._measure(file_handle)
        self._signal_interface.emit_finished(self._recommended_plot_file_paths)

    @abstractmethod
    def _measure(self, file_handle) -> None:
        pass

    def _write_overview(self, comment_lines: List[str] = [],  **data) -> None:
        print("DEBUG: write_overview called")
        overview_file = Overview(self._path, self.__class__.__name__, list(data.keys()), comment_lines)
        overview_file.add_measurement(**data)

