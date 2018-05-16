from PyQt5.QtWidgets import QMdiSubWindow, QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant


class PandasTableDataModel(QAbstractTableModel):
    """This helps to display pandas DataFrames in a TableView"""
    def __init__(self, data):
        """Makes a pandas DataFrame readable to a Qt TableView
        :param data: the pandas DataFrame you want to show
        """
        super().__init__()
        self.__data = data

    def rowCount(self, parent=None, *args, **kwargs):
        """returns the row count of the DataFrame
        :param parent:
        :param args:
        :param kwargs:
        :return: row count
        """
        return len(self.__data)

    def columnCount(self, parent=None, *args, **kwargs):
        """returns the column count of the DataFrame
        :param parent:
        :param args:
        :param kwargs:
        :return: column count
        """
        return self.__data.columns.size

    def data(self, index, role=Qt.DisplayRole):
        """return a value of the DataFrame at a certain index
        :param index: the index where the data should be
        :param role: some Qt specific stuff
        :return: value in DataFrame
        """
        if index.isValid():
            if role == Qt.DisplayRole:
                value = self.__data.values[index.row()][index.column()]
                return QVariant(str(value))
        return QVariant()

    def headerData(self, index, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """returns column and row header labels
        :param index: index of desired label
        :param orientation: Qt.Horizontal for column names, Qt.Vertical for row names
        :param role: Qt specific stuff
        :return: column or row name
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(str(self.__data.columns[index]))
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(index))
        return QVariant()


class TableWindow(QMdiSubWindow):
    """This is a simple sub window to show a table of data
    """
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        self.__table = QTableView()

        self.setWidget(self.__table)
        self.setWindowTitle('Table')

    def update_data(self, data):
        """
        Updates the table view with new data
        :param data: A Pandas DataFrame with the containing Data
        :return:
        """
        model = PandasTableDataModel(data)
        self.__table.setModel(model)
        self.__table.scrollToBottom()

    @property
    def selected_columns(self):
        return 0

