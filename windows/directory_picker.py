
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QFileDialog

from PyQt5.QtGui import QDesktopServices, QMouseEvent
from PyQt5.QtCore import QUrl, pyqtSignal, Qt


class ClickableLineEdit(QLineEdit):
    right_clicked = pyqtSignal()
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        super().mouseDoubleClickEvent(e)
        self.double_clicked.emit()
        self.deselect()

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.RightButton:
            self.right_clicked.emit()
        super().mouseReleaseEvent(e)
        
    def contextMenuEvent(self, event):
        pass



class DirectoryPicker(QWidget):
    TOOL_TIP = "Double-click to select a directory\n" \
               "Right-click to open current directory"

    directory_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_gui()

    @property
    def directory(self):
        return self._directory_path.text()

    @directory.setter
    def directory(self, path: str):
        self._directory_path.setText(path)

    def _init_gui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        layout.addWidget(QLabel('Select Directory:'))

        self._directory_path = ClickableLineEdit()
        self._directory_path.setReadOnly(True)
        self._directory_path.setToolTip(self.TOOL_TIP)

        layout.addWidget(self._directory_path)

        self._directory_path.double_clicked.connect(self._select_directory)
        self._directory_path.right_clicked.connect(self._open_directory)

    def _open_directory(self):
        QDesktopServices.openUrl(QUrl.fromUserInput(self.directory))

    def _select_directory(self):
        dir_name = QFileDialog.getExistingDirectory(self, 'Open Measurement Directory',
                                                    self.directory)

        if dir_name != '':
            self._directory_path.setText(dir_name)
            self.directory_changed.emit(self.directory)



