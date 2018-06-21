from PyQt5.QtWidgets import QWidget, QComboBox, QPushButton, QAction, QHBoxLayout
from PyQt5.QtGui import QPixmap, QIcon

from base64 import b64decode

from visa import ResourceManager

REFRESH_ICON = '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'


class GPIBPicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._combobox = QComboBox(self)
        layout.addWidget(self._combobox)

        pm = QPixmap()
        pm.loadFromData(b64decode(REFRESH_ICON))
        icon = QIcon(pm)

        button = QPushButton(self)
        button.setIcon(icon)

        button.clicked.connect(self.update_devices)

        layout.addWidget(button)

        self._resources = []

        self.update_devices()

    @property
    def device_address(self):
        return self._combobox.currentText()

    def update_devices(self):
        rm = ResourceManager('@py')

        try:
            self._resources = [ x for x in rm.list_resources() if 'GPIB' in x]
        except:
            self._resources = []

        self._combobox.clear()

        for item in self._resources:
            self._combobox.addItem(item)

        rm.close()

    def select_device(self, address):
        if address in self._resources:
            index = self._resources.index(address)
            self._combobox.setCurrentIndex(index)

    def text(self):
        return self._combobox.currentText()



