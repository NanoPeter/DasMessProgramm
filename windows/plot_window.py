from PyQt5.QtWidgets import QMdiSubWindow, QSizePolicy, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

#matplotlib related pyqt5 stuff
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from pandas import DataFrame
from typing import List, Tuple

from measurement.measurement import PlotRecommendation


class PlotWidget(FigureCanvas):
    def __init__(self, recommendation, parent=None, width: int = 5,
                 height: int = 4, dpi: int = 72,
                 x_axis_label: str = '', y_axis_label: str = '',
                 title_suffix: str = "") -> None:
        self._figure = Figure(figsize=(width, height), dpi=dpi)
        self._axes = self._figure.add_subplot(111)

        self._recommendation = recommendation
        self._x_axis_label = x_axis_label
        self._y_axis_label = y_axis_label
        self._title_suffix = title_suffix

        super().__init__(self._figure)
        self.setParent(parent)

        super().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        super().updateGeometry()

    def update_figure(self, x_data: List[float], y_data: List[float]) -> None:
        self._axes.cla()
        self._axes.set_title("{} {}".format(self._recommendation.title, self._title_suffix))
        self._axes.set_xlabel(self._x_axis_label)
        self._axes.set_ylabel(self._y_axis_label)
        self.add_figure(x_data, y_data)

    def add_figure(self, x_data: List[float], y_data: List[float], style='x') -> None:
        self._axes.plot(x_data, y_data, style)
        self.draw()

    def add_text(self, text: str, x: float = 0.2, y: float = 0.9) -> None:
        self._axes.text(x, y, text, horizontalalignment='center',
                        verticalalignment='center', transform=self._axes.transAxes)
        self.draw()

    def save_figure(self, plot_path: str) -> None:
        """Save plot to 'plot_path' as PDF."""
        self._figure.savefig(plot_path)


class PlotWindow(QMdiSubWindow):
    """This is a simple sub window to show a plot of data
    """
    def __init__(self, plot_recommendation: PlotRecommendation, plot_title_suffix: str,
                 x_axis_label: str, y_axis_label: str) -> None:
        super().__init__()

        self._recommendation = plot_recommendation
        self.resize(512, 512)

        self.setWindowTitle("{} {}".format(plot_recommendation.title,
                                           plot_title_suffix))

        main_widget = QWidget()
        self.setWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self._plot_widget = PlotWidget(
            plot_recommendation,
            x_axis_label=x_axis_label, y_axis_label=y_axis_label,
            title_suffix=plot_title_suffix
        )

        main_layout.addWidget(NavigationToolbar(self._plot_widget, self))
        main_layout.addWidget(self._plot_widget)

        window_icon_pixmap = QPixmap(1, 1)
        window_icon_pixmap.fill(Qt.transparent)
        self.setWindowIcon(QIcon(window_icon_pixmap))

    def update_data(self, data: DataFrame) -> None:
        """
        Updates the plot view with new data :)
        :param data: A Pandas DataFrame with the containing data
        :return:
        """
        if data.columns.size > 1:
            x_data = list(data.ix[:, 0])
            y_data = list(data.ix[:, 1])
            self._plot_widget.update_figure(x_data, y_data)
            if self._recommendation.show_fit:
                param_dict, fit_data = self._recommendation.fit(x_data, y_data)
                show_text_lines = []
                for param, value in param_dict.items():
                    show_text_lines.append('{} = {:0.3e}'.format(param, value))

                show_text = '\n'.join(show_text_lines)

                self._plot_widget.add_figure(fit_data[:, 0], fit_data[:, 1], '-')
                self._plot_widget.add_text(show_text)

    def save_plot(self, file_path: str) -> None:
        """Save this plot to file as PDF."""
        self._plot_widget.save_figure(file_path)
        
