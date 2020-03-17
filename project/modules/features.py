
#standard libraries
import datetime
import time

#third-party packages
import pandas as pd
import numpy as np

#local modules

'''
Module - features.py

Last Refactor: Alpha-v1.0


CONTENTS:

class Feature():

'''


#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################


class Feature():

	#dict of every feature function and its constraints
	#can be thought of as a feature function data_index
	functions = {
		'smooth': {
			'kwargs': {
				'width': ['positive integer']
			},
			'output_type': 'numerical'
		},
		'delta': {
			'kwargs': {},
			'output_type': 'numerical'
		}
		'time_series': {
			'kwargs': {},
			'output_type': 'categorical'
		}
	}


	def __init__(self, index_id):
		self.index_id = index_id
		self.layers = []


	def add_layer(self, function, **kwargs):
		'''
		Adds a feature layer to the object

		Parameters:
			function : (str) name of the computation for layer
			**kwargs : (**kwargs) parameter settings for function
		'''

		#makes sure function exists
		if function not in Feature.functions:
			#given function not found
			raise KeyError(f'"{function}" not found in Feature.functions')

		#loads feature funtion information
		func_index = Feature.functions[function]

		#makes sure there are no extraneous kwargs
		for kwarg in kwargs:
			if kwarg not in func_index['kwargs']:
				raise KeyError(f'unknown kwarg, "{kwarg}"" given')

		#creates layer with necessary information
		layer = {
			'function': function,
			'kwargs': kwargs,
			'outputs': ''
		}


	def smooth(self, width): #numerical
		'''
		This data iterates through DataFrame and averages each
		value with "width" values on either side

		Parameters:
			historical     : (pd.DataFrame()) data from one exchange
											  for one coin
			time_increment : (int) time_series increment of data in seconds
			width          : (positive int) number of points on each side
											of value used in smoothing algo

		Creates the following features
			/price/
			- price_average
			- price_low
			- price_high
			/other/
			- volume_traded
			- trades_count

		Uses following historical data
			- price_average
			- price_low
			- price_high
			- volume_traded
			- trades_count

		Assumptions:
			- historical.index values are incrementing evenly and continuously
			- historical.index values are increment by "time_increment" seconds
			- historical.isnan values are 0 if False and 1 if True
		'''

		#sets 'time_period_start' as the index of historical
		historical.set_index('time_period_start', drop=False, inplace=True)

		#creates a complete copy for the new data to be saved
		#this prevents changed values from influencing the algorithm
		data = historical.copy()

		#max and min indexes of historical data
		max_hist_index = historical.index.max()
		min_hist_index = historical.index.min()

		#iterates through historical and converts data values
		count = 0
		prev_time = time.time()#tracks duration
		for index, row in historical.iterrows():

			max_index = index + time_increment*width
			min_index = index - time_increment*width

			#if max or min indexes are outside of dataframe index,
			#it sets it to the next closest one
			if max_index >= max_hist_index:
				max_index = max_hist_index
			if min_index <= min_hist_index:
				min_index = min_hist_index

			#columns being smoothed
			columns = ['price_high']

			#array of values that will be used for average
			#in order of index
			vals = historical.loc[min_index:max_index, columns]

			#starts index count at zero for row 1 but
			#still incrementing by time_increment
			vals.index = vals.index - vals.index.min()

			#centers actual value at index 0
			#also sets index increment to 1
			vals.index = ((vals.index - width*time_increment)
						  / time_increment)

			#calculates the multiplier and adds it as a col
			vals['multiplier'] = vals.index
			vals['multiplier'] = width - abs(vals.loc[:, 'multiplier']) + 1

			print('\n', vals)

			#drop empty values
			vals.dropna(inplace=True)

			for col in columns:
				#average the vals
				average = (np.sum(vals[col]*vals['multiplier']) 
						   / np.sum(vals['multiplier']))

				#apply new average value
				data.at[index, col] = average

			if count % 10000 == 0:
				current_time = time.time()
				duration = current_time - prev_time
				prev_time = current_time
				print(f"Count: {count} | Duration: {duration}")

			count += 1

		return data


def create_feature(columns, func, id):
	'''
	Creates a custom feature with a single feature func.
	The user can request multiple columns be returned
	but it will be packaged as individual features with
	the same user given id extension.

	Parameters:

	'''
	pass


def update_feature(historical, feature_id):
	pass


def generate_data(historical, feature_id):
	'''
	Generates feature data
	'''
	pass