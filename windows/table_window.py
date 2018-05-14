from PyQt5 import QtWidgets
from PyQt5.QtWidges import QMdiSubWindow, QTableWidget


class TableWindow(QMdiSubWindow):
    """This is a simple sub window to show a table of data
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.__table = QTableWidget()

        self.setCentralWidget(self.__table)

