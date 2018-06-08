from .measurement import register, SignalInterface, AbstractValue, AbstractMeasurement, Contacts, PlotRecommendation
from .measurement import FloatValue, IntegerValue, StringValue, DatetimeValue

from visa import ResourceManager
from scientificdevices.keithley.sourcemeter2400 import Sourcemeter2400
from scientificdevices.keithley.sourcemeter2602A import Sourcemeter2602A, SMUChannel


from typing import Tuple, Dict
from datetime import datetime

@register('ALD 2probe multiple SET monitor')
class ald_2probe_multiple_set_monitor(AbstractMeasurement):

    GPIB_RESOURCE_2400_1 = 'GPIB0::10::INSTR'
    GPIB_RESOURCE_2602A = 'GPIB0::12::INSTR'
    GPIB_RESOURCE_2400_2 = 'GPIB0::13::INSTR'

    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 v: float = 0.0, i: float = 1e-6,
                 nplc: int = 3, comment: str = ''):

        super().__init__(signal_interface, path, contacts)

        self._max_voltage = v
        self._current_limit = i
        self._nplc = nplc
        self._comment = comment

        self._init_smus()

    def _init_smus(self):
        rm = ResourceManager('@py')
        dev1 = rm.open_resource(self.GPIB_RESOURCE_2400_1)
        dev2 = rm.open_resource(self.GPIB_RESOURCE_2400_2)
        dev3 = rm.open_resource(self.GPIB_RESOURCE_2602A)

        self._smus = [Sourcemeter2400(dev1),
                      Sourcemeter2400(dev2),
                      Sourcemeter2602A(dev3, sub_device=SMUChannel.channelA),
                      Sourcemeter2602A(dev3, sub_device=SMUChannel.channelB)]

        for smu in self._smus:
            smu.voltage_driven(self._max_voltage)

    @staticmethod
    def number_of_contacts():
        return Contacts.NONE

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'nplc': IntegerValue('NPLC', default=1),
                'comment': StringValue('Comment', default='')}

    @staticmethod
    def outputs() -> Dict[str, AbstractValue]:
        return {'v1': FloatValue('Voltage [V]'),
                'i1': FloatValue('Current [A]'),
                'c1': FloatValue('Conductance [S]'),
                'v2': FloatValue('Voltage [V]'),
                'i2': FloatValue('Current [A]'),
                'c2': FloatValue('Conductance [S]'),
                'v3': FloatValue('Voltage [V]'),
                'i3': FloatValue('Current [A]'),
                'c3': FloatValue('Conductance [S]'),
                'v4': FloatValue('Voltage [V]'),
                'i4': FloatValue('Current [A]'),
                'c4': FloatValue('Conductance [S]'),
                'datetime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self) -> Dict[str, Tuple[str, str]]:
        return [PlotRecommendation('Sample1 - Conductance vs. Time',
                                   x_label='datetime', y_label='c1'),
                PlotRecommendation('Sample2 - Conductance vs. Time',
                                   x_label='datetime', y_label='c2'),
                PlotRecommendation('Sample3 - Conductance vs. Time',
                                   x_label='datetime', y_label='c3'),
                PlotRecommendation('Sample4 - Conductance vs. Time',
                                   x_label='datetime', y_label='c4')
                ]

    def _measure(self, file_handle):
        self.__write_header(file_handle)

        self.__arm_devices()

        while not self._should_stop.is_set():
            data = self.__get_data()
            self.__write_data(data, file_handle=file_handle)
            self.__send_data(data)
        else:
            self._signal_interface.emit_aborted()

        self.__disarm_devices()


    def __write_header(self, file_handle):
        file_handle.write("# {0}\n".format(datetime.now().isoformat()))
        file_handle.write('# {}\n'.format(self._comment))
        file_handle.write("# maximum voltage {0} V\n".format(self._max_voltage))
        file_handle.write("# current limit {0} A\n".format(self._current_limit))
        file_handle.write('# nplc {}\n'.format(self._nplc))
        file_handle.write("Datetime Voltage1 Current1 Conductance1 Voltage2 Current2 Conductance2 Voltage3 Current3 Conductance3 Voltage4 Current4 Conductance4\n")

    def __get_data(self):
        all_data = {}
        for index, smu in enumerate(self._smus):
            v_string = 'v{}'.format(index + 1)
            i_string = 'i{}'.format(index + 1)
            c_string = 'c{}'.format(index + 1)

            data = smu.read()

            all_data[v_string] = data[0]
            all_data[i_string] = data[1]
            if data[0] != 0:
                all_data[c_string] = data[1] / data[0]
            else:
                all_data[c_string] = float('nan')

        all_data['datetime'] = datetime.now()

        return all_data

    def __send_data(self, data):
        self._signal_interface.emit_data(data)

    def __write_data(self, data, file_handle):
        datetime_string = data['datetime'].isoformat()
        file_handle.write('{datetime} {data[v1]} {data[i1]} {data[c1]} {data[v2]} {data[i2]} {data[c2]} {data[v3]} {data[i3]} {data[c3]} {data[v4]} {data[i4]} {data[c4]}\n'.format(datetime=datetime_string, data=data))

    def __arm_devices(self):
        for smu in self._smus:
            smu.set_voltage(self._max_voltage)
            smu.arm()

    def __disarm_devices(self):
        for smu in self._smus:
            smu.set_voltage(0)
            smu.disarm()
