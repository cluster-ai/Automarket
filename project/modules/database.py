
#standard libraries
import json
import os

import pandas as pd
import numpy as np

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

class Database():
	#filepaths to different portions of database file structure
	historical_base_path = 'database/historical_data/'
	historical_index_path = (historical_base_path 
							 + 'historical_index.json')
	training_base_path = 'database/training_data/'
	training_index_path = (training_base_path
						   + 'training_index.json')
	settings_path = 'database/settings.json'

	#dict variables that track/index data in database
	historical_index = {}
	training_index = {}

	#used by the other modules to store program wide information
	settings = {}


	def __init__(self):
		#loads handbook and settings file to Database
		self.load_files()


	def load_files(self):
		###SETTINGS###
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.settings_path) == False:
			open(Database.settings_path, 'w')
		else:
			print('Loading Settings: ' + Database.settings_path)
			#loads contents of file with path, "Database.setting_path"
			with open(Database.settings_path) as file:
				Database.settings = json.load(file)

		###TRAINING_INDEX###
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.training_index_path) == False:
			open(Database.training_index_path, 'w')
		else:
			print('Loading Training Index: '
				  + Database.training_index_path)
			#loads indexes for training index
			with open(Database.training_index_path) as file:
				Database.training_index = json.load(file)

		###HISTORICAL_INDEX###
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.historical_index_path) == False:
			open(Database.historical_index_path, 'w')
		else:
			print('Loading Historical Index: '
				  + Database.historical_index_path)
			#loads indexes for historical index
			with open(Database.historical_index_path) as file:
				Database.historical_index = json.load(file)


	def save_files(self):
		###SETTINGS###
		#Checks to see if path exists, if not it creates one
		if os.path.exists(Database.settings_path) == False:
			open(Database.settings_path, 'w')
		#saves settings dict class variable to file by default
		#can change settings parameter to custom settings dict
		with open(Database.settings_path, 'w') as file:
			json.dump(Database.settings, file, indent=4)

		###TRAINING_INDEX###
		#Checks to see if path exists, if not it creates one
		if os.path.exists(Database.training_index_path) == False:
			open(Database.training_index_path, 'w')
		#saves training_index dict class variable to file
		with open(Database.training_index_path, 'w') as file:
			json.dump(Database.training_index, file, indent=4)

		###HISTORICAL_INDEX###
		#Checks to see if path exists, if not it creates one
		if os.path.exists(Database.historical_index_path) == False:
			open(Database.historical_index_path, 'w')
		#saves historical_index dict class variable to file
		with open(Database.historical_index_path, 'w') as file:
			json.dump(Database.historical_index, file, indent=4)


	def reset_settings(self):
		#all settings set to a default value
		Database.settings = {
			'tracked_exchanges': []
		}

		#tracked exchanges includes ones already in use (have data from)
		#looks through historical_index and adds each exchange found
		exchanges = []
		for index_id, item_index in Database.historical_index.items():
			if item_index['exchange_id'] not in exchanges:
				exchanges.append(item_index['exchange_id'])
		#adds all exchanges found to tracked_exchanges in settings
		Database.settings['tracked_exchanges'] = exchanges

		print('NOTICE: reset database settings to their default')

		#saves new settings to file
		self.save_files()


	def index_id(self, exchange_id, coin_id, time_increment):
		'''
		Parameters:
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
		'''
		return f'{exchange_id}_{coin_id}_{time_increment}'


	def add_historical_item(self, exchange_id, coin_id, time_increment):
		'''
		Parameters:
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
		'''
		self.historical_index_keys = ['filepath',
									  'symbol_id',
									  'exchange_id',
									  'asset_id_base',
									  'time_increment',
									  'datapoints',
									  'data_start',
									  'data_end']


	def historical_data(self, index_id, interval=None):
		'''
		Parameters:
			index_id : (str) 
					   - key to select desired historical_index item
			interval : ([int, int]) None returns all available data
					   - converted to nearest time_period_start value
					   - [0] is unix time start, [1] is unix time end
		'''

		#loads index item of historical_index pointed to by index_id
		item_index = Database.historical_index[index_id]

