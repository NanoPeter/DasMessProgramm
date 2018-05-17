"""

"""
from enum import Enum
from threading import Thread
from datetime import datetime

from threading import Event

from abc import ABC, abstractmethod

from dateutil import parser

from os import listdir
from os.path import join as join_path

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
        return cls
    return register_wrapper


class AbstractValue(object):
    """Represents a generic input which the measurement class will return
    """

    def __init__(self, fullname: str, default):
        """
        :param fullname: name which should be displayed
        :param default: default value
        """
        self.__default = default
        self.__fullname = fullname

    @property
    def default(self):
        return self.__default

    @property
    def fullname(self):
        return self.__fullname

    def convert_from_string(self, value):
        NotImplementedError()


class IntegerValue(AbstractValue):
    def __init__(self, fullname: str, default: int = 0):
        super().__init__(fullname, default)

    def convert_from_string(self, value):
        return int(value)


class FloatValue(AbstractValue):
    def __init__(self, fullname: str, default: float = 0.0):
        super().__init__(fullname, default)

    def convert_from_string(self, value):
        return float(value)


class BooleanValue(AbstractValue):
    def __init__(self, fullname: str, default: bool = False):
        super().__init__(fullname, default)

    def convert_from_string(self, value):
        return bool(value)


class StringValue(AbstractValue):
    def __init__(self, fullname: str, default: str = ''):
        super().__init__(fullname, default)

    def convert_from_string(self, value):
        return str(value)


class DatetimeValue(AbstractValue):
    def __init__(self, fullname: str):
        super().__init__(fullname, datetime.now())

    def convert_from_string(self, value):
        return parser.parse(value)


class Contacts(Enum):
    """Gives
    """
    TWO = 2
    FOUR = 4


class SignalInterface:
    """An typical
    """
    def emit_finished(self, data):
        NotImplementedError()

    def emit_data(self, data):
        NotImplementedError()

    def emit_started(self):
        NotImplemented()

    def emit_aborted(self):
        NotImplemented()


class AbstractMeasurement(ABC):
    """

    """
    def __init__(self, signal_interface: SignalInterface):
        """
        :param signal_interface: An object which is derived from SignalInterface
        """
        super().__init__()
        self._number_of_contacts = Contacts.TWO
        self._signal_interface = signal_interface

        self._path = '/'
        self._contacts = ()

        self._should_stop = Event()

    @property
    def inputs(self):
        return {}

    @property
    def outputs(self):
        return {}

    @property
    def recommended_plots(self):
        return []

    @property
    def number_of_contacts(self) -> Contacts:
        return self._number_of_contacts

    @abstractmethod
    def initialize(self, path, contacts, **kwargs):
        pass

    def _get_next_file(self, file_prefix: str, file_suffix: str='.dat'):
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

    def abort(self):
        self._should_stop.set()

    @abstractmethod
    def __call__(self):
        pass

