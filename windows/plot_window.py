from PyQt5.QtWidgets import QMdiSubWindow, QSizePolicy

#matplotlib related pyqt5 stuff
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from pandas import DataFrame


class PlotWidget(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self._figure = Figure(figsize=(width, height), dpi=dpi)
        self._axes = self._figure.add_subplot(111)

        super().__init__(self._figure)
        self.setParent(parent)

        super().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        super().updateGeometry()

    def update_figure(self, x_data, y_data):
        """
        :param x_data:
        :param y_data:
        :return:
        """
        self._axes.cla()
        self._axes.plot(x_data, y_data)
        self.draw()


class PlotWindow(QMdiSubWindow):
    """This is a simple sub window to show a plot of data
    """
    def __init__(self):
        super().__init__()

        self._plot_widget = PlotWidget()
        self.setWidget(self._plot_widget)

    def update_data(self, data: DataFrame):
        """
        Updates the plot view with new data :)
        :param data: A Pandas DataFrame with the containing data
        :return:
        """
        if data.columns.size > 1:
            self._plot_widget.update_figure(list(data.ix[:, 0]), list(data.ix[:, 1]))