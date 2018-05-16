from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication

from measurement.measurement import FloatValue, IntegerValue, StringValue
from windows.table_window import TableWindow
from windows.plot_window import PlotWindow
from windows.dynamic_input import DynamicInputLayout
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

    def __init__(self):
        super(Main, self).__init__()

        self.__signal_interface = SignalDataAcquisition()
        self.__signal_interface.finished.connect(self.__finished)
        self.__signal_interface.data.connect(self.__new_data)

        self.__directory_name = ""

        self.__init_gui()

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

        self.__inputs_layout = QtWidgets.QVBoxLayout()
        central_layout.addLayout(self.__inputs_layout)

        file_name_layout = QtWidgets.QVBoxLayout()
        self.__inputs_layout.addLayout(file_name_layout)
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

        self.__dynamic_inputs_layout = None  # Initialised on-demand from menu bar
        self.__inputs_layout.addStretch()
        
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
        # Remove old dynamic layout, if any:
        if self.__dynamic_inputs_layout is not None:

            def delete_children(layout):
                while layout.count() > 0:
                    child = layout.takeAt(0)
                    if child.widget() is not None:
                        child.widget().deleteLater()
                    elif child.layout() is not None:
                        delete_children(child.layout())

            delete_children(self.__dynamic_inputs_layout)
            self.__inputs_layout.removeItem(self.__dynamic_inputs_layout)
            del self.__dynamic_inputs_layout
        
        self.__dynamic_inputs_layout = DynamicInputLayout(inputs)
        self.__dynamic_inputs_layout.setSpacing(15)

        # Remove old stretch before adding new one below:
        old_stretch = self.__inputs_layout.takeAt(self.__inputs_layout.count() - 1)
        self.__inputs_layout.removeItem(old_stretch)
        
        self.__inputs_layout.addLayout(self.__dynamic_inputs_layout, -1)
        self.__inputs_layout.addStretch()

    def __get_input_arguments(self):
        """Return a dictionary of input names with their user-set values.

        Names are not the full names of an input but their dictionary index.
        """
        # TODO: Adapt to new external DynamicInputLayout class.
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
