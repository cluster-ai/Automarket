
#standard libraries
import datetime
import time
import os

#third-party packages
import pandas as pd
import numpy as np
import jsonpickle

#local modules
from define import Database, Historical
from modules.old_modules.preproc import date_to_unix, date_to_unix
import define

'''
Module - features.py

Last Refactor: Alpha-v1.0


CONTENTS:

class Features():
	def add_layer():
		#Adds a feature layer to the object


class Feature():
	def add_item(self, exchange_id, coin_id, period_id):
		#Adds features item to Database.features_index

'''


#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################


class Feature(FeatureFunctions):

	def __init__(self, index_id, feature_id):
		'''
		Generates new feature with feature_id based on given name

		Parameters:
			index_id   : (str) name of the data group
			feature_id : (str) user given name of the feature
		'''
		self.index_id = index_id
		self.id = feature_id
		self.layers = []#record of feature function stack
		self.output_type = ''#output type of the top-most layer

		#verifies this feature will not conflict with existing ones
		self.verify()


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


	def verify(self):
		'''
		verifies this feature will not conflict with existing ones
		'''
		#verifies that the given index_id is in features_index
		if self.index_id not in Database.features_index:
			#index_id not found
			raise KeyError(f'"{self.index_id}" not found')

		#verifies that feature_id is not already being used
		feat_index = Database.features_index[self.index_id]
		if self.id in feat_index['features']:
			#feature_id already being used
			raise KeyError(f'"{self.id}" is already being used')


	def process(self, start_time, end_time):
		'''
		Processes database historical data and returns result

		NOTE: this function DOES NOT upload to the database.
		The Features class must facilitate updates to the database
		through this function.

		Parameter:
			start_time : (int) first datapoint in seconds of 
							   historical processing
			end_time   : (int) last datapoint in seconds of 
							   historical processing
		'''
		#loads historical index data
		hist_index = Database.historical_index[self.index_id]
		#loads features index data
		feat_index = Database.features_index[self.index_id]

		#loads start and end times of existing historical data
		hist_start = date_to_unix(hist_index['data_start'])
		hist_end = date_to_unix(hist_index['data_end'])

		#verifies start time is not out of range
		if start_time < hist_start:
			start_time = hist_start
		#verifies end time is not out of range
		if end_time > hist_end:
			end_time = hist_end
		#verifies start time is less than end time
		if start_time >= end_time:
			raise ValueError(f'start time cannot be greater than end time')

		#verifies start and end times are multiples of time_increment
		if start_time % hist_index['time_increment'] != 0:
			raise ValueError(f'"{start_time}" not a valid index')
		if end_time % hist_index['time_increment'] != 0:
			raise ValueError(f'"{end_time}" not a valid index')

		#initializes df with historical data
		df = Database.historical(self.index_id, 
								 start_time, 
								 end_time)

		#iterates through layers and computes features
		for layer in self.layers:
			#loads layer items
			kwargs = layers['kwargs']
			func = layers['function']

			#calls feature function according to layer
			#the "**" converts the dict to kwargs
			df = getattr(self, func)(df, **kwargs)

		return df




class Features():
	
	def __init__():
		pass


	@staticmethod
	def add_item(exchange_id, coin_id, period_id):
		'''
		Adds features item to Database.features_index

		Parameters:
			exchange_id : (str) name of exchange in bold: 'KRAKEN'
			coin_id     : (str) crytpocurrency id: 'BTC'
			period_id   : (str) period supported by coinapi:'5MIN'
		'''
		#verifies that parameters are supported by coinapi
		Historical.verify_exchange(exchange_id)
		Historical.verify_coin(coin_id)
		Historical.verify_period(period_id)

		#generates index_id using define.py index_id function
		index_id = define.index_id(exchange_id, coin_id, period_id)

		#stops function if item already found in features_index
		if index_id in Database.features_index:
			raise RuntimeError(f'"{index_id}" already in historical index')
		elif index_id not in Database.historical_index:
			raise RuntimeError(f'no historical data found for "{index_id}"')
		
		#loads associated historical data
		hist_index = Database.historical_index[index_id]

		#the item directory is the index_id
		base_dir = Database.features_dir + f'/{index_id}'
		if os.path.isdir(base_dir) == False:
 			os.mkdir(base_dir)

		#fills out required information for new 
		#historical index_item
		index_item = {
			'base_dir': base_dir,
			'symbol_id': hist_index['symbol_id'],
			'exchange_id': exchange_id,
			'asset_id_quote': hist_index['asset_id_quote'],
			'asset_id_base': hist_index['asset_id_base'],
			'period_id': period_id,
			'time_increment': hist_index['time_increment'],
			'features': {}
		}

		#updates historical_index
		Database.features_index.update({index_id: index_item})
		#saves changes to file
		Database.save_files()

		print(f'Added {index_id} to Feature Index')


	@staticmethod
	def add_feature(feature):
		'''
		Adds a new custom feature using Feature class

		Parameters:
			index_id : (str) name of Database.features_index item
			feature  : (Feature()) completed feature object
		'''
		#loads features item index
		feat_index = Database.features_index[feature.index_id]

		#verifies given feature will not conflict with existing ones
		feature.verify()

		#generates feature item using jsonpickle
		index_item = {feature.id: jsonpickle.encode(feature)}
		#updates local copy os feature_index
		feat_index['features'].update(index_item)

		#updates Database with changes and saves them
		Database.features_index[feature.index_id] = feat_index
		Database.save_files()


	@staticmethod
	def update(index_id):
		'''
		Updates each feature of a features_index item

		Parameter:
			index_id    : (str) name of item in features_index
		'''
		#loads features item index
		feat_index = Database.features_index[index_id]

		#iterates through each object