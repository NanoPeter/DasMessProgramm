#!/usr/bin/python3

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication

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


class Main(QtWidgets.QMainWindow):

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
        self.__signal_interface.status.connect(self.__show_status)
        self.__signal_interface.started.connect(self.__started)

        if 'general' in self._config:
            if 'last_folder' in self._config['general']:
                self.__directory_name = self._config['general']['last_folder']
            else:
                self.__directory_name = '/tmp'
        else:
            self.__directory_name = '/tmp'

        self._measurement_class = AbstractMeasurement
        self._measurement = None  # type: AbstractMeasurement

        self.__init_gui()

    def __init_gui(self):
        self.setWindowTitle(self.TITLE)

        central_layout = QtWidgets.QHBoxLayout()
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(central_layout)

        self.__inputs_layout = QtWidgets.QVBoxLayout()
        self.__inputs_layout.setSpacing(10)
        central_layout.addLayout(self.__inputs_layout)

        file_name_layout = QtWidgets.QVBoxLayout()
        self.__inputs_layout.addLayout(file_name_layout)
        file_name_layout.setSpacing(5)
        file_name_layout.addWidget(QtWidgets.QLabel("Save directory:"))
        self.__file_name_display = QtWidgets.QLineEdit()
        self.__file_name_display.setFixedWidth(self.SIDE_BAR_WIDTH)  # Also sets left panel width
        file_name_layout.addWidget(self.__file_name_display)
        self.__file_name_display.setReadOnly(True)
        self.__file_name_display.textChanged.connect(
            lambda text: self.__file_name_display.setToolTip(text)
        )
        self.__file_name_display.setText(self.__directory_name)
        directory_buttons_layout = QtWidgets.QHBoxLayout()
        file_name_layout.addLayout(directory_buttons_layout)
        self.__select_directory_button = QtWidgets.QPushButton("Select...")
        directory_buttons_layout.addWidget(self.__select_directory_button)
        self.__select_directory_button.clicked.connect(self.__set_directory_name)
        self.__open_directory_button = QtWidgets.QPushButton("Open...")
        directory_buttons_layout.addWidget(self.__open_directory_button)
        self.__open_directory_button.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromUserInput(self.__file_name_display.text())
            )
        )
        
        contacts_layout = QtWidgets.QVBoxLayout()
        self.__inputs_layout.addLayout(contacts_layout)
        contacts_layout.setSpacing(3)
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

        method_layout = QtWidgets.QVBoxLayout()
        method_layout.setSpacing(3)
        self.__inputs_layout.addLayout(method_layout)
        method_layout.addWidget(QtWidgets.QLabel("Measurement method:"))
        self.__method_selection_box = QtWidgets.QComboBox()
        self.__method_selection_box.setFixedWidth(self.SIDE_BAR_WIDTH)
        method_layout.addWidget(self.__method_selection_box)

        # Add a non-user-selectable default item:
        method_model = self.__method_selection_box.model()  # type: QtGui.QStandardItemModel
        default_method = QtGui.QStandardItem("-- Select a method --")
        default_method.setEnabled(False)
        method_model.appendRow(default_method)

        available_methods = list(measurement.REGISTRY.keys())  # type: List[str]
        available_methods.sort()
        for method in available_methods:
            self.__method_selection_box.addItem(method)
        self.__method_selection_box.currentTextChanged.connect(
            lambda title: self.__measurement_method_selected(title, measurement.REGISTRY[title])
        )
        
        self.__dynamic_inputs_area = QtWidgets.QScrollArea()
        self.__dynamic_inputs_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.__dynamic_inputs_area.setFixedWidth(self.SIDE_BAR_WIDTH)
        self.__dynamic_inputs_area.setWidgetResizable(True)
        self.__inputs_layout.addWidget(self.__dynamic_inputs_area)
        self.__dynamic_inputs_layout = None  # Initialised later

        right_side_layout = QtWidgets.QVBoxLayout()
        central_layout.addLayout(right_side_layout)
        self.__mdi = QtWidgets.QMdiArea()
        right_side_layout.addWidget(self.__mdi)
        self.__mdi.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.__mdi.customContextMenuRequested.connect(self.__mdi_context_menu)

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
        self.__next_button.clicked.connect(self.__increment_contact_number)

        self.__statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.__statusbar)

        self.setCentralWidget(central_widget)
        self.__tb_window = TableWindow()
        self.__mdi.addSubWindow(self.__tb_window)

        self.__plot_windows = {}

    def __measurement_method_selected(self, title, cls: AbstractMeasurement):
        for button in [self.__next_button, self.__abort_button, self.__measure_button]:
            button.setEnabled(True)

        self.setWindowTitle('{} -- {}'.format(self.TITLE, title))
        self.__create_input_ui(cls.inputs())
        self._measurement_class = cls

        if cls.number_of_contacts() == Contacts.FOUR:
            four_wire_visible = True
        else:
            four_wire_visible = False

        self.__sense_contacts_label.setVisible(four_wire_visible)
        self.__contact_input_third.setVisible(four_wire_visible)
        self.__contact_input_fourth.setVisible(four_wire_visible)
        self.__next_button.setVisible(not four_wire_visible)

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

        self._measurement = self._measurement_class(self.__signal_interface,
                                                    path, contacts, **inputs)
                
        self.__df = pd.DataFrame()

        self.__plot_windows = {}

        for recommended_plot in self._measurement.recommended_plots:
            pair = (recommended_plot.x_label, recommended_plot.y_label)
            if pair not in self.__plot_windows:
                outputs = self._measurement_class.outputs()
                x_label = outputs[pair[0]].fullname
                y_label = outputs[pair[1]].fullname
                
                window = PlotWindow(
                    recommended_plot,
                    "| Contacts: '{}' '{}'".format(self.__contact_input_first.currentText(),
                                                   self.__contact_input_second.currentText()),
                    x_axis_label=x_label, y_axis_label=y_label
                )
                self.__plot_windows[pair] = window
                self.__mdi.addSubWindow(window)
                window.show()

        thread = Thread(target=self._measurement)
        thread.start()

        self._set_ui_state(False)

    def _set_ui_state(self, enable: bool):
        self.__method_selection_box.setEnabled(enable)
        self.__abort_button.setEnabled(not enable)
        self.__measure_button.setEnabled(enable)
        self.__next_button.setEnabled(enable)
        self.__dynamic_inputs_layout.setEnabled(enable)
        self.__select_directory_button.setEnabled(enable)
        self.__open_directory_button.setEnabled(enable)
        self.__contact_input_first.setEnabled(enable)
        self.__contact_input_second.setEnabled(enable)
        self.__contact_input_third.setEnabled(enable)
        self.__contact_input_fourth.setEnabled(enable)

    def __abort_measurement(self):
        self._measurement.abort()

    def __get_contacts(self) -> Union[Tuple[str, str],
                                      Tuple[str, str, str, str]]:

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

        self.__show_status('Measurement finished.')
        self._set_ui_state(True)

    def __create_input_ui(self, inputs):
        """Dynamically set left panel user input widgets.

        Arguments:
            inputs: Dict[str, AbstractInput]: A dictionary of inputs as defined in SMU2Probe.inputs
        """
        # Remove old dynamic layout, if any:
        if self.__dynamic_inputs_layout is not None:
            delete_children(self.__dynamic_inputs_layout)
            del self.__dynamic_inputs_layout

        self.__dynamic_inputs_layout = DynamicInputLayout(inputs)

        container_widget = QtWidgets.QWidget()
        container_widget.setLayout(self.__dynamic_inputs_layout)

        old_container = self.__dynamic_inputs_area.widget()
        del old_container
        self.__dynamic_inputs_area.setWidget(container_widget)

    @QtCore.pyqtSlot()
    def __set_directory_name(self):
        """Open a dialogue to change the output directory."""
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Measurement Directory', self.__directory_name)
        
        if dir_name != '':
            self.__directory_name = dir_name
            self.__file_name_display.setText(self.__directory_name)
            self._update_config()

    def __new_data(self, data_dict):
        self.__df = self.__df.append(data_dict, ignore_index=True)
        self.__tb_window.update_data(self.__df)

        for pair, window in self.__plot_windows.items():
            window.update_data(self.__df[list(pair)])

    def __measurement_aborted(self):
        self.__show_status('Measurement aborted.')

    @QtCore.pyqtSlot()
    def __increment_contact_number(self):
        """Switch to the next contact pair in the list."""
        for contact in [self.__contact_input_first, self.__contact_input_second]:
            index = contact.currentIndex()  # type: int
            index = self.CONTACT_NUMBERS.wrap_around_index(index + 1)
            contact.setCurrentIndex(index)
        
    def __show_status(self, message):
        self.__statusbar.showMessage('{} - {}'.format(datetime.now().isoformat(), message))

    def __started(self):
        self.__show_status('Measurement running ...')

    @QtCore.pyqtSlot(QtCore.QPoint)
    def __mdi_context_menu(self, point: QtCore.QPoint):
        """Show a context menu on the MDI widget."""

        def close_subwindows(mdi: QtWidgets.QMdiArea, except_type: Type = type(None)):
            """Close all subwindows of an MDI area, except for objects of 'except_type'."""
            result_button = QtWidgets.QMessageBox.question(
                mdi, "Close ALL plot windows?",
                "Really close ALL plot windows?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes
            )
            if result_button != QtWidgets.QMessageBox.Yes:
                return
            
            for subwindow in mdi.subWindowList():
                if type(subwindow) is not except_type:
                    subwindow.close()

        def tile_subwindows(mdi: QtWidgets.QMdiArea, except_type: Type = type(None)):
            """Tile all subwindows of an MDI area, except for objects of 'except_type'."""
            # Hide windows to keep them from being tiled:
            windows_hidden = list()  # type: List[QtWidgets.QMdiSubWindow]
            for window in mdi.subWindowList():
                if type(window) == except_type:
                    windows_hidden.append(window)
                    window.hide()

            mdi.tileSubWindows()

            # Show hidden windows again:
            for window in windows_hidden:
                window.show()

            # Move all tiled windows above the excluded ones:
            for window in mdi.subWindowList():
                if window not in windows_hidden:
                    mdi.setActiveSubWindow(window)
            
        menu = QtWidgets.QMenu()
        arrange_windows_action = QtWidgets.QAction("Arrange plot windows in tiles", menu)
        arrange_windows_action.triggered.connect(lambda: tile_subwindows(self.__mdi, TableWindow))
        menu.addAction(arrange_windows_action)
        delete_windows_action = QtWidgets.QAction("Delete all plot windows", menu)
        delete_windows_action.triggered.connect(lambda: close_subwindows(self.__mdi, TableWindow))
        menu.addAction(delete_windows_action)

        menu.exec(self.__mdi.mapToGlobal(point))

    def _update_config(self):
        print('updating config')
        if 'general' in self._config:
            self._config['general']['last_folder'] = self.__directory_name
            print(self._config['general']['last_folder'])
            
        with open('settings.cfg', 'w') as file_handle:
            self._config.write(file_handle)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    m = Main()
    m.show()
    sys.exit(app.exec_())
