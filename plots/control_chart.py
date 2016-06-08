__author__ = "masslab"

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from matplotlib.ticker import LinearLocator


class ControlChart(FigureCanvasQTAgg):
    """
    Creates a control chart of a selected weight. Grabs the weight history data from the database,
    and plots it. In the legend there is essential information, like the standard deviation.
    Formats the matplotlib figure for use in QT
    """

    def __init__(self, cls, weight_name):
        """

        :param cls: mainUI class instance
        :param weight_name: string of the name of the weight
        """
        (weight_date, weight_history) = cls.db.get_weight_history(weight_name)
        weight_history = [float(i) for i in weight_history] # converting from list of strings to list of floats
        self.fig = plt.figure(facecolor='white')
        self.ax = self.fig.add_subplot(111)

        self.ax.set_ylabel("Accepted", fontsize = 12)
        self.ax.set_xlabel("Timestamp", fontsize = 12)
        self.fig.suptitle("Control Chart for Weight: %s" % weight_name)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator())

        std = np.std(weight_history)
        self.fig.text(0, 0, "Standard Deviation: %s micrograms" % str(std))

        plt.errorbar(weight_date, weight_history, yerr=.1, ecolor='g')
        self.fig.autofmt_xdate()

        FigureCanvasQTAgg.__init__(self, self.fig)




