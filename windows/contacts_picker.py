
from measurement.measurement import Contacts
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QComboBox, QVBoxLayout

from typing import List


class WrapAroundList(list):
    """A standard list with wrap-around indexing.

    Wrap-around indexing only for reading.
    """

    def __init__(self, items):
        super().__init__(items)

    def __getitem__(self, key: int):
        return super().__getitem__(self.wrap_around_index(key))

    def wrap_around_index(self, index: int) -> int:
        """Return the regular index for a wrap-around index."""
        if index >= 0:
            return index % len(self)
        else:
            return len(self) - (-index % len(self))


CONTACT_NUMBERS = WrapAroundList([
    "I-7", "I-8", "I-2", "I-4", "I-3", "I-1",
    "II-1", "II-3", "II-4", "II-2", "II-8", "II-7",
    "III-7", "III-8", "III-2", "III-4", "III-3", "III-1",
    "IV-1", "IV-3", "IV-4", "IV-2", "IV-8", "IV-7"
])


class ContactsPicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._contact_selectors = []

        self._init_ui()

    def _init_ui(self):
        vbox_layout = QVBoxLayout()
        self.setLayout(vbox_layout)

        self._no_contacts_label = QLabel('No Contacts')
        vbox_layout.addWidget(self._no_contacts_label)

        layout = QGridLayout()
        vbox_layout.addLayout(layout)

        for i in range(4):
            combobox = self._create_contact_selector()
            layout.addWidget(combobox, i/2, i%2)
            self._contact_selectors.append(combobox)

    def _create_contact_selector(self):
        combobox = QComboBox()
        combobox.addItems(CONTACT_NUMBERS)
        combobox.setCurrentIndex(len(self._contact_selectors))
        combobox.hide()

        return combobox

    def set_number_of_contacts(self, contacts: Contacts):
        self._hide_all()

        if contacts.value <= 0:
            self._no_contacts_label.show()
            return

        for i in range(contacts.value):
            self._contact_selectors[i].show()

    def _hide_all(self):
        self._no_contacts_label.hide()
        for selector in self._contact_selectors:
            selector.hide()

    def next(self):
        for selector in self._contact_selectors:
            if selector.isVisible():
                index = selector.currentIndex()
                index = CONTACT_NUMBERS.wrap_around_index(index + 1)
                selector.setCurrentIndex(index)

    def previous(self):
        for selector in self._contact_selectors:
            if selector.isVisible():
                index = selector.currentIndex()
                index = CONTACT_NUMBERS.wrap_around_index(index - 1)
                selector.setCurrentIndex(index)

    @property
    def selected(self) -> List[str]:
        result = []
        for selector in self._contact_selectors:
            if selector.isVisible():
                result.append(selector.currentText().replace(' ', '_'))
        return result







