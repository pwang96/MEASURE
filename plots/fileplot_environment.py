__author__ = 'masslab'

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import numpy as np
from sub_ui.error_message import ErrorMessage
from matplotlib.ticker import LinearLocator
import matplotlib.dates as m_dates
import re


datetime_fmt = m_dates.DateFormatter('%b %d, %H:%M')


class FileEnvironmentPlot(FigureCanvasQTAgg):
    """ Formats matplotlib figure for environmental data """
    def __init__(self, text):

        self.counter = 0
        self.fig = plt.figure(facecolor='white')
        self.ax1 = self.fig.add_subplot(311)
        self.ax2 = self.fig.add_subplot(312, sharex=self.ax1)
        self.ax3 = self.fig.add_subplot(313, sharex=self.ax1)

        FigureCanvasQTAgg.__init__(self, self.fig)

        self.ax1.margins(0.05)
        self.ax1.set_ylabel(u'Temperature [\N{DEGREE SIGN}C]', fontsize=12)
        self.ax1.xaxis.set_major_locator(LinearLocator(numticks=0))
        self.ax1.tick_params(labelbottom='off')

        self.ax2.margins(0.05)
        self.ax2.set_ylabel(u'Pressure [Pa]', fontsize=12)
        self.ax2.xaxis.set_major_locator(LinearLocator(numticks=0))
        self.ax2.xaxis.set_tick_params(labelbottom='off')

        self.ax3.margins(0.05)
        self.ax3.set_ylabel(u'Humidity [%rh]', fontsize=12)
        self.ax3.xaxis.set_major_locator(LinearLocator(numticks=5))
        self.ax3.xaxis.set_tick_params(labelbottom='off')

        plt.setp(self.ax1.get_yticklabels(), fontsize=10)
        plt.setp(self.ax2.get_yticklabels(), fontsize=10)
        plt.setp(self.ax3.get_yticklabels(), fontsize=10)

        self.extract_data(text)

    def extract_data(self, text):
        # takes the text passed in from main UI and extracts the environmental data
        temp = []  # initialize the environment lists
        press = []
        humid = []

        for line_num, line in enumerate(text):
            if "READ TEMPERATURE PRESSURE HUMIDITY" in line:
                start = line_num
            if "END OF ENVIRONMENT" in line:
                end = line_num
        try:
            for i in range(start+1, end):
                line = text[i]
                regex = r'(\d*\.\d*)'
                matches = re.findall(regex, line)
                try:
                    temp.append(matches[0])
                    press.append(matches[1])
                    humid.append(matches[2])
                except IndexError:
                    continue

            self.draw_data(temp, press, humid)
        except UnboundLocalError:
            ErrorMessage('No Data in this file!')

    def draw_data(self, temperature, pressure, humidity):
        # takes in the data from extract_data and draws it
        self.ax1.plot([i+1 for i, j in enumerate(temperature)], temperature)
        self.ax2.plot([i+1 for i, j in enumerate(pressure)], pressure)
        self.ax3.plot([i+1 for i, j in enumerate(humidity)], humidity)
        self.draw()

