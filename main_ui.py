import measurement
from windows.table_window import TableWindow
from windows.dynamic_input import DynamicInputLayout

from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui
from typing import Type


class MainUI(QtWidgets.QMainWindow):
    """Class that generates the layout for the main application window."""

    def __init__(self):
        super().__init__()

    def _init_gui(self):
        self.setWindowTitle(self.TITLE)

        central_layout = QtWidgets.QHBoxLayout()
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(central_layout)

        self._inputs_layout = QtWidgets.QVBoxLayout()
        self._inputs_layout.setSpacing(10)
        central_layout.addLayout(self._inputs_layout)

        file_name_layout = QtWidgets.QVBoxLayout()
        self._inputs_layout.addLayout(file_name_layout)
        file_name_layout.setSpacing(5)
        file_name_layout.addWidget(QtWidgets.QLabel("Save directory:"))
        self._file_name_display = QtWidgets.QLineEdit()
        self._file_name_display.setFixedWidth(self.SIDE_BAR_WIDTH)  # Also sets left panel width
        file_name_layout.addWidget(self._file_name_display)
        self._file_name_display.setReadOnly(True)
        self._file_name_display.textChanged.connect(
            lambda text: self._file_name_display.setToolTip(text)
        )
        self._file_name_display.setText(self._directory_name)
        directory_buttons_layout = QtWidgets.QHBoxLayout()
        file_name_layout.addLayout(directory_buttons_layout)
        self._select_directory_button = QtWidgets.QPushButton("Select...")
        directory_buttons_layout.addWidget(self._select_directory_button)
        self._select_directory_button.clicked.connect(self._set_directory_name)
        self._open_directory_button = QtWidgets.QPushButton("Open...")
        directory_buttons_layout.addWidget(self._open_directory_button)
        self._open_directory_button.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromUserInput(self._file_name_display.text())
            )
        )
        
        contacts_layout = QtWidgets.QVBoxLayout()
        self._inputs_layout.addLayout(contacts_layout)
        contacts_layout.setSpacing(3)
        contacts_layout.addWidget(QtWidgets.QLabel("Contacts:"))
        first_contact_pair = QtWidgets.QHBoxLayout()
        contacts_layout.addLayout(first_contact_pair)
        self._contact_input_first = QtWidgets.QComboBox()
        first_contact_pair.addWidget(self._contact_input_first)
        self._contact_input_second = QtWidgets.QComboBox()
        first_contact_pair.addWidget(self._contact_input_second)
        self._sense_contacts_label = QtWidgets.QLabel("4-wire sense contacts:")
        contacts_layout.addWidget(self._sense_contacts_label)
        second_contact_pair = QtWidgets.QHBoxLayout()
        contacts_layout.addLayout(second_contact_pair)
        self._contact_input_third = QtWidgets.QComboBox()
        second_contact_pair.addWidget(self._contact_input_third)
        self._contact_input_fourth = QtWidgets.QComboBox()
        second_contact_pair.addWidget(self._contact_input_fourth)
        for contact in self.CONTACT_NUMBERS:
            self._contact_input_first.addItem(contact)
            self._contact_input_second.addItem(contact)
            self._contact_input_third.addItem(contact)
            self._contact_input_fourth.addItem(contact)
        self._contact_input_first.setCurrentIndex(0)
        self._contact_input_first.setFixedWidth(80)
        self._contact_input_second.setCurrentIndex(1)
        self._contact_input_second.setFixedWidth(80)
        self._contact_input_third.setCurrentIndex(2)
        self._contact_input_third.setFixedWidth(80)
        self._contact_input_fourth.setCurrentIndex(3)
        self._contact_input_fourth.setFixedWidth(80)

        method_layout = QtWidgets.QVBoxLayout()
        method_layout.setSpacing(3)
        self._inputs_layout.addLayout(method_layout)
        method_layout.addWidget(QtWidgets.QLabel("Measurement method:"))
        self._method_selection_box = QtWidgets.QComboBox()
        self._method_selection_box.setFixedWidth(self.SIDE_BAR_WIDTH)
        method_layout.addWidget(self._method_selection_box)

        # Add a non-user-selectable default item:
        method_model = self._method_selection_box.model()  # type: QtGui.QStandardItemModel
        default_method = QtGui.QStandardItem("-- Select a method --")
        default_method.setEnabled(False)
        method_model.appendRow(default_method)

        available_methods = list(measurement.REGISTRY.keys())  # type: List[str]
        available_methods.sort()
        for method in available_methods:
            self._method_selection_box.addItem(method)

        self._dynamic_inputs_area = QtWidgets.QScrollArea()
        # Initialise and hold all dynamic inputs in memory:
        self._dynamic_inputs = dict()  # type: Dict[Type, QtWidgets.QWidget]
        self.__create_input_ui()
        
        self._dynamic_inputs_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._dynamic_inputs_area.setFixedWidth(self.SIDE_BAR_WIDTH)
        self._dynamic_inputs_area.setWidgetResizable(True)
        self._inputs_layout.addWidget(self._dynamic_inputs_area)
        self._dynamic_inputs_layout = None  # Initialised later

        right_side_layout = QtWidgets.QVBoxLayout()
        central_layout.addLayout(right_side_layout)
        self._mdi = QtWidgets.QMdiArea()
        right_side_layout.addWidget(self._mdi)
        self._mdi.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._mdi.customContextMenuRequested.connect(self.__mdi_context_menu)

        button_layout = QtWidgets.QHBoxLayout()
        right_side_layout.addLayout(button_layout)
        button_layout.addStretch()
        
        self._measure_button = QtWidgets.QPushButton("Measure")
        button_layout.addWidget(self._measure_button)
        self._measure_button.setFixedWidth(100)
        self._measure_button.setEnabled(False)  # Buttons disabled while no method is selected

        self._abort_button = QtWidgets.QPushButton("Abort")
        button_layout.addWidget(self._abort_button)
        self._abort_button.setFixedWidth(100)
        self._abort_button.setEnabled(False)

        self._next_button = QtWidgets.QPushButton("Next")
        button_layout.addWidget(self._next_button)
        self._next_button.setFixedWidth(100)
        self._next_button.setEnabled(False)

        self.__statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.__statusbar)

        self.setCentralWidget(central_widget)
        self._tb_window = TableWindow()
        self._mdi.addSubWindow(self._tb_window)

        self._plot_windows = {}

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
        arrange_windows_action.triggered.connect(lambda: tile_subwindows(self._mdi, TableWindow))
        menu.addAction(arrange_windows_action)
        delete_windows_action = QtWidgets.QAction("Delete all plot windows", menu)
        delete_windows_action.triggered.connect(lambda: close_subwindows(self._mdi, TableWindow))
        menu.addAction(delete_windows_action)

        menu.exec(self._mdi.mapToGlobal(point))

    def _set_ui_state(self, enable: bool):
        self._method_selection_box.setEnabled(enable)
        self._abort_button.setEnabled(not enable)
        self._measure_button.setEnabled(enable)
        self._next_button.setEnabled(enable)
        self._dynamic_inputs_layout.setEnabled(enable)
        self._select_directory_button.setEnabled(enable)
        self._open_directory_button.setEnabled(enable)
        self._contact_input_first.setEnabled(enable)
        self._contact_input_second.setEnabled(enable)
        self._contact_input_third.setEnabled(enable)
        self._contact_input_fourth.setEnabled(enable)

    def _set_input_ui(self, measurement_method: measurement.measurement.AbstractMeasurement):
        """Show the dynamic inputs for a measurement method."""
        for method, container in self._dynamic_inputs.items():
            if method is measurement_method:
                container.show()
                self._dynamic_inputs_layout = container.layout()
            else:
                container.hide()

    def _show_status(self, message):
        self.__statusbar.showMessage('{} - {}'.format(datetime.now().isoformat(), message))

    def __create_input_ui(self):
        """Create inputs for all measurement methods and keep them hidden.

        They can be selectively shown using '__set_input_ui()'.
        """
        # Create all input containers:
        for method in measurement.REGISTRY.values():
            container = QtWidgets.QWidget()
            container.setLayout(DynamicInputLayout(method.inputs()))

            self._dynamic_inputs[method] = container

        # Add them all to the dynamic input area and hide everything:
        parent_container = QtWidgets.QWidget()
        parent_layout = QtWidgets.QHBoxLayout()
        parent_layout.setContentsMargins(0, 0, 0, 0)
        parent_container.setLayout(parent_layout)
        for container in self._dynamic_inputs.values():
            parent_layout.addWidget(container)
            container.hide()

        self._dynamic_inputs_area.setWidget(parent_container)

    @QtCore.pyqtSlot()
    def _set_directory_name(self):
        """Open a dialogue to change the output directory."""
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Measurement Directory',
                                                              self._directory_name)

        if dir_name != '':
            self._directory_name = dir_name
            self.__file_name_display.setText(self._directory_name)
            self._update_config()