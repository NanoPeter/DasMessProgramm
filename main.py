from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication
from threading import Thread

from windows.table_window import TableWindow
import pandas as pd

from datetime import datetime
from time import sleep


class Test:
    """A Test class to test if qt signals are able to transport nonstandard objects
    """
    def __init__(self):
        self.foo = 'bar'

    def run(self, arg1):
        print(arg1, self.foo)


class SignalInterface:
    """An typical
    """
    def emit_finished(self, data):
        NotImplementedError()

    def emit_data(self, data):
        NotImplementedError()


class SignalDataAcquisition(QtCore.QObject, SignalInterface):
    finished = QtCore.pyqtSignal(object)
    data = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()

    def emit_finished(self, something):
        self.finished.emit(something)

    def emit_data(self, something):
        self.data.emit(something)


class Emitter(Thread):
    def __init__(self, signal_interface):
        super().__init__()

        self.signal_interface = signal_interface

    def run(self):
        self.signal_interface.emit_data('some data string')
        sleep(2)
        self.signal_interface.emit_finished(Test())

class Main(QtWidgets.QMainWindow):

    def __init__(self):
        super(Main, self).__init__()

        si = SignalDataAcquisition()

        self.__handle_strategies = {Test: self.__handle_test}

        self.e = Emitter(si)
        si.finished.connect(self.__finished)
        self.e.start()

        self.__init_gui()

    def __init_gui(self):
        bar = self.menuBar()
        method = bar.addMenu('Method')

        registry = ['SMUTwoProbe', 'LockInFourProbe']

        for entry in registry:
            method.addAction(entry, lambda x=entry: self.__menu_clicked(x))

        self.__mdi = QtWidgets.QMdiArea()

        self.setCentralWidget(self.__mdi)

        self.__tb_window = TableWindow()
        self.__mdi.addSubWindow(self.__tb_window)

        df = pd.DataFrame({'U': [1, 2, 3, 4, 5, 6],
                           'I': [-3, 2, -1, 4, 1, 2],
                           'Datetime': [datetime.now(), datetime.now(), datetime.now(),
                                        datetime.now(), datetime.now(), datetime.now()]})

        self.__tb_window.update_data(df)

    def __menu_clicked(self, x):
        df = pd.DataFrame({'U': [1, 2, 3, 4, 5, 6, 7],
                           'I': [1, 1, 1, 1, 1, 1, 1],
                           'Datetime': [datetime.now(), datetime.now(), datetime.now(),
                                        datetime.now(), datetime.now(), datetime.now(), datetime.now()]})

        self.__tb_window.update_data(df)
        print(x)

    def __handle_test(self, test):
        test.run('test')

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
