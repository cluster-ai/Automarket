
#standard libraries
import json
import os
import time

#third-party packages
import pandas as pd
import numpy as np

#local modules
from .coinapi import Coinapi
from .preproc import unix_to_date, date_to_unix
import modules.features as features

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
		if os.path.exists(Database.features_index_path) == False:
			print(f'File Not Found -> {Database.features_index_path}')
			open(Database.features_index_path, 'w')

		print('Loading features Index: '
			  + Database.features_index_path)
		#loads indexes for training index
		with open(Database.features_index_path) as file:
			try: 
				Database.features_index = json.load(file)
			except ValueError:
				Database.features_index = []
				print('NOTICE: file is empty -> '
					  + Database.features_index_path)

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


	def save_files():
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


	def add_historical_item(exchange_id, coin_id, time_increment):
		'''
		Adds historical item to historical_index

		Parameters:
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
		'''
		#verifies that parameters are supported by coinapi
		if Coinapi.verify_increment(time_increment) == False:
			return None
		elif coin_id not in Database.settings['tracked_coins']:
			print(f'WARNING: "{coin_id}" is not being tracked')
			return None
		elif exchange_id != None:
			if (exchange_id not in 
					Database.settings['tracked_exchanges']):
				print(f'WARNING: "{exchange_id}" is not being tracked')
				return None

		#index_id used as a key for historical_index items
		index_id = Database.index_id(exchange_id, coin_id, time_increment)

		#stops function if item already found in historical_index
		if index_id in Database.historical_index:
			print(f'NOTICE: Historical Index already has {index_id}')
			return None

		#period_id string equivalent to time_increments
		period_id = Coinapi.period_id(time_increment)

		#the first dir is the period_id str associated to time_increment
		filepath = Database.historical_base_path + f'/{period_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)
		#the final dir is the coin_id
		filepath += f'/{coin_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)

		#loads coin_data for new index_item
		coin_data = Database.coin_index[exchange_id][coin_id]

		#filename-example: 'KRAKEN_BTC_5MIN.csv'
		filename = f'{index_id}.csv'
		filepath = filepath + f'/{filename}' #adds filename to dir
		#creates file if there is none
		if os.path.exists(filepath) == False:
			open(filepath, 'w')

		#fills out required information for new 
		#historical index_item
		index_item = {
			'filename': filename,
			'filepath': filepath,
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
		Database.save_files()


	def backfill(coin_id, time_increment, limit=None):
		'''
		This function accepts a coin_id and backfills all 
		tracked exchanges for that coin unless a specific 
		exchange_id is given

		Parameters:
			coin_id        : (str) crytpocurrency id: 'BTC'
								   - the currency being backfilled
			limit          : (int) limit for each coinapi request
		'''

		#verifies coin_id and time_increment parameters
		if Coinapi.verify_increment(time_increment) == False:
			return None
		elif coin_id not in Database.settings['tracked_coins']:
			print(f'WARNING: "{coin_id}" is not being tracked')
			return None

		print('Backfilling Historical Data')
		print('----------------------------------------------------')

		#loads an index_id for each tracked exchange
		backfill = {}
		match_date = None
		no_match = False
		for tracked_exchange in Database.settings['tracked_exchanges']:
			#generates index_id
			index_id = Database.index_id(tracked_exchange, coin_id,
										 time_increment)
			#loads id into backfill dict
			backfill.update({index_id: tracked_exchange})

			#generates historical_item for current item
			#if it doesn't already exist
			if index_id not in Database.historical_index:
				Database.add_historical_item(tracked_exchange, coin_id, 
											 time_increment)

			#loads index of current item
			item_index = Database.historical_index[index_id]

			#determines index_id with most recent 'data_end' value
			if match_date == None:
				#initializes match_date for first item
				match_date = item_index['data_end']
			elif (date_to_unix(match_date) < 
					date_to_unix(item_index['data_end'])):
				no_match = True #true if data_end does not all match
				#determines if current item has more recent data_end
				#than the other items so far
				match_date = item_index['data_end']

		#period_id string equivalent to time_increments
		period_id = Coinapi.period_id(time_increment)

		if no_match == True:
			print(f"NOTICE: backfill items don't match")

		#The following backfills all items items in backfill
		for index_id, exchange_id in backfill.items():
			#loads the index of current item
			item_index = Database.historical_index[index_id]
			#location of historical_data file for current item
			filepath = item_index['filepath']

			#doesn't backfill past match_date if no_match==True
			new_limit = limit
			if no_match == True:
				#match_limit is the number of requests to reach match_date
				match_limit = (date_to_unix(match_date) - 
							   date_to_unix(item_index['data_end']))
				match_limit = match_limit / item_index['time_increment']
				#limit will not be higher the given parameter 'limit'
				if match_limit < limit:
					new_limit = match_limit

			#requests backfill data
			response = Coinapi.historical(item_index, new_limit)

			#extracts data and time_end from response
			data = response['data']
			time_start = response['time_start']
			time_end = response['time_end']

			#loads existing data and adds new data to it
			if (os.path.exists(filepath) == True and 
					item_index['datapoints'] > 0):
				#if there is existing_data, data is appended to it
				existing_data = pd.read_csv(filepath)

				#makes existing_data.index equal to 'time_period_start'
				existing_data.set_index('time_period_start', drop=False,
										inplace=True)

				#adds new data to existing
				existing_data = existing_data.append(data)
			else:
				#if no data is found then existing_data = response_data
				print('No existing data for:', filepath)
				existing_data = data

			#saves new data to file
			existing_data.to_csv(filepath, index=False)

			#loads index and changes values according to new data
			index_item = Database.historical_index[index_id]
			#datapoints
			index_item['datapoints'] = len(existing_data.index)
			#data_end 
			index_item['data_end'] = time_end

			#updates historical_index with changes and saves to file
			Database.historical_index[index_id] = index_item
			Database.save_files()

		print('Backfill Complete')


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


	def feature_group(index_id, start_time=None, end_time=None):
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


	def add_feature(index_id, feature_id):
		'''
		This function is used by the feature.py
		module to add a feature/feature_group. 

		Parameters:
			index_id   : (str) id used for the feature group
						  (it is the same as historical_data)
			feature_id : (str) id used for a single feature
							   within a feature group
			data       : (pd.Series) data that will overwrite 
							the current items in feautre 
		'''

		#verifies given index_id
		if index_id not in Database.historical_index:
			raise KeyError(f'"{index_id}" not in Historical Index')

		#verifies index_id not already in features_index
		if index_id in Database.features_index:
			print(f'NOTICE: {index_id} already in Features Index')

		#historical index data from index_id
		data_index = Database.historical_index[index_id]

		###################################################
		###Verify Feature Group

		#the first dir is the period_id str associated to time_increment
		filepath = Database.features_base_path + f'/{period_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)
		#the next dir is the coin_id
		filepath += f'/{coin_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)
		#the final dir is the index_id
		filename = f'{index_id}.csv'
		filepath += f'/{filename}'

		#if either index or file not found, re-initialize feature-group
		if (os.path.exists(filepath) == False or 
				index_id not in Database.features_index):

			#creates new file if one is not found
			if os.path.exists(filepath) == False:
				open(filepath, 'w')
			
			#overwrites file with time_period_start col from historical
			df = Database.historical(index_id).loc[:, ['time_period_start']]
			df.to_csv(filepath, index=False)

			index_item = {
				'filename': filename,
				'filepath': filepath,
				'features': {},
				'symbol_id': data_index['symbol_id'],
				'exchange_id': data_index['exchange_id'],
				'asset_id_quote': data_index['asset_id_quote'],
				'asset_id_base': data_index['asset_id_base'],
				'period_id': data_index['period_id'],
				'time_increment': time_data_index['increment'],
				'even_features': False,
				'data_start': data_index['data_start'],
				'data_end': data_index['data_start']#not a typo
			}

			print(f'Added {index_id} to Features Index')

			#updates historical_index
			Database.features_index.update({index_id: index_item})
			#saves changes to file
			Database.save_files()

		###################################################
		###Adds Feature

		#database does not care what feature_id is, it is
		#only useful to feature.py module when updating

		#loads feature group
		group_index = Database.features_index[index_id]

		#verifies that feature does not exist
		if feature_id not in group_index['features']:
			#update features_index with feature
			Database.features_index[index_id]['features'].update(feature_id)
			print(f'Added {feature_id} to {index_id} Feature Group')
		else:
			print(f'NOTICE: {feauture_id} already exists for {index_id}')


	def update_feature_group(index_id):
		'''
		This function updates every feature in "index_id" 
		feature group to the most recent historical_data 
		values.

		NOTE: Database does not care about the contents
		of feature_group['features'] or filname.csv

		Parameters:
			index_id : (str) id for historical_index item
							and corresponding feature_group
		'''

		#feature_group index
		group_index = Database.features_index[index_id]

		#feature_group data
		group_df = Database.feature_group(index_id)

		#calls feature.py function to update features df and
		#the feature_group['features'] index
		'''features.function(group_index, group_df)'''