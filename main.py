from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication
from threading import Thread


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
        self.signal_interface.emit_finished(Test())
        self.signal_interface.emit_finished('some string')
        self.signal_interface.emit_data('some data string')


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

    @staticmethod
    def __menu_clicked(self, x):
        print(x)

    @staticmethod
    def __handle_test(test):
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
