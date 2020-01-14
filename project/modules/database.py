
#standard libraries
import json
import os
import time

import pandas as pd
import numpy as np

from .coinapi import Coinapi
from .preproc import unix_to_date, date_to_unix, prep_historical

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
				self.reset_coin_index()
				print('NOTICE: file is empty -> '
					  + Database.coin_index_path)

		print('----------------------------------------------------')


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


	def reset_tracked(self):
		#resets tracked_coins in settings

		###TRACKED COINS###
		#lists all supported coins from tracked exchanges
		init_loop = True
		coins = []
		for exchange_id, item_index in Database.coin_index.items():
			if init_loop == True:
				init_loop = False
				#the first iteration initializes coins with all data
				#from that coin
				for coin_data in item_index:
					coins.append(coin_data['asset_id_base'])
			else:
				#creates a new list of coins in current exchange
				compare_list = []
				for coin_data in item_index:
					compare_list.append(coin_data['asset_id_base'])
				#compare new list to coins and delete coins that
				#are not in both
				for coin_id in coins:
					if coin_id not in compare_list:
						coins.remove(coin_id)
		#update settings
		Database.settings['tracked_coins'] = coins

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
				#creates a dict of exchange_coins where each coin
				#key is its coin_id
				coin_dict = {}
				for coin_data in exchange_coins:
					coin_id = coin_data['asset_id_base']
					coin_dict.update({coin_id: coin_data})

				#adds data to coin_index and saves to file
				Database.coin_index.update({exchange_id: coin_dict})

		#saves coin_index to file
		self.save_files()

		print('----------------------------------------------------')


	def index_id(self, exchange_id, coin_id, 
				 time_increment=None, period_id=None):
		'''
		Parameters:
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
			period_id      : (str) time increment of data in coinapi
								   period_id format
		'''
		#converts time_increment to period_id equivalent
		#uses period_id instead if given
		if time_increment != None:
			#converts time_increment into period_id
			period_id = self.coinapi.period_id(time_increment)
		elif period_id != None:
			if self.coinapi.verify_period(period_id) == False:
				raise ValueError(f'{period_id} not found in period_index')

		return f'{exchange_id}_{coin_id}_{period_id}'


	def add_exchange(self, exchange_id):
		'''
		Parameters:
			exchange_id : (str) Name of exchange in coinapi format
								ex: 'KRAKEN'
		'''
		#breaks function if exchange_id is invalid
		if self.coinapi.verify_exchange(exchange_id) == False:
			return None

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
		#has data is used to flag the exchange_id when there is 
		#data found in database associated to it
		has_data = False

		#Cannot delete exchange_id when there is data associated with
		#exchange in database
		for index_id, item_index in Database.historical_index.items():
			if (exchange_id == item_index['exchange_id'] and 
					item_index['datapoints'] != 0):
				#if exchange_id is found with data it cannot be removed
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


	def backfill(self, coin_id, time_increment, 
				 exchange_id=None, limit=None):
		'''
		This function accepts a coin_id and backfills all 
		tracked exchanges for that coin unless a specific 
		exchange_id is given

		Parameters:
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
							 - used to backfill specific exchange_id 
			limit          : (int) value used to limit each coins 
								   request
		'''

		print('Backfilling Historical Data')
		print('----------------------------------------------------')

		#verifies that parameters are supported by coinapi
		if self.coinapi.verify_increment(time_increment) == False:
			return None
		elif coin_id not in Database.settings['tracked_coins']:
			print(f'WARNING: "{coin_id}" is not being tracked')
			return None
		elif exchange_id != None:
			if (exchange_id not in 
					Database.settings['tracked_exchanges']):
				print(f'WARNING: "{exchange_id}" is not being tracked')
				return None

		#creates backfill list with index_id's
		backfill_dict = {}
		if exchange_id != None:
			index_id = self.index_id(exchange_id, coin_id, 
									 time_increment=time_increment)
			backfill_dict = {exchange_id: index_id}
		if exchange_id == None:
			#loads an index_id for each tracked exchange
			for tracked_exchange in Database.settings['tracked_exchanges']:
				index_id = self.index_id(tracked_exchange, 
										 coin_id, 
										 time_increment=time_increment)
				backfill_dict.update({index_id: tracked_exchange})

		#period_id string equivalent to time_increments
		period_id = self.coinapi.period_id(time_increment)

		#the first dir is the period_id str associated to time_increment
		filepath = Database.historical_base_path + f'/{period_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)
		#the final dir is the coin_id
		filepath += f'/{coin_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)

		#creates a new index item in historical index for coins that 
		#do not already have one.
		for index_id, exchange_id in backfill_dict.items():
			if index_id not in Database.historical_index:
				#loads coin_data for new index_item
				coin_data = Database.coin_index[exchange_id][coin_id]

				#filename-example: 'KRAKEN_BTC_5MIN.csv'
				filename = f'{index_id}.csv'
				path = filepath + f'/{filename}' #adds filename to dir
				#creates file if there is none
				if os.path.exists(path) == False:
					open(path, 'w')

				#fills out required information for new 
				#historical index_item
				index_item = {
					'filename': filename,
					'filepath': path,
					'symbol_id': coin_data['symbol_id'],
					'exchange_id': exchange_id,
					'asset_id_quote': coin_data['asset_id_quote'],
					'asset_id_base': coin_data['asset_id_base'],
					'period_id': period_id,
					'time_increment': time_increment,
					'datapoints': 0,
					'data_start': coin_data['data_start'],
					'data_end': coin_data['data_start']#not a typo
				}

				print(f'Added {index_id} to Historical Index')

				#updates historical_index
				Database.historical_index.update({index_id: index_item})
		#saves changes to file
		self.save_files()

		#The following backfills all items items in backfill_dict
		#coinapi.historical() needs a list of the indexes
		backfill_indexes = {}
		for index_id, exchange_id in backfill_dict.items():
			#loads the corresponding index into indexes
			backfill_indexes.update(
				{index_id: Database.historical_index[index_id]}
			)

		#requests backfill data
		data = self.coinapi.historical(backfill_indexes, limit=limit)

		#changes all time columns to unix format and
		#adds the "isnan" and "average_price" columns
		print('Preping Historical Data')
		data = prep_historical(data)

		#iterates through data and adds it to file
		for index_id, df in data.items():
			#data file should exist

			filepath = Database.historical_index[index_id]['filepath']

			#loads existing data and adds new data to it
			existing_data = pd.read_csv(filepath)

			#adds new data to existing
			existing_data.append(response_data, ignore_index=True, 
								 sort=False)

			#loads index and changes values according to new data
			index_item = Database.historical_index[index_id]
			#datapoints
			index_item['datapoints'] = len(existing_data.index)
			#data_end
			data_end = existing_data.iloc[-1, 'time_period_end']
			index_item['data_end'] = unix_to_date(data_end)

			#updates historical_index with changes and saves to file
			Database.historical_index[index_id] = index_item
			self.save_files()

		print('Backfill Complete')