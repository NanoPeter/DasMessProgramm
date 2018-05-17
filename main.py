from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication

from windows.table_window import TableWindow
from windows.plot_window import PlotWindow
from windows.dynamic_input import DynamicInputLayout, delete_children
import pandas as pd

import os
from threading import Thread

import measurement
from measurement.measurement import SignalInterface, Contacts
from typing import Dict, List


class SignalDataAcquisition(QtCore.QObject, SignalInterface):
    finished = QtCore.pyqtSignal(object)
    data = QtCore.pyqtSignal(object)
    started = QtCore.pyqtSignal()
    aborted = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def emit_finished(self, something):
        self.finished.emit(something)

    def emit_data(self, something):
        self.data.emit(something)

    def emit_started(self):
        self.started.emit()

    def emit_aborted(self):
        self.aborted.emit()


class Main(QtWidgets.QMainWindow):

    CONTACT_NUMBERS = [ 
        "05 I-7", "06 I-8", "02 I-2", "04 I-4", "03 I-3", "01 I-1",
        "07 II-1", "09 II-3", "10 II-4", "08 II-2", "12 II-8", "11 II-7", 
        "17 III-7", "18 III-8", "14 III-2", "16 III-4", "15 III-3", "13 III-1",
        "19 IV-1", "21 IV-3", "22 IV-4","20 IV-2", "24 IV-8", "23 IV-7"
    ]

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
        self.__file_name_display.setFixedWidth(200)  # Also sets left panel width
        file_name_layout.addWidget(self.__file_name_display)
        self.__file_name_display.setReadOnly(True)
        self.__file_name_display.textChanged.connect(
            lambda text: self.__file_name_display.setToolTip(text)
        )
        self.__file_name_display.setText(self.__directory_name)
        directory_button = QtWidgets.QPushButton()
        file_name_layout.addWidget(directory_button)
        directory_button.setText("Browse...")
        directory_button.clicked.connect(self.__set_directory_name)

        contacts_layout = QtWidgets.QVBoxLayout()
        self.__inputs_layout.addLayout(contacts_layout)
        contacts_layout.setSpacing(5)
        contacts_layout.addWidget(QtWidgets.QLabel("Contacts:"))
        first_contact_pair = QtWidgets.QHBoxLayout()
        contacts_layout.addLayout(first_contact_pair)
        self.__contact_input_first = QtWidgets.QComboBox()
        first_contact_pair.addWidget(self.__contact_input_first)
        self.__contact_input_second = QtWidgets.QComboBox()
        first_contact_pair.addWidget(self.__contact_input_second)
        self.__sense_contacts_label = QtWidgets.QLabel("4-wire sense contacts:")
        contacts_layout.addWidget(self.__sense_contacts_label)
        second_contact_pair = QtWidgets.QHBoxLayout()
        contacts_layout.addLayout(second_contact_pair)
        self.__contact_input_third = QtWidgets.QComboBox()
        second_contact_pair.addWidget(self.__contact_input_third)
        self.__contact_input_fourth = QtWidgets.QComboBox()
        second_contact_pair.addWidget(self.__contact_input_fourth)
        for contact in self.CONTACT_NUMBERS:
            self.__contact_input_first.addItem(contact)
            self.__contact_input_second.addItem(contact)
            self.__contact_input_third.addItem(contact)
            self.__contact_input_fourth.addItem(contact)
        self.__contact_input_first.setCurrentIndex(0)
        self.__contact_input_first.setFixedWidth(80)
        self.__contact_input_second.setCurrentIndex(1)
        self.__contact_input_second.setFixedWidth(80)
        self.__contact_input_third.setCurrentIndex(2)
        self.__contact_input_third.setFixedWidth(80)
        self.__contact_input_fourth.setCurrentIndex(3)
        self.__contact_input_fourth.setFixedWidth(80)

        # TODO: make left hand side scrollable:
        self.__dynamic_inputs_layout = None  # Initialised on-demand from menu bar
        self.__inputs_layout.addStretch()

        right_side_layout = QtWidgets.QVBoxLayout()
        central_layout.addLayout(right_side_layout)
        self.__mdi = QtWidgets.QMdiArea()
        right_side_layout.addWidget(self.__mdi)

        button_layout = QtWidgets.QHBoxLayout()
        right_side_layout.addLayout(button_layout)
        button_layout.addStretch()
        
        self.__measure_button = QtWidgets.QPushButton("Measure")
        button_layout.addWidget(self.__measure_button)
        self.__measure_button.setFixedWidth(100)
        self.__measure_button.setEnabled(False)  # Buttons disabled while no method is selected

        self.__measure_button.clicked.connect(self.__start__measurement)

        self.__abort_button = QtWidgets.QPushButton("Abort")
        button_layout.addWidget(self.__abort_button)
        self.__abort_button.setFixedWidth(100)
        self.__abort_button.setEnabled(False)

        self.__abort_button.clicked.connect(self.__abort_measurement)

        self.__next_button = QtWidgets.QPushButton("Next")
        button_layout.addWidget(self.__next_button)
        self.__next_button.setFixedWidth(100)
        self.__next_button.setEnabled(False)
        
        self.setCentralWidget(central_widget)
        self.__tb_window = TableWindow()
        self.__mdi.addSubWindow(self.__tb_window)

        self.__plot_windows = {}

    def __menu_measurement_selected(self, x):
        for button in [self.__next_button, self.__abort_button, self.__measure_button]:
            button.setEnabled(True)
        
        self.__measurement = measurement.REGISTRY[x](self.__signal_interface)
        self.__create_input_ui(self.__measurement.inputs)

        if self.__measurement.number_of_contacts == Contacts.TWO:
            four_wire_visible = False
        elif self.__measurement.number_of_contacts == Contacts.FOUR:
            four_wire_visible = True
        self.__sense_contacts_label.setVisible(four_wire_visible)
        self.__contact_input_third.setVisible(four_wire_visible)
        self.__contact_input_fourth.setVisible(four_wire_visible)

    def __start__measurement(self):
        contacts = self.__get_contacts()
        path = self.__get_path()

        inputs = self.__dynamic_inputs_layout.get_inputs()

        while not os.path.isdir(path):
            result = QtWidgets.QMessageBox.critical(
                self, "Save directory not found!",
                "Click 'OK' to select a different one or "
                "'Cancel' to abort starting a measurement.",
                buttons=(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            )
            if result == QtWidgets.QMessageBox.Ok:
                self.__set_directory_name()
                path = self.__get_path()
            else:
                return

        self.__measurement.initialize(path, contacts, **inputs)
                
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

        thread = Thread(target=self.__measurement)
        thread.start()

    def __abort_measurement(self):
        self.__measurement.abort()

    def __get_contacts(self):

        contact_inputs = [self.__contact_input_first, self.__contact_input_second,
                          self.__contact_input_third, self.__contact_input_fourth]

        contacts = []

        for contact_input in contact_inputs:
            if contact_input.isVisible():
                contacts.append(contact_input.currentText().replace(' ', '_'))

        return tuple(contacts)

    def __get_path(self):
        return self.__file_name_display.text()

    def __finished(self, data_dict):
        # Save plots:
        for axis_label_pair in list(data_dict.keys()):
            if axis_label_pair in self.__plot_windows.keys():
                plot_window = self.__plot_windows[axis_label_pair]  # type: PlotWindow
                plot_path = data_dict[axis_label_pair]  # type: str
                plot_window.save_plot(plot_path)

    def __create_input_ui(self, inputs):
        """Dynamically set left panel user input widgets.

        Arguments:
            inputs: Dict[str, AbstractInput]: A dictionary of inputs as defined in SMU2Probe.inputs
        """
        # Remove old dynamic layout, if any:
        if self.__dynamic_inputs_layout is not None:
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

    @QtCore.pyqtSlot()
    def __set_directory_name(self):
        """Open a dialogue to change the output directory."""
        self.__directory_name = QtWidgets.QFileDialog.getExistingDirectory()
        self.__file_name_display.setText(self.__directory_name)

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
