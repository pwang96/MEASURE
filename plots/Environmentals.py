__author__ = "masslab"

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


class Environmentals(FigureCanvasQTAgg):
    """

    """

    def __init__(self, cls, enviroType, apparatusName, apparatusID, apparatusSerial):
        """

        :param cls:
        :param enviroType:
        :param apparatusName:
        :param apparatusID:
        """
        if enviroType == "Temperature":
            (date, readout) = cls.db.get_all_temps(apparatusID)
        elif enviroType == "Pressure":
            (date, readout) = cls.db.get_all_press(apparatusID)
        elif enviroType == "Humidity":
            (date, readout) = cls.db.get_all_humid(apparatusID)

        self.measurement = np.empty(len(readout))

        for index, value in enumerate(readout):
            try:
                self.measurement[index] = float(value)
            except ValueError:
                try:
                    self.measurement[index] = self.measurement[index-1]
                except IndexError:
                    self.measurement[index] = 0

        date = np.array(date)

        self.fig = plt.figure(facecolor='white')
        self.ax = self.fig.add_subplot(111)

        self.fig.autofmt_xdate()

        if enviroType == "Temperature":
            self.ax.set_ylabel(u'Temperature [\N{DEGREE SIGN}C]', fontsize=12)
        if enviroType == "Pressure":
            self.ax.set_ylabel(u'Pressure [Pa]', fontsize=12)
        if enviroType == "Humidity":
            self.ax.set_ylabel(u'Humidity [%rh]', fontsize=12)

        self.ax.set_xlabel("Timestamp", fontsize=12)
        self.fig.suptitle("%s, Apparatus: %s, Serial #%s" % (enviroType, apparatusName, apparatusSerial))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
        self.ax.xaxis.set_major_locator(mdates.MonthLocator())

        # self.ax.plot(date, measurement)
        plt.plot_date(date, self.measurement)

        FigureCanvasQTAgg.__init__(self, self.fig)

