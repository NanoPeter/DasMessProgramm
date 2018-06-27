import measurement
from windows.table_window import TableWindow
from windows.dynamic_input import DynamicInputLayout

from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui
from typing import Type

from windows.contacts_picker import ContactsPicker
from windows.directory_picker import DirectoryPicker


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

        self._dir_picker = DirectoryPicker()
        self._inputs_layout.addWidget(self._dir_picker)
        self._dir_picker.directory_changed.connect(self._set_directory_name)

        self._contacts_picker = ContactsPicker()
        self._inputs_layout.addWidget(self._contacts_picker)

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

    @QtCore.pyqtSlot(str)
    def _set_directory_name(self, dir_name):
        self._directory_name = dir_name
        self._update_config()

    def _update_config(self):
        pass
