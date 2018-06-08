from .measurement import register, SignalInterface, AbstractValue, AbstractMeasurement, Contacts, PlotRecommendation
from .measurement import FloatValue, IntegerValue, StringValue, DatetimeValue

from visa import ResourceManager
from scientificdevices.keithley.sourcemeter2400 import Sourcemeter2400
from scientificdevices.keithley.sourcemeter2602A import Sourcemeter2602A, SMUChannel
from scientificdevices.keithley.sourcemeter2636A import Sourcemeter2636A

from typing import Tuple, Dict, List
from datetime import datetime


@register('ALD 2probe multiple SET monitor')
class Ald2ProbeMultipleSETMonitor(AbstractMeasurement):

    GPIB_RESOURCE_2400_1 = 'GPIB0::10::INSTR'
    GPIB_RESOURCE_2602A = 'GPIB0::12::INSTR'
    GPIB_RESOURCE_2400_2 = 'GPIB0::13::INSTR'

    def __init__(self, signal_interface: SignalInterface,
                 path: str, contacts: Tuple[str, str],
                 sample1_v: float = 0.0, sample1_i: float = 1e-6,
                 sample1_nplc: int = 3, sample1_comment: str = '',
                 sample2_v: float = 0.0, sample2_i: float = 1e-6,
                 sample2_nplc: int = 3, sample2_comment: str = '',
                 sample3_v: float = 0.0, sample3_i: float = 1e-6,
                 sample3_nplc: int = 3, sample3_comment: str = '',
                 sample4_v: float = 0.0, sample4_i: float = 1e-6,
                 sample4_nplc: int = 3, sample4_comment: str = ''):

        super().__init__(signal_interface, path, contacts)

        self._sample1 = {'v': sample1_v, 'i': sample1_i, 'nplc': sample1_nplc, 'comment': sample1_comment}
        self._sample2 = {'v': sample2_v, 'i': sample2_i, 'nplc': sample2_nplc, 'comment': sample2_comment}
        self._sample3 = {'v': sample3_v, 'i': sample3_i, 'nplc': sample3_nplc, 'comment': sample3_comment}
        self._sample4 = {'v': sample4_v, 'i': sample4_i, 'nplc': sample4_nplc, 'comment': sample4_comment}

        self._samples = [self._sample1, self._sample2, self._sample3, self._sample4]

        self._init_smus()

    def _init_smus(self):
        rm = ResourceManager('@py')
        dev1 = rm.open_resource(self.GPIB_RESOURCE_2400_1)
        dev2 = rm.open_resource(self.GPIB_RESOURCE_2400_2)
        dev3 = rm.open_resource(self.GPIB_RESOURCE_2602A)

        self._smus = [Sourcemeter2400(dev1),
                      Sourcemeter2400(dev2),
                      Sourcemeter2636A(dev3, sub_device=SMUChannel.channelA),
                      Sourcemeter2636A(dev3, sub_device=SMUChannel.channelB)]

        for index, smu in enumerate(self._smus):
            sample = self._samples[index]
            smu.voltage_driven(sample['v'], current_limit=sample['i'], nplc=sample['nplc'])

    @staticmethod
    def number_of_contacts():
        return Contacts.NONE

    @staticmethod
    def inputs() -> Dict[str, AbstractValue]:
        return {'sample1_v': FloatValue('(1) Maximum Voltage', default=1e-3),
                'sample1_i': FloatValue('(1) Current Limit', default=1e-6),
                'sample1_nplc': IntegerValue('(1) NPLC', default=1),
                'sample1_comment': StringValue('(1) Comment'),
                'sample2_v': FloatValue('(2) Maximum Voltage', default=1e-3),
                'sample2_i': FloatValue('(2) Current Limit', default=1e-6),
                'sample2_nplc': IntegerValue('(2) NPLC', default=1),
                'sample2_comment': StringValue('(2) Comment'),
                'sample3_v': FloatValue('(3) Maximum Voltage', default=1e-3),
                'sample3_i': FloatValue('(3) Current Limit', default=1e-6),
                'sample3_nplc': IntegerValue('(3) NPLC', default=1),
                'sample3_comment': StringValue('(3) Comment'),
                'sample4_v': FloatValue('(4) Maximum Voltage', default=1e-3),
                'sample4_i': FloatValue('(4) Current Limit', default=1e-6),
                'sample4_nplc': IntegerValue('(4) NPLC', default=1),
                'sample4_comment': StringValue('(4) Comment')
                }

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
    def recommended_plots(self) -> List[PlotRecommendation]:
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
        for index, smu in enumerate(self._smus):
            sample = self._sample[index]
            file_handle.write('#\n')
            file_handle.write('# {}\n'.format(str(smu)))
            file_handle.write('# {}\n'.format(sample['comment']))
            file_handle.write("# applied voltage {} V\n".format(sample['v']))
            file_handle.write("# current limit {} A\n".format(sample['i']))
            file_handle.write('# nplc {}\n'.format(sample['nplc']))
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
