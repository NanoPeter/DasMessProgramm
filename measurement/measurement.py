"""

"""
from enum import Enum
from threading import Thread
from datetime import datetime

from threading import Event

from dateutil import parser

from os import listdir
from os.path import join as joinpath

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


class AbstractMeasurement(Thread):
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

    def initialize(self, path, contacts, **kwargs):
        NotImplementedError()

    def _get_next_file(self, file_name):
        return

    def abort(self):
        self._should_stop.set()
        self.join()

    def run(self):
        pass

