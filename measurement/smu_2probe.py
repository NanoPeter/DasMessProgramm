from .measurement import register, AbstractMeasurement, Contacts
from .measurement import FloatValue, IntegerValue, DatetimeValue, BooleanValue


@register('SourceMeter two probe voltage sweep')
class SMU2Probe(AbstractMeasurement):
    def __init__(self, signal_interface):
        super().__init__(signal_interface)
        self._number_of_contacts = Contacts.TWO

    @property
    def inputs(self):
        return {'v': FloatValue('Maximum Voltage', default=0.0),
                'i': FloatValue('Current Limit', default=1e-6),
                'n': IntegerValue('Number of Points', default=100),
                'nplc': IntegerValue('')}

    @property
    def outputs(self):
        return {'v': FloatValue('Voltage'),
                'i': FloatValue('Current'),
                'DateTime': DatetimeValue('Timestamp')}

    @property
    def recommended_plots(self):
        return {'dummy': ('v', 'i')}

    def initialize(self, path, contacts, v=0.0, i=1e-6, n=100, nplc=3):
        """

        :param path: Location where all the measurements shall be saved
        :param contacts: contact pair as tuple
        :param v: maximal voltage to
        :param i:
        :param nplc:
        :return:
        """
        pass

    def run(self):
        self._signal_interface.emit_started()
        #do stuff
        self._signal_interface.emit_finished()
