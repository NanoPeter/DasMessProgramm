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


@register('Two Probe I-V Automatic Temperature Sweep (blue)')
class SMUTempSweepIV(AbstractMeasurement):


    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 v: float = 0.0, i: float = 1e-6,
                 nplc: int = 3, comment: str = '', time_difference: float=0, gpib: str='GPIB0::10::INSTR',
                 temperatures: str = '[2,10,100,300]'):
        super().__init__(signal_interface, path, contacts)
        self._max_voltage = v
        self._current_limit = i
        self._nplc = nplc
        self._comment = comment
        self._time_difference = time_difference
        self._gpib = gpib

        resource_man = ResourceManager('@py')
        resource = resource_man.open_resource(self._gpib)
        resource.timeout = 30000

        self._device = SMUTempSweepIV._get_sourcemeter(resource)
        self._device.voltage_driven(0, i, nplc)
        
        self._temp =  ITC(get_gpib_device(24))
        
        step1 = np.linspace(0, self._max_voltage, 25, endpoint=False)
        step2 = np.linspace(self._max_voltage, -self._max_voltage, 50, endpoint=False)
        step3 = np.linspace(-self._max_voltage, 0, 25)
        self._voltages = np.concatenate((step1, step2, step3))

        try:
            self._temperatures = literal_eval(temperatures)
        except:
            print('ERROR', 'Malformed String for Temperatures')
            self.abort()
            return
            

        if type(self._temperatures) is not list:
            print('ERROR', 'Temperature String is not a List')
            self.abort()
            return
            
        for k in self._temperatures:
            t = type(k)
            
            if t is not int and t is not float:
                print('ERROR', 'Temperature List does not only contain ints or floats')
                self.abort()
                return
                
        self._temperatures = np.array(self._temperatures)
                

    @staticmethod
    def number_of_contacts():
        return Contacts.TWO

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
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'nplc': IntegerValue('NPLC', default=1),
                'comment': StringValue('Comment', default=''),
                'gpib': GPIBPathValue('GPIB Address', default='GPIB0::10::INSTR'),
                'temperatures': StringValue('Temperatures', default='[2,10,100.0,300]')
                }

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'R': FloatValue('Resistance'),
                'T': DatetimeValue('Temperature')}

    @property
    def recommended_plots(self) -> List[PlotRecommendation]:
        return [PlotRecommendation('Conductance Monitoring', x_label='T', y_label='R', show_fit=False)]

    def _measure(self, file_handle):
        """Custom measurement code lives here.
        """
        self.__write_header(file_handle)
        sleep(0.5)
        

        for next_temperature in self._temperatures:
            if self._should_stop.is_set():
                break

            self._goto_temperature_and_stabilize(next_temperature)  
            self._acquire_i_v_u_curve(file_handle)

        self.__deinitialize_device()

         
    def _goto_temperature_and_stabilize(self, temperature):
        ramp = 2.0
        current_temperature = self._temp.T1
        
        sweep_time = abs((current_temperature - temperature) / ramp)
        
        self._temp.temperature_set_point = current_temperature
        self._temp.set_temperature_sweep(temperature, sweep_time = sweep_time)
        self._temp.start_temperature_sweep()
        
        temperatures = []
        
        temperature_reached = False
        last_toggle_time = time()
        
        print('DEBUG','new set temperature: {}'.format(temperature))
        
        while not temperature_reached:
            if len(temperatures) > 300:
                temperatures = temperatures[1:300]
            try:
                temperatures.append(self._temp.T1)
            except:
                temperatures.append(self._temp.T1)
            
            if 20 < temperatures[-1] < 30 and time() - last_toggle_time >= 10:
                self._temp.toggle_pid_auto(False)
                sleep(1)
                self._temp.toggle_pid_auto(True)
                last_toggle_time = time()

            # letzten 10 sekunden
            deviation = np.abs(np.mean(temperatures[-10:]) - temperature) / temperature
            
            if deviation < 0.01:
                temperature_reached = True
            else:
                sleep(1)
            
            if self._should_stop.is_set():
                self._temp.stop_temperature_sweep()
                return
                
        print('DEBUG','temperature reached, waiting for stabilization')
            
        temperature_stabilized = False
        timeout_start = time()
        relative_std = 0
        
        while time() - timeout_start < 1000 and not temperature_stabilized:
            if len(temperatures) == 300:
                temperatures = temperatures[1:]
                
            try:
                temperatures.append(self._temp.T1)
            except:
                temperatures.append(self._temp.T1)
        
            relative_std = np.std(temperatures) / temperature
        
            if relative_std < 0.01:
                temperature_stabilized = True
            else:
                sleep(1)
        
            if self._should_stop.is_set():
                self._temp.stop_temperature_sweep()
                return
                
        print('DEBUG','temperature is now stabilized (hopefully), waited time: {}s'.format(time() - timeout_start))
                
        if not temperature_stabilized:
            print('WARNING', ' I was too impatient to stabilize the temperature, relative std was: {}'.format(relative_std))
        
            
            
        
         
    def _acquire_i_v_u_curve(self, file_handle):
        self._device.arm()
        
        voltages = []
        currents = []
        temperatures = []
        
        print('DEBUG','start voltage sweep')
        for voltage in self._voltages:
            if self._should_stop.is_set():
                self._device.disarm()
                return
                
            self._device.set_voltage(voltage)
            sleep(0.1)
            try:
                voltage, current = self.__measure_data_point()
            except:
                file_handle.write("# error while collecting data\n")
                print('ERROR', '-'*74)
                traceback.print_exc()
                continue
                
            try:
                T1 = self._temp.T1
                T2 = self._temp.T2
                T3 = self._temp.T3   
            except:
                T1 = self._temp.T1
                T2 = self._temp.T2
                T3 = self._temp.T3   
            
            voltages.append(voltage)
            currents.append(current)
            temperatures.append(T3)

        
            timestamp = datetime.now()
            file_handle.write("{} {} {} {} {} {}\n".format(timestamp.isoformat(), voltage, current, T1, T2, T3))
            file_handle.flush()
        
        self._device.disarm()
        try:
            R, _ = np.polyfit(currents, voltages, 1)
            self._signal_interface.emit_data({'R': R, 'T': np.mean(temperatures)})
        except:
            print('ERROR', '-'*74)
            traceback.print_exc()


    def __deinitialize_device(self) -> None:
        self._temp.stop_temperature_sweep()
        self._device.set_voltage(0)
        self._device.disarm()

    def __write_header(self, file_handle: TextIO) -> None:
        """Write a file header for present settings.

        Arguments:
            file_handle: The open file to write to
        """
        file_handle.write("# {0}\n".format(datetime.now().isoformat()))
        file_handle.write('# {}\n'.format(self._comment))
        file_handle.write("# maximum voltagepython {0} V\n".format(self._max_voltage))
        file_handle.write("# current limit {0} A\n".format(self._current_limit))
        file_handle.write('# nplc {}\n'.format(self._nplc))
        file_handle.write("Datetime Voltage Current T1 T2 T3\n")

    def __measure_data_point(self) -> Tuple[float, float]:
        """Return one data point: (voltage, current).

        Device must be initialised and armed.
        """
        return self._device.read()
