#!/usr/bin/python3

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication

from main_ui import MainUI
from windows.table_window import TableWindow
from windows.plot_window import PlotWindow
from windows.dynamic_input import DynamicInputLayout, delete_children
import pandas as pd

import os
from threading import Thread

from datetime import datetime

import measurement
from measurement.measurement import SignalInterface, Contacts, AbstractMeasurement
from typing import Dict, List, Union, Tuple, Type

from configparser import ConfigParser

from windows.gpib_picker import GPIBPicker


class SignalDataAcquisition(QtCore.QObject, SignalInterface):
    finished = QtCore.pyqtSignal(object)
    data = QtCore.pyqtSignal(object)
    started = QtCore.pyqtSignal()
    aborted = QtCore.pyqtSignal()
    status = QtCore.pyqtSignal(str)

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

    def emit_status_message(self, message):
        self.status.emit(message)


class WrapAroundList(list):
    """A standard list with wrap-around indexing.
    
    Wrap-around indexing only for reading.
    """

    def __init__(self, items) -> None:
        super().__init__(items)

    def __getitem__(self, key: int):
        return super().__getitem__(self.wrap_around_index(key))

    def wrap_around_index(self, index: int) -> int:
        """Return the regular index for a wrap-around index."""
        if index >= 0:
            return index % len(self)
        else:
            return len(self) - (-index % len(self))


class Main(MainUI):
    """Main application window."""

    CONTACT_NUMBERS = WrapAroundList([
        "I-7", "I-8", "I-2", "I-4", "I-3", "I-1",
        "II-1", "II-3", "II-4", "II-2", "II-8", "II-7",
        "III-7", "III-8", "III-2", "III-4", "III-3", "III-1",
        "IV-1", "IV-3", "IV-4", "IV-2", "IV-8", "IV-7"
    ])

    TITLE = 'DasMessProgramm'

    SIDE_BAR_WIDTH = 210

    def __init__(self):
        super(Main, self).__init__()

        self._config = ConfigParser()
        self._config.read('settings.cfg')

        self.__signal_interface = SignalDataAcquisition()
        self.__signal_interface.finished.connect(self.__finished)
        self.__signal_interface.data.connect(self.__new_data)
        self.__signal_interface.aborted.connect(self.__measurement_aborted)
        self.__signal_interface.status.connect(self._show_status)
        self.__signal_interface.started.connect(self.__started)

        if 'general' in self._config:
            if 'last_folder' in self._config['general']:
                self._directory_name = self._config['general']['last_folder']
            else:
                self._directory_name = '/tmp'
        else:
            self._directory_name = '/tmp'

        self._measurement_class = AbstractMeasurement
        self._measurement = None  # type: AbstractMeasurement

        self._init_gui()
        self.__setup_connections()


    def __setup_connections(self):
        """Connect UI elements to slots that deal with measurement."""
        self._method_selection_box.currentTextChanged.connect(
            lambda title: self.__measurement_method_selected(title, measurement.REGISTRY[title])
        )
        self._measure_button.clicked.connect(self.__start__measurement)
        self._abort_button.clicked.connect(self.__abort_measurement)
        self._next_button.clicked.connect(self.__increment_contact_number)



    def __measurement_method_selected(self, title, cls: AbstractMeasurement):
        for button in [self._next_button, self._abort_button, self._measure_button]:
            button.setEnabled(True)

        self.setWindowTitle('{} -- {}'.format(self.TITLE, title))
        self._measurement_class = cls
        self._set_input_ui(cls)

        if cls.number_of_contacts() == Contacts.FOUR:
            four_wire_visible = True
        else:
            four_wire_visible = False

        self._sense_contacts_label.setVisible(four_wire_visible)
        self._contact_input_third.setVisible(four_wire_visible)
        self._contact_input_fourth.setVisible(four_wire_visible)
        self._next_button.setVisible(not four_wire_visible)

    def __start__measurement(self):
        contacts = self.__get_contacts()
        path = self.__get_path()

        inputs = self._dynamic_inputs_layout.get_inputs()

        while not os.path.isdir(path):
            result = QtWidgets.QMessageBox.critical(
                self, "Save directory not found!",
                "Click 'OK' to select a different one or "
                "'Cancel' to abort starting a measurement.",
                buttons=(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            )
            if result == QtWidgets.QMessageBox.Ok:
                self._set_directory_name()
                path = self.__get_path()
            else:
                return

        self._measurement = self._measurement_class(self.__signal_interface,
                                                    path, contacts, **inputs)
                
        self.__df = pd.DataFrame()

        self._plot_windows = {}

        for recommended_plot in self._measurement.recommended_plots:
            pair = (recommended_plot.x_label, recommended_plot.y_label)
            if pair not in self._plot_windows:
                outputs = self._measurement_class.outputs()
                x_label = outputs[pair[0]].fullname
                y_label = outputs[pair[1]].fullname
                
                window = PlotWindow(
                    recommended_plot,
                    "| Contacts: '{}' '{}'".format(self._contact_input_first.currentText(),
                                                   self._contact_input_second.currentText()),
                    x_axis_label=x_label, y_axis_label=y_label
                )
                self._plot_windows[pair] = window
                self._mdi.addSubWindow(window)
                window.show()

        thread = Thread(target=self._measurement)
        thread.start()

        self._set_ui_state(False)


    def __abort_measurement(self):
        self._measurement.abort()

    def __get_contacts(self) -> Tuple[str, ...]:
        contact_inputs = [self._contact_input_first, self._contact_input_second,
                          self._contact_input_third, self._contact_input_fourth]
        contacts = []  # type: List[str]

        for contact_input in contact_inputs:
            if contact_input.isVisible():
                contacts.append(contact_input.currentText().replace(' ', '_'))

        return tuple(contacts)

    def __get_path(self):
        return self._file_name_display.text()

    def __finished(self, data_dict):
        # Save plots:
        for axis_label_pair in list(data_dict.keys()):
            if axis_label_pair in self._plot_windows.keys():
                plot_window = self._plot_windows[axis_label_pair]  # type: PlotWindow
                plot_path = data_dict[axis_label_pair]  # type: str
                plot_window.save_plot(plot_path)

        self._show_status('Measurement finished.')
        self._set_ui_state(True)

    def __new_data(self, data_dict):
        self.__df = self.__df.append(data_dict, ignore_index=True)
        self._tb_window.update_data(self.__df)

        for pair, window in self._plot_windows.items():
            window.update_data(self.__df[list(pair)])

    def __measurement_aborted(self):
        self._show_status('Measurement aborted.')

    @QtCore.pyqtSlot()
    def __increment_contact_number(self):
        """Switch to the next contact pair in the list."""
        for contact in [self._contact_input_first, self._contact_input_second]:
            index = contact.currentIndex()  # type: int
            index = self.CONTACT_NUMBERS.wrap_around_index(index + 1)
            contact.setCurrentIndex(index)

    def __started(self):
        self._show_status('Measurement running ...')

    def __update_config(self):
        print('updating config')
        if 'general' in self._config:
            self._config['general']['last_folder'] = self._directory_name
            print(self._config['general']['last_folder'])
            
        with open('settings.cfg', 'w') as file_handle:
            self._config.write(file_handle)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    m = Main()
    m.show()
    sys.exit(app.exec_())
