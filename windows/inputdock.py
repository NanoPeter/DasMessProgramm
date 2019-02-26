from PyQt5.QtWidgets import (
    QDockWidget,
    QVBoxLayout,
    QScrollArea,
    QWidget,
    QComboBox,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QGroupBox,
    QInputDialog,
    QPlainTextEdit,
    QLabel,
    QErrorMessage,
    QSizePolicy,
)
from PyQt5.QtGui import QStandardItem, QFontMetrics
from PyQt5.QtCore import Qt

from .directory_picker import DirectoryPicker
from .sample_widget import ContactsSelector
from .sample_config import SampleConfig
from .dynamic_input import DynamicInputLayout


class InputDock(QDockWidget):
    def __init__(self):
        super().__init__()
        self._methods = {}
        self.setWindowFlags(Qt.WindowTitleHint)

        central_widget = QWidget()
        self._layout = QVBoxLayout()
        central_widget.setLayout(self._layout)
        self.setWidget(central_widget)

        self._general_box = QGroupBox("General")
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        self._general_layout = QVBoxLayout()
        self._general_box.setLayout(self._general_layout)
        self._layout.addWidget(self._general_box)

        self._measurement_box = QGroupBox("Measurement")
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._measurement_box.setSizePolicy(size_policy)
        self._measurement_layout = QVBoxLayout()
        self._measurement_box.setLayout(self._measurement_layout)
        self._layout.addWidget(self._measurement_box)

        self._init_dir_picker()
        self._init_comment()
        self._init_contacts_picker()
        self._init_sample_config()
        self._init_measurement_box()
        self._init_input_area()
        self._init_controls()

    def _init_comment(self):

        self._comment_box = QPlainTextEdit()

        metrics = QFontMetrics(self._comment_box.font())
        row_height = metrics.lineSpacing()
        # four rows
        self._comment_box.setFixedHeight(4 * row_height)

        self._general_layout.addWidget(QLabel("Comment:"))
        self._general_layout.addWidget(self._comment_box)

    def _init_controls(self):
        self._play_string = "\u25b6"
        self._pause_string = "\u23F8"

        button_layout = QHBoxLayout()
        self._measure_button = QPushButton(self._play_string)
        self._measure_button.setDisabled(True)
        font = self._measure_button.font()
        font.setPointSize(20)
        font.setWeight(100)
        self._measure_button.setFont(font)
        self._measure_button.setToolTip("start/pause a measurement")

        self._abort_button = QPushButton("\u2716")
        self._abort_button.setDisabled(True)
        font = self._abort_button.font()
        font.setPointSize(20)
        font.setWeight(100)
        self._abort_button.setFont(font)
        self._abort_button.setToolTip("abort the current measurement")

        self._next_button = QPushButton("\u2192")
        self._next_button.setDisabled(True)
        font = self._next_button.font()
        font.setPointSize(20)
        font.setWeight(100)
        self._next_button.setFont(font)
        self._next_button.setToolTip("next contacts")

        button_layout.addStretch()
        button_layout.addWidget(self._measure_button)
        button_layout.addWidget(self._abort_button)
        button_layout.addWidget(self._next_button)

        self._layout.addLayout(button_layout)

    def _init_dir_picker(self):
        self._dir_picker = DirectoryPicker()
        self._general_layout.addWidget(self._dir_picker)

    def _init_contacts_picker(self):
        self._contacts_picker = ContactsSelector()
        self._general_layout.addWidget(self._contacts_picker)

        self._contacts_picker.save_triggered.connect(self._on_new_group)

    def _on_new_group(self):
        contacts = self._contacts_picker.contacts
        name, okay = QInputDialog.getText(self, "New Group", "Enter Group Name")

        if name != "" and okay:
            result = self._sample_config.add_config(name, contacts)

            if result == False:
                error = QErrorMessage()
                error.showMessage("Name is already in use")

    def _init_sample_config(self):
        self._sample_config = SampleConfig()
        self._general_layout.addWidget(self._sample_config)

    def _init_measurement_box(self):
        self._method_selection_box = QComboBox()

        self._method_selection_box.currentTextChanged.connect(self._method_changed)

        self._method_model = self._method_selection_box.model()

        default_item = QStandardItem("-- Select a method --")
        default_item.setEnabled(False)

        self._method_model.appendRow(default_item)

        self._measurement_layout.addWidget(self._method_selection_box)

    def _init_input_area(self):
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._scroll_layout = QVBoxLayout()
        scroll_widget = QWidget()
        self._scroll_area.setWidget(scroll_widget)
        scroll_widget.setLayout(self._scroll_layout)
        self._layout.addWidget(self._scroll_area)

        self._measurement_layout.addWidget(self._scroll_area)

    def add_method(self, method_name: str, method):
        if not method_name in self._methods:
            dynamic_layout = DynamicInputLayout(method.inputs())
            dynamic_layout.setContentsMargins(0, 0, 0, 0)

            container = QWidget()
            container.hide()
            container.setLayout(dynamic_layout)

            self._scroll_layout.addWidget(container)
            self._methods[method_name] = (container, method)

            self._method_selection_box.addItem(method_name)

    def load_sample_config(self, file_name):
        self._sample_config.load_from_file(file_name)

    def save_sample_config(self, file_name):
        self._sample_config.save_to_file(file_name)

    @property
    def comment(self):
        text = self._comment_box.toPlainText()
        text = text.replace("\n", "\n# ")

        return "# " + text

    @property
    def directory_path(self):
        self._dir_picker.directory

    @property
    def contacts(self):
        self._contacts_picker.contacts

    @property
    def method(self):
        self._method_selection_box.currentText()

    @property
    def inputs(self):
        widget, _ = self._methods[self.method]
        method_layout = widget.layout()
        return method_layout.get_inputs()

    def _method_changed(self):
        selected_method = self._method_selection_box.currentText()
        self._hide_all_methods()
        self._show_method(selected_method)

    def _hide_all_methods(self):
        [widget.hide() for _, (widget, _) in self._methods.items()]

    def _show_method(self, name):
        if name in self._methods:
            widget, method = self._methods[name]
            widget.show()

            self._contacts_picker.set_number_of_contacts(method.number_of_contacts())
