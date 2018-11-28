from .measurement import register, AbstractMeasurement, Contacts, PlotRecommendation
from .measurement import StringValue, FloatValue, IntegerValue, DatetimeValue, AbstractValue, SignalInterface, GPIBPathValue

from typing import Dict, Tuple, List
from typing.io import TextIO

from visa import ResourceManager
from scientificdevices.keithley.sourcemeter2400 import Sourcemeter2400
from scientificdevices.keithley.sourcemeter2602A import Sourcemeter2602A
from scientificdevices.keithley.sourcemeter2636A import Sourcemeter2636A

from scientificdevices.oxford.itc503 import ITC

from datetime import datetime
from time import sleep, time
from threading import Event

import numpy as np
from queue import Queue

import gpib

import traceback

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


@register('SourceMeter two probe Current vs. Temp. (blue)')
class SMU2ProbeIvTBlue(AbstractMeasurement):


    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str, str, str],
                 comment: str = '', gpib: str='GPIB0::12::INSTR',
                 sweep_rate:float = 1.0,
                 temperature_end: float = 2,
                 nplc: int = 3, voltage:float = 0.1, current_limit: float=1e-6):
                     
        super().__init__(signal_interface, path, contacts)
        self._comment = comment
        self._temp = ITC(get_gpib_device(24))
        self._sweep_rate = sweep_rate
        self._voltage = voltage
        self._current_limit = current_limit
        self._gpib = gpib
            
        if not (0 <= temperature_end <= 299): 
            print("end temperature too high or too low. (0 ... 299)")
            self.abort()
            return  
            
        if not (0 <= sweep_rate <= 2.5): 
            print("you're insane! sweep rate is too high. (0 ... 2.5)")
            self.abort()
            return   
            
        resource_man = ResourceManager('@py')
        resource = resource_man.open_resource(self._gpib)
            
        self._device = SMU2ProbeIvTBlue._get_sourcemeter(resource)
        self._device.voltage_driven(0, current_limit, nplc)
            
        self._temperature_end = temperature_end
        
        self._last_toggle = time()
        
        sleep(1)

    @staticmethod
    def number_of_contacts():
        return Contacts.FOUR
        
    @staticmethod
    def _get_sourcemeter(resource):
        identification = resource.query('*IDN?')
        print('DEBUG', identification)
        if '2400' in identification:
            return Sourcemeter2400(resource)
        elif '2602' in identification:
            return Sourcemeter2602A(resource)
        elif '2636' in identification:
            return Sourcemeter2636A(resource)
        else:
            raise ValueError('Sourcemeter "{}" not known.'.format(identification))
            
    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'temperature_end': FloatValue('Target temperature', default=295),
                'comment': StringValue('Comment', default=''),
                'gpib': GPIBPathValue('GPIB Address', default='GPIB0::12::INSTR'),
                'voltage' : FloatValue('Voltage', default=0.1),
                'current_limit': FloatValue('Current Limit', default=1e-6),
                'sweep_rate': FloatValue('Sweep Rate [K/min]', default=1)
                }

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'G': FloatValue('Conductance'),
                'I': FloatValue('Current'),
                'T': FloatValue('Temperature')}

    @property
    def recommended_plots(self) -> List[PlotRecommendation]:
        return [PlotRecommendation('Current Monitoring', x_label='T', y_label='I', show_fit=False),
                PlotRecommendation('Conductance Monitoring', x_label='T', y_label='G', show_fit=False)]

    def _measure(self, file_handle):
        self.__write_header(file_handle)
        sleep(0.5)
        
        self._start_sweep()

        while not self._should_stop.is_set():
            try:
                self._acquire_data_point(file_handle)
            except:
                print('{} failed to acquire datapoint.'.format(datetime.now().isoformat()))
                traceback.print_exc()
                
            self._toggle_pid_if_necessary()

        self.__deinitialize_device()

    def _start_sweep(self):
        current_temperature = self._temp.T1
        
        sweep_time = abs((current_temperature - self._temperature_end) / self._sweep_rate)
        
        self._temp.temperature_set_point = current_temperature
        self._temp.set_temperature_sweep(self._temperature_end, sweep_time = sweep_time)
        self._temp.start_temperature_sweep()

    def _toggle_pid_if_necessary(self):
        current_temperature = self._temp.T1
        
        if 20 < current_temperature < 30 and time() - self._last_toggle > 100:
            self._temp.toggle_pid_auto(False)
            sleep(0.5)
            self._temp.toggle_pid_auto(True)
    

    def _acquire_data_point(self, file_handle):
        voltage, current = self.__measure_data_point()
        T1, T2, T3 = self._temp.T1, self._temp.T2, self._temp.T3
        
        file_handle.write('{} {} {} {} {} {}\n'.format(datetime.now().isoformat(), 
                                                       voltage, current, T1, T2, T3))
        file_handle.flush()
        
        conductance = current / voltage
        
        self._signal_interface.emit_data({'G': conductance, 'I': current, 'T': T3})
        
        

    def __deinitialize_device(self) -> None:
        self._temp.stop_temperature_sweep()

    def __write_header(self, file_handle: TextIO) -> None:
        file_handle.write("# {0}\n".format(datetime.now().isoformat()))
        file_handle.write('# {}\n'.format(self._comment))
        file_handle.write('# {} V\n'.format(self._voltage))      
        file_handle.write('# {} A-max\n'.format(self._current_limit))  
        file_handle.write("# sweep rate {0} K/min\n".format(self._sweep_rate))
        file_handle.write("Datetime Voltage Current T1 T2 T3\n")

    def __measure_data_point(self):
        return self._device.read()

