from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QPushButton, QFileDialog, QLabel
from PyQt5.QtGui import QStandardItem
from PyQt5.QtCore import QModelIndex, pyqtSignal

from typing import List
import json

class SampleItem(QStandardItem):
    def __init__(self, name:str, contacts: List[str]):
        super().__init__()
        self._contacts = contacts 
        self._name = name
        self.setText(self._name)

    @property
    def item(self):
        return self._contacts.copy()

    @property 
    def name(self):
        return self._name

    def __str__(self):
        contacts_string = '-'.join(self._contacts)
        return '{:s} {:s}'.format(self._name, contacts_string)


class SampleConfig(QWidget):

    sample_selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        central_layout = QVBoxLayout()
        self.setLayout(central_layout)

        search_layout = QHBoxLayout()

        central_layout.addLayout(search_layout)

        search_button = QPushButton('...')

        self._file_path_label = QLabel('Sample Config File')

        search_layout.addWidget(self._file_path_label)
        search_layout.addStretch()
        search_layout.addWidget(search_button)

        search_button.clicked.connect(self._load)

        self._sample_selection = QComboBox()
        self._sample_selection.currentIndexChanged.connect(self._selection_changed)

        central_layout.addWidget(self._sample_selection)

        self._configuration = dict(samples = [], comment='', date='', experiment='')

        self._init_samples()

    def _selection_changed(self):
        samples = self._configuration['samples']
        selected_text = self._sample_selection.currentText()

        if selected_text in samples:
            sample = samples[selected_text]
            self.sample_selection_changed.emit(sample)

    def _init_samples(self, samples = {}):
        self._sample_selection.clear()
        method_model = self._sample_selection.model()
        default_method = QStandardItem("-- Select a Sample --")
        default_method.setEnabled(False)
        method_model.appendRow(default_method)

        for name, contacts in samples.items():
            method_model.appendRow(SampleItem(name, contacts))

    def _load(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Samples Configuration", filter="Configuration (*.json)")
        if file_path != '':
            with open(file_path, 'r', encoding='utf-8') as fil:
                self._configuration = json.load(fil)

            self._init_samples(self._configuration['samples'])        

