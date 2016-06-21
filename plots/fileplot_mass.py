__author__ = "masslab"

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from matplotlib.ticker import LinearLocator


class FileMassPlot(FigureCanvasQTAgg):
    """
    Creates a control chart of a selected weight. Grabs the weight history data from the database,
    and plots it. In the legend there is essential information, like the standard deviation.
    Formats the matplotlib figure for use in QT
    """

    def __init__(self, text):
        """

        :param text: the text of the output file of a masscode
        """

        self.fig = plt.figure(facecolor='white')
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.fig.add_subplot(112)
        self.ax3 = self.fig.add_subplot(113, sharex=self.ax1)
        self.ax4 = self.fig.add_subplot(114, sharex=self.ax2)

        FigureCanvasQTAgg.__init__(self, self.fig)

        self.ax1.margins(0.05)
        self.ax1.set_title('Weight 1')
        self.ax1.set_ylabel("Measurement", fontsize=12)
        self.ax1.set_xlabel("Timestamp", fontsize=12)
        self.ax1.xaxis.set_major_locator(LinearLocator(numticks=0))
        self.ax1.tick_params(labelbottom='off')

        self.ax2.margins(0.05)
        self.ax2.set_title('Weight 2')
        self.ax2.set_ylabel("Measurement", fontsize=12)
        self.ax2.xaxis.set_major_locator(LinearLocator(numticks=0))
        self.ax2.set_xlabel("Timestamp", fontsize=12)
        self.ax2.xaxis.set_tick_params(labelbottom='off')

        self.ax3.margins(0.05)
        self.ax3.set_title('Weight 3')
        self.ax3.set_ylabel("Measurement", fontsize=12)
        self.ax3.xaxis.set_major_locator(LinearLocator(numticks=5))
        self.ax3.set_xlabel("Timestamp", fontsize=12)
        self.ax3.xaxis.set_tick_params(labelbottom='off')

        self.ax4.margins(0.05)
        self.ax4.set_title('Weight 4')
        self.ax4.set_ylabel("Measurement", fontsize=12)
        self.ax4.xaxis.set_major_locator(LinearLocator(numticks=5))
        self.ax4.set_xlabel("Timestamp", fontsize=12)
        self.ax4.xaxis.set_tick_params(labelbottom='off')

        self.extract_data(text)

    def extract_data(self, text):
        # gets the data from the text
        mass1 = []
        mass2 = []
        mass3 = []
        mass4 = []
        for line_num, line in enumerate(text):
            if '!---------- All Weighing Data ----------!' in line:
                start = line_num



