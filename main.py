from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication

from measurement.measurement import FloatInput, IntegerInput
from windows.table_window import TableWindow
from windows.plot_window import PlotWindow
import pandas as pd

from datetime import datetime

import measurement
from measurement.measurement import SignalInterface
from typing import Dict, List


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

    input_validators = {int: QtGui.QIntValidator,  # Qt-internal checks for different input widget types
                        float: QtGui.QDoubleValidator,
                        str: None}

    def __init__(self):
        super(Main, self).__init__()

        self.__signal_interface = SignalDataAcquisition()
        self.__signal_interface.finished.connect(self.__finished)
        self.__signal_interface.data.connect(self.__new_data)

        self.__directory_name = ""
        self.__dynamic_inputs = dict()  # type: Dict[str, QtWidgets.QLineEdit]

        self.__init_gui()

        # DEBUG:
        self.__create_input_ui({
            'v': FloatInput('Maximum Voltage', default=0.0),
            'i': FloatInput('Current Limit', default=1e-6),
            'nplc': IntegerInput('NPLC', default=1)})

    def __init_gui(self):
        self.setWindowTitle('DasMessProgramm')
        bar = self.menuBar()
        method = bar.addMenu('Method')

        registry = measurement.REGISTRY.keys()

        for entry in registry:
            method.addAction(entry, lambda x=entry: self.__menu_measurement_selected(x))


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
        file_name_button.setText("Browse...")
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

    def __finished(self, data_dict):
        pass

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
            self.__dynamic_inputs[element] = element_input_field
            element_layout.addWidget(element_input_field)

            # Validate the input field if it is numerical:
            element_type = inputs[element].type
            element_input_validator = self.input_validators[element_type]  # This is a type object
            if element_input_validator is not None:
                element_input_field.setValidator(element_input_validator())

            element_default = inputs[element].default
            element_input_field.setText(str(element_default))

    def __get_input_arguments(self):
        """Return a dictionary of input names with their user-set values.

        Names are not the full names of an input but their dictionary index.
        """
        input_values = dict()
        for name in self.__dynamic_inputs:
            input_values[name] = self.__dynamic_inputs[name].text()

        return input_values

    @QtCore.pyqtSlot()
    def __set_directory_name(self):
        """Open a dialogue to change the output directory."""
        self.__directory_name = QtWidgets.QFileDialog.getExistingDirectoryUrl().path() + "/"


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
