from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication
from threading import Thread

from measurement.measurement import FloatInput, IntegerInput
from windows.table_window import TableWindow
import pandas as pd

from datetime import datetime
from time import sleep
from typing import Dict, List


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

    input_validators = {int: QtGui.QIntValidator,  # Qt-internal checks for different input widget types
                        float: QtGui.QDoubleValidator,
                        str: None}
    
    def __init__(self):
        super(Main, self).__init__()

        si = SignalDataAcquisition()

        self.__handle_strategies = {Test: self.__handle_test}

        self.e = Emitter(si)
        si.finished.connect(self.__finished)
        self.e.start()

        self.__directory_name = ""
        self.__dynamic_inputs = list()  # type: List[QtWidgets.QLineEdit]
        
        self.__init_gui()

        # DEBUG:
        self.__create_input_ui({
            'v': FloatInput('Maximum Voltage', default=0.0),
            'i': FloatInput('Current Limit', default=1e-6),
            'nplc': IntegerInput('NPLC', default=1)})

    def __init_gui(self):
        bar = self.menuBar()
        method = bar.addMenu('Method')

        registry = ['SMUTwoProbe', 'LockInFourProbe']

        for entry in registry:
            method.addAction(entry, lambda x=entry: self.__menu_clicked(x))


        central_layout = QtWidgets.QHBoxLayout()
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(central_layout)
        
        inputs_layout = QtWidgets.QVBoxLayout()
        central_layout.addLayout(inputs_layout)

        file_name_layout = QtWidgets.QVBoxLayout()
        inputs_layout.addLayout(file_name_layout)
        file_name_layout.setSpacing(5)
        file_name_layout.addWidget(QtWidgets.QLabel("Save directory:"))
        self.__file_name_display = QtWidgets.QLineEdit()
        self.__file_name_display.setFixedWidth(180)  # Also sets left panel width
        file_name_layout.addWidget(self.__file_name_display)
        self.__file_name_display.setReadOnly(True)
        self.__file_name_display.textChanged.connect(
            lambda text: self.__file_name_display.setToolTip(text)
        )
        self.__file_name_display.setText(self.__directory_name)
        file_name_button = QtWidgets.QPushButton()
        file_name_layout.addWidget(file_name_button)
        file_name_button.setText("Select directory...")
        file_name_button.clicked.connect(self.__set_directory_name)

        # This layout contains the dynamically managed inputs:
        self.__dynamic_inputs_layout = QtWidgets.QVBoxLayout()
        self.__dynamic_inputs_layout.setSpacing(15)
        file_name_layout.addLayout(self.__dynamic_inputs_layout)

        inputs_layout.addStretch()

        self.__mdi = QtWidgets.QMdiArea()
        central_layout.addWidget(self.__mdi)

        self.setCentralWidget(central_widget)

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

    def __create_input_ui(self, inputs):
        """Dynamically set left panel user input widgets.
        
        Arguments:
            inputs: Dict[str, AbstractInput]: A dictionary of inputs as defined in SMU2Probe.inputs
        """
        self.__dynamic_inputs.clear()

        for element in list(inputs.keys()):
            element_layout = QtWidgets.QVBoxLayout()
            element_layout.setSpacing(0)
            self.__dynamic_inputs_layout.addLayout(element_layout)

            element_name = inputs[element].fullname
            element_layout.addWidget(QtWidgets.QLabel(element_name))  # Header text

            element_input_field = QtWidgets.QLineEdit()
            self.__dynamic_inputs.append(element_input_field)
            element_layout.addWidget(element_input_field)
            
            # Validate the input field if it is numerical:
            element_type = inputs[element].type
            element_input_validator = self.input_validators[element_type]  # This is a type object
            if element_input_validator is not None:
                element_input_field.setValidator(element_input_validator())

            element_default = inputs[element].default
            element_input_field.setText(str(element_default))

            
    @QtCore.pyqtSlot()
    def __set_directory_name(self):
        """Open a dialogue to change the output directory."""
        self.__directory_name = QtWidgets.QFileDialog.getExistingDirectoryUrl().path() + "/"




if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    m = Main()
    m.show()
    sys.exit(app.exec_())
