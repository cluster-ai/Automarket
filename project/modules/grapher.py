
#kivy
import kivy
kivy.require('1.11.1') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.label import Label

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
without having to reopen it manually. (use kivy UI framework)

NOTE: Had to download the following for it to work
pip install --upgraade pip wheel setuptools
pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew
pip install kivy.deps.gstreamer
pip install kivy.deps.angle
pip install --upgrade kivy
'''

class Grapher(App):

    def build(self):
        return Label(text='Hello world')

'''
class Grapher():

	def __init__(self):
		''
		IMPORTANT:
		Develope this class to utilize the database directly.
		''
		self.datapoints = 100 #datapoints
		self.raw = Database.historical('KRAKEN_BTC_5MIN')
		self.raw = self.raw.loc[1537761000:1550275800, :]
		self.delta = features.delta(self.raw)
		self.smooth = features.smooth(self.raw, 300, width=10)
		self.index = 0


	def animate(self, i):
		offset = 300 * self.index
		end_time = 1537789800 + offset
		start_time = end_time - (300 * self.datapoints)
		interval = abs(end_time - start_time)

		#self.index += 1

		display_raw = self.raw.loc[start_time:end_time, 'price_high']
		display_smooth = self.smooth.loc[start_time:end_time, 'price_high']
		display_delta = self.delta.loc[start_time:end_time, 'price_high']

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
		plt.plot(display_smooth)


def graph():
	graph = Grapher()

	ani = FuncAnimation(plt.gcf(), graph.animate, interval=100)
	plt.show()
'''