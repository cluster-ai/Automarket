
#standard libraries
import json
import os
import time

#third-party packages
import pandas as pd
import numpy as np

#local modules
from define import *
from .preproc import unix_to_date, date_to_unix

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
Database.py Design Target:
	Handles the mechanisms at which this program
	stores and retrieves data. The only local 
	module this module imports is preproc.py.
'''

class Database():
	#filepaths to different portions of database file structure
	base_path = 'database'

	historical_base_path = base_path + '/historical_data'
	historical_index_path = (historical_base_path 
							+ '/historical_index.json')
	features_base_path = base_path + '/features_data'
	features_index_path = (features_base_path
						  + '/features_index.json')
	settings_path = base_path + '/settings.json'
	coin_index_path = base_path + '/coin_index.json'

	#dict variables that track/index data in database
	historical_index = {}
	features_index = {}
	coin_index = {}

	#used by the other modules to store program wide information
	settings = {}


	def __init__():
		#loads base paths (directories)
		if os.path.isdir(Database.base_path) == False:
			os.mkdir(Database.base_path)

		if os.path.isdir(Database.historical_base_path) == False:
			os.mkdir(Database.historical_base_path)

		if os.path.isdir(Database.features_base_path) == False:
			os.mkdir(Database.features_base_path)

		#loads index and settings files to Database
		Database.load_files()


	def load_files():

		print('----------------------------------------------------')
		print('Loading Files...')
		print('...')

		###SETTINGS###
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
		#Checks to see if path exists, if not creates one
		if os.path.exists(Database.features_index_path) == False:
			print(f'File Not Found -> {Database.features_index_path}')
			open(Database.features_index_path, 'w')

		print('Loading Features Index: '
			  + Database.features_index_path)
		#loads indexes for training index
		with open(Database.features_index_path) as file:
			try: 
				Database.features_index = json.load(file)
			except ValueError:
				Database.features_index = {}
				print('NOTICE: file is empty -> '
					  + Database.features_index_path)

		###HISTORICAL_INDEX###
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


	def save_files():

		#function for saving files
		def save(path, data):
			'''
			Parameters:
				path : (str) full path from main file
				data : (json) data being saved to file
			'''
			#Checks to see if path exists, if not it creates one
			if os.path.exists(path) == False:
				open(path, 'x')
			#saves settings dict class variable to file by default
			#can change settings parameter to custom settings dict
			with open(path, 'w') as file:
				json.dump(data, file, indent=4)

		###SETTINGS###
		Database.save(Database.settings_path, Database.settings)
		###TRAINING_INDEX###
		Database.save(Database.training_index_path, Database.training_index)
		###HISTORICAL_INDEX###
		Database.save(Database.historical_index_path, Database.historical_index)
		###COIN_INDEX###
		Database.save(Database.coin_index_path, Database.coin_index)


	def reset_tracked():
		#resets tracked_coins in settings

		###TRACKED COINS###
		#lists all supported coins from tracked exchanges
		init_loop = True
		coins = {}
		for exchange_id, exchange_index in Database.coin_index.items():
			if init_loop == True:
				init_loop = False
				#the first iteration initializes coins with all data
				#from that coin
				coins = list(exchange_index.keys())
			else:
				#creates a new list of coins in current exchange
				compare_list = list(exchange_index.keys())

				#compare new list to coins and delete coins that
				#are not in both
				for coin_id, coin_data in coins:
					if coin_id not in compare_list:
						coins.remove(coin_id)
		#update settings
		Database.settings['tracked_coins'] = coins

		print(Database.settings)

		print('NOTICE: reset database settings to their default')

		Database.save_files()


	def reset_coin_index():
		#reloads the coins for each tracked exchange

		if Database.settings['tracked_exchanges'] == []:
			Database.coin_index = {}
			print('NOTICE: No Tracked Exchanges')
		else:
			filters = {
				'asset_id_quote': Coinapi.asset_id_quote
			}
			#requests all currency data and filters by fiat currency
			response = Coinapi.request('free_key',
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
				exchange_coins = Coinapi.filter(response,
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
		Database.save_files()

		print('----------------------------------------------------')


	def index_id(exchange_id, coin_id, 
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
			period_id = Coinapi.period_id(time_increment)
		elif period_id != None:
			if Coinapi.verify_period(period_id) == False:
				raise ValueError(f'{period_id} not found in period_index')

		return f'{exchange_id}_{coin_id}_{period_id}'


	def add_exchange(exchange_id):
		'''
		Parameters:
			exchange_id : (str) Name of exchange in coinapi format
								ex: 'KRAKEN'
		'''
		#breaks function if exchange_id is invalid
		if Coinapi.verify_exchange(exchange_id) == False:
			return None

		if exchange_id in Database.settings['tracked_exchanges']:
			#checks if exchange is already in tracked_exchanges
			print(f'NOTICE: {exchange_id} Already Being Tracked')
		elif Coinapi.verify_exchange(exchange_id):
			#Verifies the given exchange is a valid coinapi exchange_id
			print(f'Adding Exchange: {exchange_id}')
			Database.settings['tracked_exchanges'].append(exchange_id)
			#saves settings
			Database.save_files()
			#updates coin_index
			Database.reset_coin_index()


	def remove_exchange(exchange_id):
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
		elif (Coinapi.verify_exchange(exchange_id) and
				has_data == False):
			#Verifies the given exchange is a valid coinapi exchnage_id
			print(f'Removing Exchange: {exchange_id}')
			#removes exchange_id from settings and saves settings ti file
			Database.settings['tracked_exchanges'].remove(exchange_id)
			Database.save_files()
			#resets coin_index with new tracked_exchanges
			Database.reset_coin_index()


	def historical(index_id, start_time=None, end_time=None):
		'''
		Returns dataframe for the specified historical data

		Parameters:
			index_id   : (str) id to desired historical data

			start_time : (int, unix-utc) returned data
						 will be >= this time
				NOTE: if start_time == None, all data
					  is loaded before end_time

			end_time   : (int, unix-utc) returned data
						 will be <= this time
				NOTE: if end_time == None, all data is
					  is loaded after start_time

		NOTE: start_time and end_time parameters both use
				'time_period_start' column as reference for
				the interval.
		'''

		#verifies given index_id
		if index_id not in Database.historical_index:
			raise KeyError(f'"{index_id}" not in Historical Index')

		#makes sure start_time is <= end_time
		if start_time != None and end_time != None: 
			if start_time > end_time:
				raise RuntimeError(f'start_time > end_time')

		#loads data file path
		filepath = Database.historical_index[index_id]['filepath']
		#loads data file name
		filename = Database.historical_index[index_id]['filename']

		#loads all data from file
		data = pd.read_csv(filepath)

		#makes data.index equal to 'time_period_start' column
		data.set_index('time_period_start', drop=False, inplace=True)

		#slices data based on start_time if parameter was given
		if start_time != None:
			#catches out out of scope start_time
			if start_time not in data.index:
				raise IndexError(f'{start_time} index not in {filename}')
			data = data.loc[start_time: , :]

		#slices data based on end_time if parameter was given
		if end_time != None:
			#catches out out of scope end_time
			if end_time not in data.index:
				raise IndexError(f'{end_time} index not in {filename}')
			data = data.loc[:end_time, :]

		return data


	def features(index_id, start_time=None, end_time=None):
		'''
		Returns dataframe for the specified feature_group

		Parameters:
			index_id : (str) id for historical_data item
						and its corresponding feature_group

			start_time : (int, unix-utc) returned data
						 will be >= this time
				NOTE: if start_time == None, all data
					  is loaded before end_time

			end_time   : (int, unix-utc) returned data
						 will be <= this time
				NOTE: if end_time == None, all data is
					  is loaded after start_time

		NOTE: This assumes time_period_start data is included
		with the data
		'''

		#verifies given index_id
		if index_id not in Database.features_index:
			raise KeyError(f'"{index_id}" not in Features Index')

		#makes sure start_time is <= end_time
		if start_time != None and end_time != None: 
			if start_time > end_time:
				raise RuntimeError(f'start_time > end_time')

		#loads data file path
		filepath = Database.features_index[index_id]['filepath']
		#loads data file name
		filename = Database.features_index[index_id]['filename']

		#loads all data from file
		data = pd.read_csv(filepath)

		#makes data.index equal to 'time_period_start' column
		data.set_index('time_period_start', drop=False, inplace=True)

		#slices data based on start_time if parameter was given
		if start_time != None:
			#catches out out of scope start_time
			if start_time not in data.index:
				raise IndexError(f'{start_time} index not in {filename}')
			data = data.loc[start_time: , :]

		#slices data based on end_time if parameter was given
		if end_time != None:
			#catches out out of scope end_time
			if end_time not in data.index:
				raise IndexError(f'{end_time} index not in {filename}')
			data = data.loc[:end_time, :]

		return data