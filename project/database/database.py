
import json
import os

import time
import datetime

import database.coin_api as coin_api
import database.preprocess as preprocess

from sklearn import preprocessing

import multiprocessing

from multiprocessing import Process, Value, Lock, Manager
from collections import deque

import pandas as pd
import numpy as np

import math

import matplotlib.pyplot as plt

class Database():
	def __init__(self):
		print('----------------------------------------------------')
		print('Initializing Program')
		print('----------------------------------------------------')
		self.coin_api = coin_api.CoinAPI()
		self.preprocess = preprocess.Preprocess()
		self.historical_base_path = "database/historical_data/"
		self.historical_index_path = f"{self.historical_base_path}historical_index.json"
		self.training_base_path = "database/training_data/"
		self.training_index_path = f"{self.training_base_path}training_index.json"
		self.handbook_path = f'{self.historical_base_path}handbook.json'
		self.config_path = 'database/config.json'
		self.data_increment = 300 #5 minute data increment

		#loads config.json
		with open(self.config_path) as file:
			self.config = json.load(file)


		#for self.next_update, the '- 36000' is for my current timezone relative to unix (HST)
		#ONLY USE FOR PRINTING TO CONSOLE
		self.next_update = self.SetUnixToDate(self.config['last_update'] + self.config['update_frequency'] - 36000)


		#makes sure handbook.json exists and has proper datastructure
		reset_handbook = False
		default_handbook = {'period_data': [], 'exchange_data': {}}
		if os.path.exists(self.handbook_path):
			try:
				with open(self.handbook_path) as file:
					self.handbook = json.load(file)

				#makes sure the dictionary has these two keys
				self.handbook['period_data']
				self.handbook['exchange_data']
			except:
				print(f'self.handbook data failed to load, resetting...')
				reset_handbook = True
		else:
			open(self.handbook_path, 'w')
			self.UpdateHandbook()
			reset_handbook = True

		self.update_database = False
		if ((self.config['last_update'] + self.config['update_frequency']) < time.time()):
			self.update_database = True
			self.UpdateHandbook()
		elif reset_handbook == False:
			print('handbook.json up to date, next update after', self.next_update, "HST")

		self.BackfillHistoricalData()




	def SetUnixToDate(self, unix):#input unix time as string or int
		#when using to display on screen, add to UTC unix param to offset for your timezone
		return datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S.%f0Z')
		#RETURNS UTC, confirmed

	def SetDateToUnix(self, date):
		unix = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f0Z')
		unix = unix.timestamp() - 36000#sets it to UTC
		return unix
		

	def UpdateHandbook(self):
		print('Updating handbook.json...')

		exchanges_response = self.coin_api.MakeRequest(url_ext=self.config['exchanges_url_ext'], 
									filters={'exchange_id': self.config['tracked_exchanges'],
											 'asset_id_quote': self.config['asset_id_quote']},
											 return_type='json')

		periods_response = self.coin_api.MakeRequest(url_ext=self.config['periods_url_ext'],
									filters={'length_seconds': 0}, omit_filtered=True, return_type='json')

		#filters out irrelevant exchange data, only keeps relevant_data_keys
		exchange_data = {}
		for tracked_exchange in self.config['tracked_exchanges']:
			#creates a new self.handbook['exchange_data'] element for each tracked_exchange
			exchange_data.update({tracked_exchange : []})

		#the only data keys this program needs for self.handbook
		relevant_data_keys = ['symbol_id', 
							  'symbol_type', 
							  'asset_id_base', 
							  'asset_id_quote', 
							  'data_start', 
							  'data_end']
		#this iterates through exchanges_response for relevent data
		# if an exchanges_response has all relevant_data_keys then it is appended
		for item in exchanges_response:
			for key, value in exchange_data.items():
				if value == item['exchange_id']:
					relevant_data = {}
					has_keys = True
					for key in relevant_data_keys:
						if self.coin_api.CheckForKey(key, item) == True:
							relevant_data.update({key: item[key]})
						else:
							has_keys = False
					if has_keys == True:
						extracted_data[exchange_id].append(relevant_data)
					break

		updated_handbook = {}
		updated_handbook.update({'period_data' : periods_response})
		updated_handbook.update({'exchange_data' : exchange_data})

		self.handbook = updated_handbook
		with open(self.handbook_path, 'w') as file:
			json.dump(self.handbook, file, indent=4)

		self.config['last_update'] = time.time()

		with open(self.config_path, 'w') as file:
			json.dump(self.config, file, indent=4)
		print("Finished: handbook.json up to date, next update after", self.next_update, "HST")


	def UpdateHistoricalIndex(self):
		#updates historical_data/historical_index.json file with self.historical_index
		with open(self.historical_index_path, 'w') as file:
				#when it is in the file, it will not have the "exchange_id" dictionary layer
				json.dump(self.historical_index, file, indent=4)


	def __InitHistoricalDir(self):

		'''
		The following looks at all tracked exchanges and crypto-coins in config.json and filters through
		handbook.json to find matches. If any are found and there is no existing dir/file for that currency pair 
		or exchange then those dir/files are generated 
		(ex: KRAKEN is found in self.config['tracked_exchanges'] so program verifies that a KRAKEN dir exists.
		Within the KRAKEN exchange a currency pair is found, "BTC" in "USD". so program verifies that the file 
		KRAKEN_SPOT_BTC_USD.csv exists within the KRAKEN dir)
		'''

		self.historical_index = {}
		#if you change historical_index_keys, you must change the corresponding if statments below
		self.historical_index_keys = ['filepath',
									  'symbol_id',
									  'exchange_id',
									  'symbol_type',
									  'asset_id_base',
									  'asset_id_quote',
									  'datapoints',
									  'data_start',
									  'data_end']

		#checks for self.historical_index_path defined in self.__init__()
		# creates file if not found
		if os.path.exists(self.historical_index_path) == True:
			#if file is found, it loads its contents
			with open(self.historical_index_path, 'r') as file:
				index = json.load(file)
				self.historical_index.update(index)
		else:
			#if no file is found it creates one
			open(self.historical_index_path, 'w')


		#looks through all tracked exchanges in self.handbook['exchange_data']
		for exchange_id, exchange_data in self.handbook['exchange_data'].items():
			#following uses coin_api function to filter through exchange contents by specified filter.
			#remember, contents of self.handbook['exchange_data'] are already filtered by asset_id_quote
			exchange_data = self.coin_api.JsonFilter(exchange_data, 
												{'asset_id_base': self.config['tracked_crypto']}, False)

			#checks for historical_data/(exchange_id), creates dir if not found
			exchange_path = self.historical_base_path+f"{exchange_id}"
			if os.path.isdir(exchange_path) == False:
				os.mkdir(exchange_path)

			#extracts data from each item and uses it to create/load historical data files
			for item in exchange_data:
				coin_data_filename = item['symbol_id']+".csv"
				coin_data_path = exchange_path+f"/{coin_data_filename}"
				#checks for historical/{exchange_id}/{symbol_id}.csv, creates file if not found
				if os.path.exists(coin_data_path) == False:
					open(coin_data_path, 'w')

					coin_data = {coin_data_filename: {}}
					for key in self.historical_index_keys:
						if key == 'filepath':
							coin_data[coin_data_filename].update({key: coin_data_path})
						elif key == 'exchange_id':
							coin_data[coin_data_filename].update({key: exchange_id})
						elif key == 'symbol_id':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'symbol_type':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'asset_id_base':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'asset_id_quote':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'datapoints':
							coin_data[coin_data_filename].update({key: 0})
						elif key == 'data_start':
							coin_data[coin_data_filename].update({key: item[key]+"T00:00:00.0000000Z"})
						elif key == 'data_end':
							coin_data[coin_data_filename].update({key: item['data_start']+"T00:00:00.0000000Z"})
					self.historical_index.update(coin_data)

		self.UpdateHistoricalIndex()

	def FindPeriodId(self, unix):
		for item in self.handbook['period_data']:
			if item['length_seconds'] == unix:
				return item['period_id']
		print('Error: period_id not found for unix_time value:', unix)
		return ''

	def LoadHistoricalData(self, filename):
		return pd.read_csv(self.historical_index[filename]['filepath'])

	def BackfillHistoricalData(self):
		self.__InitHistoricalDir()

		#the current version only supports 'balanced' backfilling of data
		#in other words it updates all tracked currencies in all exchanges evenly and at the same time
		if self.config['backfill_historical_data'] == True and self.update_database == True:
			print('----------------------------------------------------')
			print('Backfilling Historical Data')
			print('----------------------------------------------------')

			#The following finds the total number of backfilling requests being made.
			#backfill_list is the queue for things that will be backfilled
			backfill_list = {}
			print('Backfill List:')
			for filename, backfill_item in self.historical_index.items():
				if (backfill_item['exchange_id'] in self.config['tracked_exchanges'] and
					backfill_item['asset_id_base'] in self.config['tracked_crypto']):
					print('   ', filename)
					backfill_list.update({filename: backfill_item})

			backfill_count = len(backfill_list)
			print(f'{backfill_count} total requests\n')

			#limit_per_request is the number of datapoints each backfill item will request.
			#The sum of all requests is equal to the limit of the api_key being used * 98%...
			#                                    		   (this leaves 2% for troubleshooting)
			limit_per_request = int(self.coin_api.api_index['startup_key']['limit'] / backfill_count * 100 * 0.98)
			#one request is 100 datapoints so limit_per_request is made a multiple of 100
			limit_per_request = limit_per_request - (limit_per_request % 100)
			limit_per_request = 100

			#the following goes through each item within backfill_list
			#the key for each backfill_item is the filename (filename = f'{symbol_id}.csv')
			for filename, backfill_item in backfill_list.items():

				#url_ext is appended to the baseline coin_api url declared in coin_api.__init__()
				url_ext = self.config['historical_url_ext'].format(backfill_item['symbol_id'])
				#this query data are used as parameters for the api request
				queries = {'time_start': backfill_item['data_end'],
						   'limit': limit_per_request,
						   'period_id': self.FindPeriodId(self.data_increment)}

				print(queries)

				#no filter, the default request size is 100 (100 datapoints: uses one request)
				response = self.coin_api.MakeRequest(url_ext=url_ext, queries=queries, api_key_id='startup_key')

				#formats response from json into a 2d array
				response_data = pd.DataFrame.from_dict(response, orient='columns')

				#==============================================================
				#SET REQUEST DATES INTO UNIX VALUES
				#==============================================================
				prev_time = time.time()
				start_time = time.time()
				new_df = response_data.copy()

				print('Converting Timestamps to Unix')
				for index, row in new_df.iterrows():
					for col in new_df.columns:

						if 'time' in col:#if true, needs to be changed to unix time
							new_df.at[index, col] = self.SetDateToUnix(row[col])
					if index % 5000 == 0 and index != 0:
						current_time = time.time()
						delay = current_time - prev_time
						print(f"index: {index} || delay: {delay}")
						prev_time = current_time

				#==============================================================
				#VERIFIES CONTINUITY OF UNIX TIME CONVERSION
				#==============================================================
				print('Verifying Unix Dates')

				#timestamp = arbitrary unix number to test date-unix conversion
				timestamp = 1000000
				new_timestamp = self.SetUnixToDate(timestamp)
				new_timestamp = self.SetDateToUnix(new_timestamp)
				print(f'timestamp convertion test: {timestamp} || {new_timestamp}')

				#The following goes back and converts the unix time back to date in memory 
				# and compares to original request data
				#If the resulting date values are not the same after the conversion then 
				# something is wrong
				prev_time = time.time()
				for index, row in new_df.iterrows():
					for col in new_df.columns:

						if 'time' in col:
							if self.SetUnixToDate(row[col]) != response_data.at[index, col]:
								raise ValueError(
									'An Error Occured: SetDataFrameToUnix is different from argument: response_data')
						elif row[col] != response_data.at[index, col]:
							raise ValueError(
								'An Error Occured: SetDataFrameToUnix is different from argument: response_data')
					if index % 5000 == 0 and index != 0:
						current_time = time.time()
						delay = current_time - prev_time
						print(f"index: {index} || delay: {delay}")
						prev_time = current_time


				total_time = time.time() - start_time
				print(f'Time Format Change Duration: {total_time} seconds')

				response_data = new_df
				#==============================================================
				#==============================================================

				#loads existing historical_data for current backfill_item if any
				try:
					#if there is existing_data, response data is appended to it
					existing_data = pd.read_csv(backfill_item['filepath'])
					existing_data = existing_data.append(response_data, ignore_index=True, sort=False)
				except(pd.errors.EmptyDataError):
					#if no data is found then existing_data = response_data
					print('No existing data for:', backfill_item['filepath'])
					print('Creating New Dataframe')
					existing_data = response_data


				#existing_data is then saved to the proper csv file
				existing_data.to_csv(backfill_item['filepath'], index=False)

				#this updates the number of datapoints in backfill_item
				backfill_item['datapoints'] = len(existing_data.index)

				#changes data_start to reflect actual first datapoint
				backfill_item['data_start'] = self.SetUnixToDate(existing_data.at[0, 'time_period_start'])

				#this message is offset to the timezone UTC-36000 (HST)
				print(filename, 'updated to: ', self.SetUnixToDate(existing_data.iloc[-1]['time_period_end'] - 36000))
				print('----------------------------------------------------')

				#update currency index for current backfill_item
				#ONLY CHANGE TIME_END
				backfill_item['data_end'] = self.SetUnixToDate(existing_data.iloc[-1]['time_period_end'])


				#then self.historical_index['filename'] is updated with new backfill_item data
				self.historical_index[filename] = backfill_item

				self.UpdateHistoricalIndex()
		elif self.config['backfill_historical_data'] == False:
			print('database.config[\'backfill_historical_data\'] = false: not updating historical data')
		elif self.update_database == False:
			print('historical backfill requests are used, next refresh after', self.next_update, "HST")


	def UpdateTrainingIndex(self):
		#updates historical_data/training_index.json file with self.training_index
		with open(self.training_index_path, 'w') as file:
			json.dump(self.training_index, file, indent=4)


	def QueryTrainingData(self, **kwargs):
		print('----------------------------------------------------')
		print('Making Request For Training Data')
		print('----------------------------------------------------')

		#this loads training_index
		if os.path.exists(self.training_index_path):
			with open(self.training_index_path, 'r') as file:
				self.training_index = json.load(file)
		else:
			with open(self.training_index_path, 'w') as file:
				json.dump({}, file, indent=4)
				self.training_index = {}

		'''
		This function handles all training_data requests.
		The idea is that a data request will require a set of parameters for the format of data
		and will compare it to the data it already has. If the corresponding data exists and
		is up to date, it will just return that. If the data does not exist or is not up to date
		then the item will be generated or updated as needed.

		Parameters: (kwargs)
		- prediction_steps (maximum number of data fills in a row, this is because it loses accuracy
																					larger the gap)
		- exchange_id ('KRAKEN')
		- currencies (['BTC', 'ETH']) #order does not matter
		'''

		#Default Kwargs
		if 'prediction_steps' not in kwargs:
			kwargs['prediction_steps'] = 1
		if 'exchange_id' not in kwargs:
			kwargs['exchange_id'] = 'KRAKEN'
		if 'currencies' not in kwargs:
			kwargs['currencies'] = ['BTC', 'ETH']

		print(f"Query Parameters:")
		print(" - prediction_steps =", kwargs['prediction_steps'])
		print(" - exchange_id =", kwargs['exchange_id'])
		print(" - currencies =", kwargs['currencies'], '\n')

		#loop through training_index to find queried dataset
		matched_filename = ''
		for filename, index_item in self.training_index.items():
			#compare the format to existing indexes until a match is found
			#if no match is found then the training_data is generated

			#exchange_id
			if (index_item['exchange_id'] == kwargs['exchange_id'] and 
				len(index_item['currencies']) == len(kwargs['currencies'])):
				#compares kwargs['currencies'] items to each index_item['currencies'] item
				#kwarg_currency example == ['BTC', 'ETH']
				#index_currency example == {'KRAKEN_SPOT_ETH_USD.csv': 0, 'KRAKEN_SPOT_BTC_USD.csv': 1}
				matches = 0
				for kwarg_currency in kwargs['currencies']:
					for key, coin_filename in index_item['currencies'].items():
						#key is in format f"{currency}_{order_num}" ex: "BTC_0"
						if kwarg_currency in coin_filename:
							matches += 1

				#currencies
				if matches != len(kwargs['currencies']):
					continue;

				#prediction_steps
				if kwargs['prediction_steps'] != index_item['prediction_steps']:
					continue;

				matched_filename = filename
				break;


		dataset = pd.DataFrame()
		dataset_index = {}

		#generates new index if one wasn't found above
		if matched_filename == '':
			matched_filename = self.__AddTrainingIndex(kwargs['exchange_id'],
													   kwargs['prediction_steps'],
													   kwargs['currencies'])

		training_data = self.__LoadTrainingData(matched_filename)

		#puts all trend data in x and all other data in y
		x = training_data.copy()
		y = training_data.copy()
		for col in training_data.columns:
			if 'trend' in col:
				x = x.drop(columns=[col])
			else:
				y = y.drop(columns=[col])

		training_data = {'x': x, 'y': y}

		return training_data


	def __LoadTrainingData(self, filename_param):
		'''
		This function updates the dataset associated to the given 
		index identified by filename_param

		Every time this function is called. The dataset is completely reprocessed
		'''

		#verifies existance of given training_index key (filename_param)
		if filename_param not in self.training_index:
			print(f'Invalid filename "{filename_param}", database.__LoadTrainingData()')
			raise

		#loads contents of training_data index that will be updated
		index_item = self.training_index[filename_param]

		#generates the data file and enchange_id dir if it doesnt exist
		exchange_path = self.training_base_path+index_item['exchange_id']
		if os.path.exists(exchange_path) == False:
			os.mkdir(exchange_path)

		if os.path.exists(index_item['filepath']) == False:
			open(index_item['filepath'], 'w')
			print('Generating', index_item['filepath'])

		#==============================================================
		#Initializes column and historical_data for processing
		#==============================================================

		#These are all the columns that each currency has their own copy of
		#time_period_start is the first column by default and so not included
		used_columns = ['price_high',
						'price_low',
						'average_price',
						'trades_count',
						'volume_traded',
						'is_nan',
						'trend']
						#if this is changed, a training_data reset is required

		#Goes through currencies and loads historical data into historical_data var
		#index_item['currencies'] format example:
		#"currencies:" : {
		#	"BTC_0" : "KRAKEN_SPOT_BTC_USD.csv",
		#	"ETH_1" : "KRAKEN_SPOT_ETH_USD.csv"						
		#}
		self.historical_data = {}
		#this verifies that all currencies are being tracked
		for key, filename in index_item['currencies'].items():
			match = False
			for tracked_currency in self.config['tracked_crypto']:
				if tracked_currency in filename:
					match = True

			if match == True:
				#creates a dictionary of historical_data using coin name (ex: {"BTC": bitcoin_data, ...})
				self.historical_data.update({key: self.LoadHistoricalData(filename)})
			else:
				print(f"Untracked currency in {filename}")
				raise

		#creates currency key list IN ORDER OF CURRENCIES, NETWORK WILL FAIL WITHOUT ORDER
		#The second loop is needed to make sure each item is in order
		#The currency key list gives us accurate, in-order calling of historical_data
		currency_order = []
		for order_num in range(0, len(self.historical_data)):
			for key, dataset in self.historical_data.items():
				if str(order_num) in key:
					currency_order.append(key)
		
		#Generates list of columns in order of currency_order
		# starting with time_period_start
		columns = ['time_period_start']
		for coin in currency_order:
			for col in used_columns:
				columns.append(f"{coin}|{col}")

		#loads existing data if any
		existing_data = pd.DataFrame()
		try:
			existing_data = pd.read_csv(index_item['filepath'])

			#verifies that existing_data is not missing_columns
			'''
			missing_columns = []
			for col in columns:
				if col not in existing_data.columns:
					missing_columns.append(col)
			if len(missing_columns) > 0:
				print('Existing data on', index_item['filename'], 'is missing columns:')
				print(missing_columns)
				raise
			#there cannot be extra columns from here on
			extra_columns = len(existing_data.columns) - len(columns)
			if extra_columns > 0:
				print(extra_columns, 'Extra Columns Found')
				raise
			'''
		except:
			existing_data = pd.DataFrame(columns=columns)


		#returns data if the data is up to date
		matches = 0
		for coin in currency_order:
			coin_index = self.historical_index[index_item['currencies'][coin]]
			if index_item['data_end'] == coin_index['data_end']:
				matches += 1
		if matches == len(currency_order):
			print('training_data up to date')
			print(existing_data.head(10))
			return existing_data


		#This finds the interval where data from all coins overlap
		#If there is existing_data, the start_data is index_item['data_end']
		#Else, the start time must be found.
		#  It must be the most recent historical_data data_start of all coins
		start_time = 0
		end_time = 0
		for coin in currency_order:
			coin_index = self.historical_index[index_item['currencies'][coin]]
			coin_start_time = self.SetDateToUnix(coin_index['data_start'])
			coin_end_time = self.SetDateToUnix(coin_index['data_end'])
			if coin_start_time > start_time:
				start_time = coin_start_time
			if coin_end_time < end_time or end_time == 0:
				end_time = coin_end_time


		#SORT OF IRRELAVENT COMMENT
		#New_data is declared with the same columns as historical_data
		# but has a NaN value for each cell at initialization. The index
		# count is also made to reflect the total number of timesteps
		# independent of any missing data starting at start_time
		total_datapoints = int(end_time - start_time) / self.data_increment
		if total_datapoints - int(total_datapoints) != 0:
			print('data_increment calculation error, database.__LoadTrainingData()')
		else:
			#this gets rid of .0 at the end of number so further calculations with
			#it are not considered floating points
			total_datapoints = int(total_datapoints)


		#init_index is a list with length total_datapoints
		#Initializing the new_data with values increases compute time
		# by several orders of magnitude because all the memory addresses 
		# needed for the list have been registered before the loop rather
		# than during each iteration of it.
		init_index = []
		for x in range(total_datapoints):
			time_increment = int(x * self.data_increment + start_time)
			init_index.append(time_increment)
		new_data = pd.DataFrame(columns=columns, index=init_index)
		new_data.time_period_start = new_data.index

		#==============================================================
		#Data Processor
		#==============================================================

		for coin in currency_order:

			#The following changes the index of historical_data to equal time_period_start
			#=============================================================================
			#=============================================================================
			#converts time_period_start column (soon to be index) to int
			self.historical_data[coin].time_period_start = self.historical_data[coin].time_period_start.astype(int)
			
			#sets the index to the time_period_start column and drops time_period_start
			self.historical_data[coin] = self.historical_data[coin].set_index('time_period_start', drop=False)

			#adds used_columns to historical_data if not already included
			for col in used_columns:
				if col not in self.historical_data[coin].columns:
					self.historical_data[coin][col] = np.nan
			
			#this drops all unused columns in local historical_data variable
			# so that training_data does not have it
			drop_columns = []
			for col in self.historical_data[coin].columns:
				if col not in used_columns:
					drop_columns.append(col)
			self.historical_data[coin] = self.historical_data[coin].drop(columns=drop_columns)

			#renames columns in local historical_data variable to match training_data
			new_columns = {}
			for col in self.historical_data[coin].columns:
				new_columns.update({col: f"{coin}|{col}"})
			self.historical_data[coin] = self.historical_data[coin].rename(columns=new_columns)

			for col in self.historical_data[coin].columns:
				#BEFORE adding historical_data to new_data, this sets all historical_data is_nan to False (0)
				#Additionally, all new_data is_nan is set to True (1)
				#That way, when merged, new_data will start with False and only datapoints 
				#  with data will be set to True
				if 'is_nan' in col:
					new_data[col] = 1 #True, is_nan
					self.historical_data[coin][col] = 0 #False, not is_nan

				#adds values to new_data from historical_data
				new_data.loc[:, col] = self.historical_data[coin].loc[:, col]


		#new_data = new_data.head(300)
		#total_datapoints = 300
		self.historical_data = new_data.copy()
	
		#used to calculate time delay between iterations of following loop
		init_time = time.time()

		#this sets up a batch of data for each processing thread so that all data is processed once
		proc_length = math.ceil(total_datapoints / multiprocessing.cpu_count())
		proc_interval = []
		proc_intervals = []
		last_index = self.historical_data.index[-1]
		for index in self.historical_data.index:
			proc_interval.append(index)
			if len(proc_interval) == proc_length or index == last_index:
				proc_intervals.append(proc_interval)
				proc_interval = []

		manager = Manager()
		new_proc_data = manager.dict()
		lock = Lock()

		#uses proc_data_all in loop to set up each process for multithreading, order does not matter
		#MULTIPROC SETUP
		print("preping data..")
		procs = []
		for proc_num, proc_interval in enumerate(proc_intervals):
			print(proc_num)
			proc = Process(target=self.MultiprocSetup, args=(proc_interval, 
															new_proc_data, 
															lock,
															proc_num,))
			procs.append(proc)
			proc.start()
		#ends multithreaded processes
		for proc in procs:
			proc.join()
		for proc_num, dataframe in new_proc_data.items():
			new_data.loc[proc_intervals[proc_num], :] = dataframe.loc[proc_intervals[proc_num], :]


		self.historical_data = new_data.copy()

		#wipes new_proc_data
		new_proc_data = manager.dict()

		print("preprocessing...")
		#MULTIPROC FINAL
		procs = []
		for proc_num, proc_interval in enumerate(proc_intervals):
			proc = Process(target=self.MultiprocFinal, args=(proc_interval, 
															index_item['prediction_steps'],
															new_proc_data,
															lock,
															proc_num,))
			procs.append(proc)
			proc.start()
		#ends multithreaded processes
		for proc in procs:
			proc.join()
		for proc_num, dataframe in new_proc_data.items():
			new_data.loc[proc_intervals[proc_num], :] = dataframe.loc[proc_intervals[proc_num], :]


		total_time = time.time() - init_time
		print(f"Total Duration: {total_time}")

		#==============================================================
		#Data Processor End
		#==============================================================

		print(new_data.head(150))

		#normalization
		'''
		for col in new_data.columns:
			if 'is_nan' not in col and 'trend' not in col:
				print(new_data[col].values)
				new_data[col] = preprocessing.scale(new_data[col].values)
		'''

		#updates local index variable on new data
		index_item['datapoints'] = total_datapoints
		index_item['data_start'] = self.SetUnixToDate(start_time)
		index_item['data_end'] = self.SetUnixToDate(end_time)

		#updates training_index with newly updated local index_item data
		# and saves it to file
		self.training_index[filename_param] = index_item
		self.UpdateTrainingIndex()

		#This saves new_data to the f"{symbol_id}.csv" file
		#new_data.to_csv(index_item['filepath'], index=False)

		return new_data

	def MultiprocSetup(self, proc_interval=[], proc_data=[], lock=0, proc_num=0):
		count = 0
		start = proc_interval[0]
		end = proc_interval[-1]
		historical_data = self.historical_data.loc[start:end, :]
		new_data = historical_data.copy()
		for index, row in historical_data.iterrows():
			for col in historical_data.columns:

				if 'is_nan' in col:
					if np.isnan(row[col]):
						new_data.at[index, col] = 1 #is_nan = true

				if 'average_price' in col:
					low = self.historical_data.at[index, col.replace('average_price', 'price_low')]
					high = self.historical_data.at[index, col.replace('average_price', 'price_high')]
					average = (low + high) / 2
					new_data.at[index, col] = average
			count += 1
		proc_data[proc_num] = new_data

	def MultiprocFinal(self, proc_interval=[], prediction_steps=0, proc_data=[], lock=0, proc_num=0):
		if prediction_steps == 0:
			print("database.MultiprocFinal argument, prediction_steps, cannot be 0")
			raise

		start = proc_interval[0]
		end = proc_interval[-1]
		start = start - (prediction_steps * self.data_increment)
		historical_data = self.historical_data.loc[start:end, :]
		new_data = historical_data.copy()
		for index, row in historical_data.iterrows():
			for col in historical_data.columns:

				if 'trend' in col:
					trend_index = index - (prediction_steps * self.data_increment)
					if trend_index in proc_interval:
						#this gathers all relevant points between current index and trend_index
						average_col =  col.replace('trend', 'average_price')
						is_nan_col = col.replace('trend', 'is_nan')
						data = {'y_values': list(historical_data.loc[trend_index:index, average_col]),
								'is_nan': list(historical_data.loc[trend_index:index, is_nan_col])}
						trend_data = pd.DataFrame(data)
						#this drops all rows where is_nan == 1 
						trend_data = trend_data[trend_data.is_nan == 0]#drops all is_nan==1 rows

						n = len(trend_data.index)
						data_density = n / prediction_steps
						if data_density < .1:
							new_data.at[trend_index, col] = np.nan
							data_density = n / prediction_steps
							#print(f'{data_density}%')
							continue

						x_values = np.array(trend_data.index)
						y_values = np.array(trend_data['y_values'])
						#components
						x_mean = np.mean(x_values, dtype=np.float64)
						y_mean = np.mean(y_values, dtype=np.float64)
						x_sum = np.sum(x_values)
						y_sum = np.sum(y_values)
						xy_sum = np.sum((x_values*y_values))
						x_sqr_sum = np.sum((x_values**2))
						x_sum_sqr = np.sum(x_values) ** 2
						#slope
						m = (xy_sum - (x_sum*y_sum)/n)/(x_sqr_sum - x_sum_sqr/n)
						new_data.at[trend_index, col] = m
		proc_data[proc_num] = new_data


	def __AddTrainingIndex(self, exchange_id, prediction_steps, currencies):
		'''
		This function adds an index_item to training_index based on given parameters
		parameters examples:
		- exchange_id = 'KRAKEN'
		- prediction_steps = 1
		- currencies = ['BTC', 'ETH']

		training_index format: 

		[
			"KRAKEN_USD_1_BTC_ETH.csv" : {
				"filepath" : "database/training_data/KRAKEN/KRAKEN_USD_1_BTC_ETH.csv",
				"exchange_id" : "KRAKEN"
				"asset_id_quote" : "USD",
				"prediction_steps" : 1,
				"currencies" : {
					"BTC_0" : "KRAKEN_SPOT_BTC_USD.csv", (order of currencies in neural net output left to right)
					"ETH_1" : "KRAKEN_SPOT_ETH_USD.csv"
				}
				"density" : {
					timestamp : 0.2345, (1 is no missing data, 0 is no data)
					(timestamp + 3months) : 0.6970,
					...
				},
				"datapoints" : 324425, (only counts data with no missing data)
				"data_start" : timestamp,
				"data_end" : timestamp
			}	
		] 
		'''
		#the surface level keys associated with training_data
		#if training_index_keys are changed,
		# 					the if statements below must be as well
		self.training_index_keys = ['filepath',
									'exchange_id',
									'asset_id_quote',
									'prediction_steps',
									'currencies',
									'density',
									'datapoints',
									'data_start',
									'data_end']

		if exchange_id not in self.config['tracked_exchanges']:
			print(f"{exchange_id} not in self.config['tracked_exchanges'], database.__AddTrainingIndex()")
			raise

		currency_string = ''
		formatted_currencies = {}
		order_num = 0
		for coin in currencies:
			#Currency Code
			in_tracked = False
			for tracked_coin in self.config['tracked_crypto']:
				if coin == tracked_coin:
					in_tracked = True

			if in_tracked == True and coin not in currency_string:
				if currency_string == '':
					currency_string += coin
				else:
					currency_string += f'_{coin}'
			else:
				raise

			#formatted_currencies code, finds all needed historical data filenames
			for filename, index_item in self.historical_index.items():
				if index_item['asset_id_base'] == coin and index_item['exchange_id'] == exchange_id:
					key = f"{coin}_{order_num}"
					formatted_currencies.update({key: filename})
					order_num += 1

		asset_id_quote = self.config['asset_id_quote']
		#ex: filename == "KRAKEN_USD_1_BTC_ETH.csv"
		filename = f"{exchange_id}_{asset_id_quote}_{prediction_steps}_{currency_string}.csv"
		filepath = self.training_base_path+f'{exchange_id}/{filename}'

		index_item = {}
		arbitrary_date = self.SetUnixToDate(86500)#doesnt crash at any timezone
		for key in self.training_index_keys:
			if key == 'filepath':
				index_item.update({key: filepath})
			if key == 'exchange_id':
				index_item.update({key: exchange_id})
			if key == 'asset_id_quote':
				index_item.update({key: self.config['asset_id_quote']})
			if key == 'prediction_steps':
				index_item.update({key: prediction_steps})
			if key == 'currencies':
				index_item.update({key: formatted_currencies})
			if key == 'density':
				index_item.update({key: {}})
			if key == 'datapoints':
				index_item.update({key: 0})
			if key == 'data_start' or key == 'data_end':
				index_item.update({key: arbitrary_date})

		self.training_index.update({filename: index_item})

		self.UpdateTrainingIndex()

		return filename
