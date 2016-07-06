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

    def __init__(self, db, restraint, check, unknown1, unknown2):
        # type: (str, str, str, str) -> FileMassPlot
        """

        :param restraint: restraint weight name
        :param check: check weight name
        :param unknown1: first unknown's name
        :param unknown2: second unknown's name
        """

        self.fig, self.axs = plt.subplots(nrows=2, ncols=2, sharex=True)
        self.ax1 = self.axs[0,0]
        self.ax2 = self.axs[0,1]
        self.ax3 = self.axs[1,0]
        self.ax4 = self.axs[1,1]

        FigureCanvasQTAgg.__init__(self, self.fig)

        self.ax1.margins(0.05)
        self.ax1.set_title('Restraint: %s' % restraint)
        self.ax1.set_ylabel("Correction", fontsize=12)
        self.ax1.tick_params(labelbottom='off')

        self.ax2.margins(0.05)
        self.ax2.set_title('Check: %s' % check)
        self.ax2.set_ylabel("Correction", fontsize=12)
        self.ax2.xaxis.set_tick_params(labelbottom='off')

        self.ax3.margins(0.05)
        self.ax3.set_title('Unknown: %s' % unknown1)
        self.ax3.set_ylabel("Correction", fontsize=12)
        self.ax3.xaxis.set_major_locator(LinearLocator(numticks=5))
        self.ax3.set_xlabel("Timestamp", fontsize=12)
        self.ax3.xaxis.set_tick_params(labelbottom='off')

        self.ax4.margins(0.05)
        self.ax4.set_title('Unknown: %s' % unknown2)
        self.ax4.set_ylabel("Correction", fontsize=12)
        self.ax4.xaxis.set_major_locator(LinearLocator(numticks=5))
        self.ax4.set_xlabel("Timestamp", fontsize=12)
        self.ax4.xaxis.set_tick_params(labelbottom='off')

        self.extract_data(db, restraint, check, unknown1, unknown2)

    def extract_data(self, db, restraint, check, unknown1, unknown2):
        # gets the correction, typeA, typeB for each weight.
        # overall uncertainty is 2* sqrt(typeA^2 + typeB^2)
        r_correction, r_a, r_b, c_correction, c_a, c_b, u1_correction, u1_a, u1_b, u2_correction, u2_a, u2_b = \
            [], [], [], [], [], [], [], [], [], [], [], []

        r = db.get_int_weight_corrections_uncertainty(restraint)
        c = db.get_int_weight_corrections_uncertainty(check)
        u1 = db.get_ext_weight_corrections_uncertainty(unknown1)
        u2 = db.get_ext_weight_corrections_uncertainty(unknown2)

        for i in r:
            r_correction.append(i[0])  # first element will be the corrections
            r_a.append(i[1])  # typeA will be the second element
            r_b.append(i[2])  # typeB will be the third element

        for i in c:
            c_correction.append(i[0])  # first element will be the corrections
            c_a.append(i[1])  # typeA will be the second element
            c_b.append(i[2])  # typeB will be the third element

        for i in u1:
            u1_correction.append(i[0])  # first element will be the corrections
            u1_a.append(i[1])  # typeA will be the second element
            u1_b.append(i[2])  # typeB will be the third element

        for i in u2:
            u2_correction.append(i[0])  # first element will be the corrections
            u2_a.append(i[1])  # typeA will be the second element
            u2_b.append(i[2])  # typeB will be the third element

        r_uncertainty = [float(2*(i[0]**2 + i[1]**2)**0.5) for i in zip(r_a, r_b)]
        c_uncertainty = [float(2*(i[0]**2 + i[1]**2)**0.5) for i in zip(c_a, c_b)]
        u1_uncertainty = [float(2*(i[0]**2 + i[1]**2)**0.5) for i in zip(u1_a, u1_b)]
        u2_uncertainty = [float(2*(i[0]**2 + i[1]**2)**0.5) for i in zip(u2_a, u2_b)]

        self.ax1.errorbar(range(len(r_correction)), [float(i) for i in r_correction], yerr=r_uncertainty)
        self.ax2.errorbar(range(len(c_correction)), [float(i) for i in c_correction], yerr=c_uncertainty)
        self.ax3.errorbar(range(len(u1_correction)), [float(i) for i in u1_correction], yerr=u1_uncertainty)
        self.ax4.errorbar(range(len(u2_correction)), [float(i) for i in u2_correction], yerr=u2_uncertainty)

        self.draw()
