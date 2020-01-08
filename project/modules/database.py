
#standard libraries
import json
import os
import time

import pandas as pd
import numpy as np

from .coinapi import Coinapi

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

class Database():
	#filepaths to different portions of database file structure
	base_path = 'database'

	historical_base_path = base_path + '/historical_data'
	historical_index_path = (historical_base_path 
							 + '/historical_index.json')
	training_base_path = base_path + '/training_data'
	training_index_path = (training_base_path
						   + '/training_index.json')
	settings_path = base_path + '/settings.json'
	coin_index_path = base_path + '/coin_index.json'

	#dict variables that track/index data in database
	historical_index = {}
	training_index = {}
	coin_index = {}

	#used by the other modules to store program wide information
	settings = {}


	def __init__(self):
		#loads base paths (directories)
		if os.path.isdir(Database.base_path) == False:
			os.mkdir(Database.base_path)

		if os.path.isdir(Database.historical_base_path) == False:
			os.mkdir(Database.historical_base_path)

		if os.path.isdir(Database.training_base_path) == False:
			os.mkdir(Database.training_base_path)

		#creates instance of coinapi
		self.coinapi = Coinapi()

		#loads handbook and settings file to Database
		self.load_files()


	def load_files(self):
		###SETTINGS###
		print('...')
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.settings_path) == False:
			print(f'File Not Found -> {Database.settings_path}')
			open(Database.settings_path, 'w')

		print('Loading Settings: ' + Database.settings_path)
		#loads contents of file with path, "Database.setting_path"
		with open(Database.settings_path) as file:
			try: 
				Database.settings = json.load(file)
			except ValueError:
				Database.settings = []
				print('NOTICE: file is empty -> '
					  + Database.settings_path)

		###TRAINING_INDEX###
		print('...')
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.training_index_path) == False:
			print(f'File Not Found -> {Database.training_index_path}')
			open(Database.training_index_path, 'w')

		print('Loading Training Index: '
			  + Database.training_index_path)
		#loads indexes for training index
		with open(Database.training_index_path) as file:
			try: 
				Database.training_index = json.load(file)
			except ValueError:
				Database.training_index = []
				print('NOTICE: file is empty -> '
					  + Database.training_index_path)

		###HISTORICAL_INDEX###
		print('...')
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.historical_index_path) == False:
			print(f'File Not Found -> {Database.historical_index_path}')
			open(Database.historical_index_path, 'w')

		print('Loading Historical Index: '
			  + Database.historical_index_path)
		#loads indexes for historical index
		with open(Database.historical_index_path) as file:
			try: 
				Database.historical_index = json.load(file)
			except ValueError:
				Database.historical_index = []
				print('NOTICE: file is empty -> '
					  + Database.historical_index_path)

		###COIN_INDEX###
		print('...')
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.coin_index_path) == False:
			print(f'File Not Found -> {Database.coin_index_path}')
			open(Database.coin_index_path, 'w')

		print('Loading Coin Index: '
			  + Database.coin_index_path)
		#loads indexes for training index
		with open(Database.coin_index_path) as file:
			try: 
				Database.coin_index = json.load(file)
			except ValueError:
				Database.coin_index = []
				print('NOTICE: file is empty -> '
					  + Database.coin_index_path)


	def save_files(self):
		###SETTINGS###
		#Checks to see if path exists, if not it creates one
		if os.path.exists(Database.settings_path) == False:
			open(Database.settings_path, 'x')
		#saves settings dict class variable to file by default
		#can change settings parameter to custom settings dict
		with open(Database.settings_path, 'w') as file:
			json.dump(Database.settings, file, indent=4)

		###TRAINING_INDEX###
		#Checks to see if path exists, if not it creates one
		if os.path.exists(Database.training_index_path) == False:
			open(Database.training_index_path, 'x')
		#saves training_index dict class variable to file
		with open(Database.training_index_path, 'w') as file:
			json.dump(Database.training_index, file, indent=4)

		###HISTORICAL_INDEX###
		#Checks to see if path exists, if not it creates one
		if os.path.exists(Database.historical_index_path) == False:
			open(Database.historical_index_path, 'x')
		#saves historical_index dict class variable to file
		with open(Database.historical_index_path, 'w') as file:
			json.dump(Database.historical_index, file, indent=4)

		###COIN_INDEX###
		#Checks to see if path exists, if not it creates one
		if os.path.exists(Database.coin_index_path) == False:
			open(Database.coin_index_path, 'x')
		#saves coin_index dict class variable to file
		with open(Database.coin_index_path, 'w') as file:
			json.dump(Database.coin_index, file, indent=4)


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

		self.save_files()


	def reset_coin_index(self):
		#reloads the coins for each tracked exchange

		if Database.settings['tracked_exchanges'] == []:
			Database.coin_index = {}
			print('NOTICE: No Tracked Exchanges')
		else:
			filters = {
				'asset_id_quote': Coinapi.asset_id_quote
			}
			#requests all currency data and filters by fiat currency
			response = self.coinapi.request('free_key',
											url=Coinapi.coins_url,
											filters=filters)
			#sets index to empty dict
			Database.coin_index = {}

			print('Resetting Coin Index')

			#iterates through each tracked exchange
			for exchange_id in Database.settings['tracked_exchanges']:
				#filters request and appends relevant data to coin_index
				#for current exchange_id
				filters = {'exchange_id': exchange_id}
				exchange_coins = self.coinapi.filter(response,
													 filters,
													 False)
				#adds data to coin_index and saves to file
				Database.coin_index.update({exchange_id: exchange_coins})

		#saves coin_index to file
		self.save_files()

		print('----------------------------------------------------')


	def index_id(self, exchange_id, coin_id, time_increment):
		'''
		Parameters:
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
		'''
		return f'{exchange_id}_{coin_id}_{time_increment}'


	def add_exchange(self, exchange_id):
		'''
		Parameters:
			exchange_id : (str) Name of exchange in coinapi format
								ex: 'KRAKEN'
		'''

		if exchange_id in Database.settings['tracked_exchanges']:
			#checks if exchange is already in tracked_exchanges
			print(f'NOTICE: {exchange_id} Already Being Tracked')
		elif self.coinapi.verify_exchange(exchange_id):
			#Verifies the given exchange is a valid coinapi exchange_id
			print(f'Adding Exchange: {exchange_id}')
			Database.settings['tracked_exchanges'].append(exchange_id)
			#saves settings
			self.save_files()
			#updates coin_index
			self.reset_coin_index()


	def remove_exchange(self, exchange_id):
		'''
		Parameters:
			exchange_id : (str) Name of exchange in coinapi format
								ex: 'KRAKEN'
		'''
		#has data is used to flag the exchange_id when there is data found
		#in database associated to it
		has_data = False

		#Cannot delete exchange_id when there is data associated with
		#exchange in database
		for index_id, item_index in Database.historical_index.items():
			if exchange_id == item_index['exchange_id']:
				#if exchange_id is found, it cannot be removed
				print(f'NOTICE: {exchange_id} Cannot Be Deleted')
				has_data = True

		if exchange_id not in Database.settings['tracked_exchanges']:
			#checks if exchange is already in tracked_exchanges
			print(f'NOTICE: {exchange_id} Not Being Tracked')
		elif (self.coinapi.verify_exchange(exchange_id) and
				has_data == False):
			#Verifies the given exchange is a valid coinapi exchnage_id
			print(f'Removing Exchange: {exchange_id}')
			#removes exchange_id from settings and saves settings ti file
			Database.settings['tracked_exchanges'].remove(exchange_id)
			self.save_files()
			#resets coin_index with new tracked_exchanges
			self.reset_coin_index()


	def add_historical_item(self, exchange_id, coin_id, time_increment):
		'''
		Parameters:
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
		'''
		index_keys = ['filepath',
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

