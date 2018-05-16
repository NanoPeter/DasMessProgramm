from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication

from windows.table_window import TableWindow
from windows.plot_window import PlotWindow
import pandas as pd

from datetime import datetime

import measurement
from measurement.measurement import SignalInterface


class SignalDataAcquisition(QtCore.QObject, SignalInterface):
    finished = QtCore.pyqtSignal(object)
    data = QtCore.pyqtSignal(object)
    started = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def emit_finished(self, something):
        self.finished.emit(something)

    def emit_data(self, something):
        self.data.emit(something)

    def emit_started(self):
        self.started.emit()


class Main(QtWidgets.QMainWindow):

    def __init__(self):
        super(Main, self).__init__()

        self.__signal_interface = SignalDataAcquisition()
        self.__signal_interface.finished.connect(self.__finished)
        self.__signal_interface.data.connect(self.__new_data)

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

        self.__df = pd.DataFrame()

        self.__plot_windows = {}

    def __menu_measurement_selected(self, x):
        print('DEBUG', 'selected', x, measurement.REGISTRY[x])

        self.__measurement = measurement.REGISTRY[x](self.__signal_interface)
        self.__create_input_ui(self.__measurement.inputs)

        for input in self.__measurement.inputs:
            print(input)

        self.__df = pd.DataFrame()

        self.__plot_windows = {}

        for title, pair in self.__measurement.recommended_plots.items():
            if pair not in self.__plot_windows:
                x_label = self.__measurement.outputs[pair[0]].fullname
                y_label = self.__measurement.outputs[pair[1]].fullname

                print(x_label, y_label)

                window = PlotWindow(title=title, x_label=x_label, y_label=y_label)
                self.__plot_windows[pair] = window
                self.__mdi.addSubWindow(window)
                window.show()

        if x == 'Dummy Measurement':
            self.__measurement.initialize('/', (1, 2), n=50)
            self.__measurement.start()

    def __create_input_ui(self, inputs):
        pass

    def __finished(self, data_dict):
        pass

    def __new_data(self, data_dict):

        self.__df = self.__df.append(data_dict, ignore_index=True)
        self.__tb_window.update_data(self.__df)

        for pair, window in self.__plot_windows.items():
            window.update_data(self.__df[list(pair)])


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    m = Main()
    m.show()
    sys.exit(app.exec_())
