from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication

from windows.table_window import TableWindow
import pandas as pd

from datetime import datetime

import measurement
from measurement.measurement import SignalInterface


class SignalDataAcquisition(QtCore.QObject, SignalInterface):
    finished = QtCore.pyqtSignal(object)
    data = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()

    def emit_finished(self, something):
        self.finished.emit(something)

    def emit_data(self, something):
        self.data.emit(something)


class Main(QtWidgets.QMainWindow):

    def __init__(self):
        super(Main, self).__init__()

        self.__signal_interface = SignalDataAcquisition()

        self.__init_gui()

    def __init_gui(self):
        self.setWindowTitle('DasMessProgramm')
        bar = self.menuBar()
        method = bar.addMenu('Method')

        registry = measurement.REGISTRY.keys()

        for entry in registry:
            method.addAction(entry, lambda x=entry: self.__menu_measurement_selected(x))

        self.__mdi = QtWidgets.QMdiArea()

        self.setCentralWidget(self.__mdi)

        self.__tb_window = TableWindow()
        self.__mdi.addSubWindow(self.__tb_window)

        df = pd.DataFrame({'U': [1, 2, 3, 4, 5, 6],
                           'I': [-3, 2, -1, 4, 1, 2],
                           'Datetime': [datetime.now(), datetime.now(), datetime.now(),
                                        datetime.now(), datetime.now(), datetime.now()]})

        self.__tb_window.update_data(df)

    def __menu_measurement_selected(self, x):
        print('DEBUG', 'selected', x, measurement.REGISTRY[x])

        self.__measurement = measurement.REGISTRY[x](self.__signal_interface)
        self.__create_input_ui(self.__measurement.inputs)

    def __create_input_ui(self, inputs):
        pass

    def __finished(self, data_object):
        print(type(data_object))

        data_type = type(data_object)

        if data_type in self.__handle_strategies:
            self.__handle_strategies[data_type](data_object)
        else:
            print(data_object)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    m = Main()
    m.show()
    sys.exit(app.exec_())
