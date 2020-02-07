
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


class Grapher():

	def __init__(self):
		self.interval = 100 #datapoints
		self.data = Database.historical('KRAKEN_BTC_5MIN')
		self.index = 0


	def animate(self, i):

		display_width = 300

		end_time = 1470159900 + (300 * self.index)
		start_time = end_time - (300 * display_width) + (300 * self.index)

		self.index += 1

		print(self.index)

		'''start_time = start_time - (300 * self.index)
		end_time = end_time - (300 * self.index)'''

		plt.cla()
		plt.plot(self.data.loc[start_time:end_time, 'price_high'])


	def display(self):
		ani = FuncAnimation(plt.gcf(), self.animate, interval=10)
		plt.show()