"""

"""
from enum import Enum
from threading import Thread

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


class AbstractInput(object):
    """Represents a generic input which the measurement class will return
    """

    def __init__(self, fullname: str, expected_type: type, default):
        """
        :param fullname: name which should be displayed
        :param expected_type:
        :param default: default value
        """
        self.__type = expected_type
        self.__default = default
        self.__fullname = fullname

    @property
    def type(self) -> type:
        """
        :return:
        """
        return self.__type

    @property
    def default(self):
        return self.__default

    @property
    def fullname(self):
        return self.__fullname


class IntegerInput(AbstractInput):
    def __init__(self, fullname: str, default: int = 0):
        super().__init__(fullname, int, default)


class FloatInput(AbstractInput):
    def __init__(self, fullname: str, default: float = 0.0):
        super().__init__(fullname, float, default)


class StringInput(AbstractInput):
    def __init__(self, fullname: str, default: str = ''):
        super().__init__(fullname, str, default)


class Contacts(Enum):
    """Gives
    """
    TWO = 0
    FOUR = 1


class AbstractMeasurement(Thread):
    """

    """
    def __init__(self):
        self._number_of_contacts = Contacts.TWO

    @property
    def inputs(self):
        return {}

    @property
    def number_of_contacts(self) -> Contacts:
        return self._number_of_contacts

    def initialize(self, **kwargs):
        NotImplementedError()

    def run(self):
        pass

