from .measurement import register, AbstractMeasurement, Contacts, PlotRecommendation
from .measurement import StringValue, FloatValue, IntegerValue, DatetimeValue, AbstractValue, SignalInterface, GPIBPathValue

from typing import Dict, Tuple, List
from typing.io import TextIO

from visa import ResourceManager
from scientificdevices.stanford_research_systems.sr830m import SR830m

from datetime import datetime
from time import sleep, time
from threading import Event

import numpy as np
from queue import Queue

import gpib

import traceback

from enum import Enum

from ast import literal_eval

class GenericInstrument(object):
    """ This is an abstract class for a generic instrument """
    def __init__(self):
        """ Initialises the generic instrument """
        self.term_chars = '\n'

    def ask(self, query):
        """ ask will write a request and waits for an answer

            Arguments:
            query -- (string) the query which shall be sent

            Result:
            (string) -- answer from device
        """
        self.write(query)
        return self.read()

    def write(self, query):
        """ writes a query to remote device

            Arguments:
            query -- (string) the query which shall be sent
        """
        pass

    def read(self):
        """ reads a message from remote device

            Result:
            (string) -- message from remote device
        """
        pass

    def close(self):
        """ closes connection to remote device """
        pass

class GpibInstrument(GenericInstrument):
    """ Implementation of GenericInstrument to communicate with gpib devices """
    def __init__(self, device):
        """ initializes connection to gpib device

            Arguments:
            connection - (gpib.dev) a gpib object to speak to
        """
        GenericInstrument.__init__(self)
        self.device = device
        self.term_chars = '\n'

    def write(self, query):
        """ writes a query to remote device

            Arguments:
            query -- (string) the query which shall be sent
        """
        gpib.write(self.device, query + self.term_chars)

    def read(self):
        """ reads a message from remote device

            Result:
            (string) -- message from remote device
        """
        return gpib.read(self.device, 512).rstrip()

    def close(self):
        """ closes connection to remote device """
        gpib.close(self.device)

    def clear(self):
        """ clears all communication buffers """
        gpib.clear(self.device)

def get_gpib_timeout(timeout):
    """ returns the correct timeout object to a certain timeoutvalue
        it will find the nearest match, e.g., 120us will be 100us

        Arguments:
        timeout -- (float) number of seconds to wait until timeout
    """
    gpib_timeout_list = [(0, gpib.TNONE), \
                         (10e-6, gpib.T10us), \
                         (30e-6, gpib.T30us), \
                         (100e-6, gpib.T100us), \
                         (300e-6, gpib.T300us), \
                         (1e-3, gpib.T1ms), \
                         (3e-3, gpib.T3ms), \
                         (10e-3, gpib.T10ms), \
                         (30e-3, gpib.T30ms), \
                         (100e-3, gpib.T100ms), \
                         (300e-3, gpib.T300ms), \
                         (1, gpib.T1s), \
                         (3, gpib.T3s), \
                         (10, gpib.T10s), \
                         (30, gpib.T30s), \
                         (100, gpib.T100s), \
                         (300, gpib.T300s), \
                         (1000, gpib.T1000s)]

    for val, res in gpib_timeout_list:
        if timeout <= val:
            return res
    return gpib.T1000s

def get_gpib_device(port: int, timeout=0.5):
    device = gpib.dev(0, port)
    gpib.timeout(device, get_gpib_timeout(timeout))
    return GpibInstrument(device)


@register('SRS830 measure')
class SRS830Measure(AbstractMeasurement):


    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str, str, str],
                 R: float = 9.99e6, comment: str = '', gpib: str='GPIB0::7::INSTR',
                 number_of_measurements: int = 5):
                     
        super().__init__(signal_interface, path, contacts)
        self._comment = comment
        self._device = SR830m(gpib)
        self._pre_resistance = R
        self._number_of_measurements = number_of_measurements 

        sleep(1)

    @staticmethod
    def number_of_contacts():
        return Contacts.FOUR

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'R': FloatValue('Pre Resistance', default=9.99e6),
                'number_of_measurements': IntegerValue('Measurements', default=5),
                'comment': StringValue('Comment', default=''),
                'gpib': GPIBPathValue('GPIB Address', default='GPIB0::7::INSTR'),
                }

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'U': FloatValue('Voltage[V]'),
                'Datetime': FloatValue('Time')}

    @property
    def recommended_plots(self) -> List[PlotRecommendation]:
        return [PlotRecommendation('Voltage Monitoring', x_label='Datetime', y_label='U', show_fit=False)]

    def _measure(self, file_handle):
        self.__write_header(file_handle)
        sleep(0.5)
        
        self.__initialize_device()
        for _ in range(self._number_of_measurements):
            if self._should_stop.is_set():
                break
            try:
                self._acquire_data_point(file_handle)
            except: 
                print('{} failed to acquire datapoint.'.format(datetime.now().isoformat()))
                traceback.print_exc()
                

        self.__deinitialize_device()

        
           
 
    def _acquire_data_point(self, file_handle):
        x, y, r, t = self.__measure_data_point()
        sensitivity = self.__get_auxiliary_data()
        
        file_handle.write('{} {} {} {} {} {}\n'.format(datetime.now().isoformat(), 
                                                             x, y, r, t,sensitivity))
        file_handle.flush()
        
        self._signal_interface.emit_data({'U': x, 'Datetime': time()})
     
    def __initialize_device(self):
        pass
        
    def __deinitialize_device(self) -> None:
        pass

    def __write_header(self, file_handle: TextIO) -> None:
        file_handle.write("# {0}\n".format(datetime.now().isoformat()))
        file_handle.write('# {}\n'.format(self._comment))
        file_handle.write('# {} Hz\n'.format(self._device.freq))
        file_handle.write('# {} V\n'.format(self._device.slvl))        
        file_handle.write('# {} Time constant\n'.format(self._device.oflt))
        file_handle.write("# pre resistance {0} OHM\n".format(self._pre_resistance))
        file_handle.write("Datetime Real Imaginary Amplitude Theta Sensitivity\n")

    def __measure_data_point(self):
        return (self._device.outpX, self._device.outpY, self._device.outpR, self._device.outpT)

    def __get_auxiliary_data(self):
        return self._device.sens
