
#standard libraries
from itertools import count

#third-party packages
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#local modules

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
The "Graph" class will be used as a continuously updating 
representation of data. The built in features of this class
will be for data stored in the database, any other data must 
be loaded into it via argument.

For version 1 (if time permits), this module would benefit from
being nested in a UI allowing the user to change graph data/options
without having to reopen it manually. (use kivy UI framework)
'''

from define import *
import numpy as np
import modules.preproc as preproc


class Grapher():

	def __init__(self):
		'''
		IMPORTANT:
		Develope this class to utilize the database on
		its own.
		'''
		self.datapoints = 100 #datapoints
		self.data = Database.historical('KRAKEN_BTC_5MIN')
		self.index = 0


	def animate(self, i):
		offset = 300 * self.index
		end_time = 1470159900 - offset
		start_time = end_time - (300 * self.datapoints)
		interval = abs(end_time - start_time)

		self.index += 1

		display_data = self.data.loc[start_time:end_time, 'price_high']

		xticks_count = 4
		#the first value is start_time and the last value is end_time
		xticks = np.multiply(range(xticks_count), 
							 interval / (xticks_count - 1))
		xticks = np.add(xticks, start_time)

		#convert to date
		xticks_labels = []
		for unix in xticks:
			xticks_labels.append(preproc.unix_to_date(unix, decimal=False))

		plt.cla()
		plt.xticks(xticks, xticks_labels, rotation=10)
		plt.plot(display_data)


	def display(self):
		ani = FuncAnimation(plt.gcf(), self.animate, interval=100)
		plt.show()