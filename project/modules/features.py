
#standard libraries
import datetime
import time

#third-party packages
import pandas as pd
import numpy as np

#local modules
from define import Database, Historical

'''
Module - features.py

Last Refactor: Alpha-v1.0


CONTENTS:

class Features():

class Feature():

'''


#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################


class Features(Feature):
	
	def __init__():
		pass


	@classmethod
	def add_item(cls, exchange_id, coin_id, time_increment):
		'''
		Adds features item to Database.features_index

		Parameters:
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
		'''
		#verifies that parameters are supported by coinapi
		Historical.verify_exchange(exchange_id)
		Historical.verify_coin(coin_id)
		Historical.verify_increment(period_id)

		#generates index_id using define.py index_id function
		index_id = index_id(exchange_id, coin_id, period_id)

		#stops function if item already found in features_index
		if index_id in Database.features_index:
			print(f'NOTICE: {index_id} already in historical index')
			return None

		#the item directory is the index_id
 		base_dir = Database.features_base_path + f'/{index_id}'
		if os.path.isdir(base_dir) == False:
			os.mkdir(base_dir)

		#fills out required information for new 
		#historical index_item
		index_item = {
			'base_dir': base_dir,
			'symbol_id': coin_data['symbol_id'],
			'exchange_id': exchange_id,
			'asset_id_quote': coin_data['asset_id_quote'],
			'asset_id_base': coin_data['asset_id_base'],
			'period_id': period_id,
			'time_increment': time_increment
		}

		#updates historical_index
		Database.feature_index.update({index_id: index_item})
		#saves changes to file
		Database.save_files()

		print(f'\nAdded {index_id} to Feature Index')
		print(f'Duration:', time.time() - init_time)
		print('----------------------------------------------------')


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
		},
		'time_series': {
			'kwargs': {},
			'output_type': 'categorical'
		}
	}


	def __init__(self, index_id, feature_id=None):
		'''
		Parameters:
			index_id   : (str) name of the data group
			feature_id : (str) name of the feature in the data group

		NOTE: If a feature_id is given, that data will be loaded
		from database. If the feature_id is not given, a new feature
		is initialized.
		'''
		self.index_id = index_id
		self.layers = []#record of feature function stack
		self.output_type = ''#output type of the top-most layer
		'''
		#verifies feature_id
		if feature_id not in Database.features_index[index_id]:
			#feature_id not found
			raise KeyError(
				f'"{feature_id}" not found in {index_id} features')'''


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

		#currently, nothing can be put on top of a categorical layer
		if self.output_type == 'categorical':
			#top-most layer is categorical and cannot be added to
			raise RuntimeError(f'cannot add to a categorical layer')

		#loads feature funtion information
		func_index = Feature.functions[function]

		#makes sure there are no extraneous kwargs
		for kwarg in kwargs:
			if kwarg not in func_index['kwargs']:
				raise KeyError(f'unknown kwarg, "{kwarg}"" given')

		#makes sure every kwarg is given
		for kwarg in func_index['kwargs']:
			if kwarg not in kwargs:
				#missing kwarg in given parameters
				raise KeyError(f'missing kwarg "{kwarg}"')

		#creates layer with necessary information
		layer = {
			'function': function,
			'kwargs': kwargs,
			'output_type': func_index['output_type']
		}

		#appends layer to the function stack (self.layers)
		self.layers.append(layer)

		#self.output_type is the output_type of the top-most layer
		self.output_type = func_index['output_type']


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