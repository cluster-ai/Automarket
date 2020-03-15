
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


'''
Module - database.py

Last Refactor: Alpha-v1.0 (In Progress)


CONTENTS:

class Database():
	def load_file(path, try_func, fail_func):
		#tool for loading a single file

	def load_files():
		#loads all database index files
		#NOTE: DOES NOT LOAD COINAPI FILES

	def save_file(path, data):
		#tool for saving a single json file into database

	def save_files():
		#commits database indexes to file
		#NOTE: DOES NOT SAVE COINAPI FILES
'''


#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################


class Database():
	#filepaths to different portions of database file structure
	#NOTE: dir -> to folder, path -> to file
	base_dir = 'database'

	historical_dir = base_dir + '/historical'
	historical_index_path = historical_dir + '/historical_index.json'
	features_dir = base_dir + '/features'
	features_index_path = features_dir + '/features_index.json'
	settings_path = base_dir + '/settings.json'

	#coinapi data paths
	coinapi_dir = base_dir + '/coinapi'
	coin_index_path = coinapi_dir + '/coin_index.json'
	exchange_index_path = coinapi_dir + '/exchange_index.json'
	period_index_path = coinapi_dir + '/period_index.json'
	api_index_path = coinapi_dir + '/api_index.json'

	#dict variables that track/index data in database
	historical_index = {}
	features_index = {}
	coin_index = {}
	exchange_index = {}
	period_index = {}
	api_index = {}
	settings = {} #stores application configs


	def __init__():
		#makes sure fixed directories all exist (directories)
		###BASE_DIR###
		if os.path.isdir(Database.base_dir) == False:
			os.mkdir(Database.base_dir)
		###HISTORICAL_DIR###
		if os.path.isdir(Database.historical_dir) == False:
			os.mkdir(Database.historical_dir)
		###FEATURES_DIR###
		if os.path.isdir(Database.features_dir) == False:
			os.mkdir(Database.features_dir)
		###COINAPI_DIR###
		if os.path.isdir(Database.coinapi_dir) == False:
			os.mkdir(Database.coinapi_dir)

		#loads index and settings files to Database
		Database.load_files()


	def load_file(path, try_func, fail_func):
		'''
		Parameters:
			path      : (str) path to file from main directory
			try_func  : (function) scrypt that is run to load file
				NOTE: has 1 argument 'json'
			fail_func : (function) scrypt that is run if load fails 
				NOTE: has no arguments

		Tool for loading a single json file
		'''
		#creates file if not found
		if os.path.exists(path) == False:
			print(f'NOTICE: creating file -> {path}')
			open(path, 'w')
			fail_func()
		else:
			print('Loading: ' + path)
			#loads contents of file with path, "Database.setting_path"
			with open(path) as file:

				#loads json file
				file_data = json.load(file)

				if file_data == {} or file_data == []:
					#file has only {} or []
					fail_func()
					print('NOTICE: file empty -> ' + path)
				else:
					try:#attempts to load file contents
						try_func(file_data)
					except ValueError:
						fail_func()
						print('NOTICE: file empty -> ' + path)


	def load_files():
		#loads all database index files
		#NOTE: DOES NOT LOAD COINAPI FILES

		print('----------------------------------------------------')
		print('Loading Files...\n')

		###SETTINGS###
		def try_func(json):
			Database.settings = json
		def fail_func():
			Database.settings = {}
		Database.load_file(Database.settings_path, try_func, fail_func)

		###FEATURES_INDEX###
		def try_func(json):
			Database.features_index = json
		def fail_func():
			Database.features_index = {}
		Database.load_file(Database.features_index_path, try_func, fail_func)

		###HISTORICAL_INDEX###
		def try_func(json):
			Database.historical_index = json
		def fail_func():
			Database.historical_index = {}
		Database.load_file(Database.historical_index_path, try_func, fail_func)

		print('----------------------------------------------------')


	def save_file(path, data):
		'''
		Parameters:
			path : (str) full path from main file
			data : (json) data being saved to file

		tool for saving a single json file into database
		'''
		#Checks to see if path exists, if not it creates one
		if os.path.exists(path) == False:
			open(path, 'x')
		#saves settings dict class variable to file by default
		#can change settings parameter to custom settings dict
		with open(path, 'w') as file:
			json.dump(data, file, indent=4)


	def save_files():
		#commits database indexes to file
		#NOTE: DOES NOT SAVE COINAPI FILES

		###SETTINGS###
		Database.save_file(Database.settings_path, 
						   Database.settings)
		###TRAINING_INDEX###
		Database.save_file(Database.features_index_path, 
						   Database.features_index)
		###HISTORICAL_INDEX###
		Database.save_file(Database.historical_index_path, 
						   Database.historical_index)


	#######################################################
	###Alpha-v1.0 end of progress
	#######################################################


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