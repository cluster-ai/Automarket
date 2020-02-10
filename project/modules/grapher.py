
#PyQt (GUI Framework)
import sys

from PyQt5.QtWidgets import QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import random

#standard libraries
from itertools import count

#third-party packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#local modules
from define import *
import modules.preproc as preproc
import modules.features as features


#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
NOTE: TO CREATE A GRAPH, USE ONLY THE "graph" FUCNTION
	  DO NOT CREATE INSTANCE OF GRAPHER (its unnecessary)

The "Graph" class will be used as a continuously updating 
representation of data. The built in features of this class
will be for data stored in the database, any other data must 
be loaded into it via argument.

For version 1 (if time permits), this module would benefit from
being nested in a UI allowing the user to change graph data/options
without having to reopen it manually. (use PyQt UI framework)
'''

class App(QMainWindow):

	def __init__(self):
		super().__init__()
		self.left = 10
		self.top = 10
		self.title = 'PyQt5 matplotlib example - pythonspot.com'
		self.width = 640
		self.height = 400
		self.initUI()

	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		m = PlotCanvas(self, width=5, height=4)
		m.move(0,0)

		button = QPushButton('PyQt5 button', self)
		button.setToolTip('This s an example button')
		button.move(500,0)
		button.resize(140,100)

		self.show()


class PlotCanvas(FigureCanvas):

	def __init__(self, parent=None, width=5, height=4, dpi=100):
		self.datapoints = 100 #datapoints
		self.raw = Database.historical('KRAKEN_BTC_5MIN')

		fig = Figure(figsize=(width, height), dpi=dpi)
		self.axes = fig.add_subplot(111)

		FigureCanvas.__init__(self, fig)
		self.setParent(parent)

		FigureCanvas.setSizePolicy(self,
			QSizePolicy.Expanding,
			QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

		self.animate(0)


	def animate(self, i):
		end_time = 1537789800
		start_time = end_time - (300 * self.datapoints)

		#self.index += 1
		ax = self.figure.add_subplot(111)

		display_raw = self.raw.loc[start_time:end_time, 'price_high']

		ax.plot(display_raw)
		ax.set_title('PyQt Matplotlib Example')
		self.draw()


'''
class Grapher():

	def __init__(self):
		
		#IMPORTANT:
		#Develope this class to utilize the database directly.
		
		self.datapoints = 100 #datapoints
		self.raw = Database.historical('KRAKEN_BTC_5MIN')
		#self.raw = self.raw.loc[1537761000:1550275800, :]
		#self.delta = features.delta(self.raw)
		#self.smooth = features.smooth(self.raw, 300, width=10)
		self.index = 0


	def animate(self, i):
		offset = 300 * self.index
		end_time = 1537789800 + offset
		start_time = end_time - (300 * self.datapoints)
		interval = abs(end_time - start_time)

		#self.index += 1

		display_raw = self.raw.loc[start_time:end_time, 'price_high']
		#display_smooth = self.smooth.loc[start_time:end_time, 'price_high']
		#display_delta = self.delta.loc[start_time:end_time, 'price_high']

		xticks_count = 4
		#the first value is start_time and the last value is end_time
		xticks = np.multiply(range(xticks_count), 
							 interval / (xticks_count - 1))
		xticks = np.add(xticks, start_time)

		#convert to date
		xticks_labels = []
		for unix in xticks:
			xticks_labels.append(preproc.unix_to_date(unix, show_dec=False))

		plt.cla()
		plt.xticks(xticks, xticks_labels, rotation=10)
		plt.plot(display_raw)
		#plt.plot(display_delta)
		#plt.plot(display_smooth)


def graph():
	graph = Grapher()

	ani = FuncAnimation(plt.gcf(), graph.animate, interval=100)
	plt.show()
'''