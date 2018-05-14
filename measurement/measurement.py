"""

"""
from enum import Enum, auto

REGISTRY = {}


def register(cls):
    """Decorator to register new measurement methods.

    This function should only be used as a decorator for measurement classes
    which inherit the AbstractMeasurement class.

    Usage:
    @Register
    class MyMeasurement(AbstractMeasurement):
        ....

    Args:
        cls: measurement class to be registered

    Returns:
        class which was given in the args
    """
    if issubclass(cls, AbstractMeasurement):
        REGISTRY[cls.__name__] = cls
    return cls


class AbstractInput(object):
    """Represents a generic Input which the measurement class will return
    """

    def __init__(self, fullname: str, expected_type: type, default):
        """Initialises the Input class

        Args:
            fullname:
            expected_type: expected type of input (float, int, string)
            default:
        """
        self.__type = expected_type
        self.__default = default
        self.__fullname = fullname

    @property
    def type(self) -> type:
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
    TWO = auto()
    FOUR = auto()


class AbstractMeasurement:

    def __init__(self):
        self._number_of_contacts = Contacts.TWO

    @property
    def input(self):
        return {}

    @property
    def number_of_contacts(self) -> Contacts:
        return self._number_of_contacts

    def start(self, **kwargs):
        print(kwargs)
        raise NotImplementedError()

    def run(self):
        pass

