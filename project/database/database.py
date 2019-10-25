
import json
import os

import time
import datetime

import database.coin_api as coin_api

import pandas as pd
import numpy as np

class Database():
	def __init__(self):
		print('----------------------------------------------------')
		print('Initializing Program')
		print('----------------------------------------------------')
		self.coin_api = coin_api.CoinAPI()
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
		print('Request Made For Training Data, max_filler_gap does nothing')
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
		- max_filler_gap (maximum number of data fills in a row, this is because it loses accuracy
																					larger the gap)
		- exchange_id ('KRAKEN')
		- currencies (['BTC', 'ETH']) #order does not matter
		'''

		#Default Kwargs
		if 'max_filler_gap' not in kwargs:
			kwargs['max_filler_gap'] = 1
		if 'exchange_id' not in kwargs:
			kwargs['exchange_id'] = 'KRAKEN'
		if 'currencies' not in kwargs:
			kwargs['currencies'] = ['BTC', 'ETH']

		print(f"Query Parameters:")
		print(" - max_filler_gap =", kwargs['max_filler_gap'])
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

				#max_filler_gap
				if kwargs['max_filler_gap'] != index_item['max_filler_gap']:
					continue;

				matched_filename = filename
				break;


		dataset = pd.DataFrame()
		dataset_index = {}

		#generates new index if one wasn't found above
		if matched_filename == '':
			matched_filename = self.__AddTrainingIndex(kwargs['exchange_id'],
													   kwargs['max_filler_gap'],
													   kwargs['currencies'])

		self.__LoadTrainingData(matched_filename)


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
						'is_nan']
						#if this is changed, a training_data reset is required

		#Goes through currencies and loads historical data into historical_data var
		#index_item['currencies'] format example:
		#"currencies:" : {
		#	"BTC_0" : "KRAKEN_SPOT_BTC_USD.csv",
		#	"ETH_1" : "KRAKEN_SPOT_ETH_USD.csv"						
		#}
		historical_data = {}
		#this verifies that all currencies are being tracked
		for key, filename in index_item['currencies'].items():
			match = False
			for tracked_currency in self.config['tracked_crypto']:
				if tracked_currency in filename:
					match = True

			if match == True:
				#creates a dictionary of historical_data using coin name (ex: {"BTC": bitcoin_data, ...})
				historical_data.update({key: self.LoadHistoricalData(filename)})
			else:
				print(f"Untracked currency in {filename}")
				raise

		#creates currency key list IN ORDER OF CURRENCIES, NETWORK WILL FAIL WITHOUT ORDER
		#The second loop is needed to make sure each item is in order
		#The currency key list gives us accurate, in-order calling of historical_data
		currency_order = []
		for order_num in range(0, len(historical_data)):
			for key, dataset in historical_data.items():
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
			historical_data[coin].time_period_start = historical_data[coin].time_period_start.astype(int)
			
			#sets the index to the time_period_start column and drops time_period_start
			historical_data[coin] = historical_data[coin].set_index('time_period_start', drop=False)

			#adds used_columns to historical_data if not already included
			for col in used_columns:
				if col not in historical_data[coin].columns:
					historical_data[coin][col] = np.nan
			
			#this drops all unused columns in local historical_data variable
			# so that training_data does not have it
			drop_columns = []
			for col in historical_data[coin].columns:
				if col not in used_columns:
					drop_columns.append(col)
			historical_data[coin] = historical_data[coin].drop(columns=drop_columns)

			#renames columns in local historical_data variable to match training_data
			new_columns = {}
			for col in historical_data[coin].columns:
				new_columns.update({col: f"{coin}|{col}"})
			historical_data[coin] = historical_data[coin].rename(columns=new_columns)

			for col in historical_data[coin].columns:
				#BEFORE adding historical_data to new_data, this sets all historical_data is_nan to False (0)
				#Additionally, all new_data is_nan is set to True (1)
				#That way, when merged, new_data will start with False and only datapoints 
				#  with data will be set to True
				if 'is_nan' in col:
					new_data[col] = 1 #True, is_nan
					historical_data[coin][col] = 0 #False, not is_nan

				#adds values to new_data from historical_data
				new_data.loc[:, col] = historical_data[coin].loc[:, col]


		#historical_data becomes a copy of new_data without the preproccessing changes
		historical_data = new_data.copy()

		print(new_data.head(20))

		#used to calculate the density
		prev_density_date = start_time
		#used to calculate time delay between iterations of following loop
		init_time = time.time()
		previous_time = init_time
		#used to calculate sec value of previous index against current one (price col)
		prev_index = 0

		count = 0
		for index, row in new_data.iterrows():
			if index >= self.SetDateToUnix(index_item['data_end']):#only iterates on new data

				for col in new_data.columns:

					if 'is_nan' in col:
						if np.isnan(row[col]):
							new_data.at[index, col] = 1 #is_nan = true
					elif 'price' in col:
						if np.isnan(row[col]):
							new_data.at[index, col] = 0
					'''if 'price' in col:
						if index == start_time:
							new_data.at[index, col] = 0
						elif prev_index == index - self.data_increment:
							new_data.at[index, col] = row[col] / historical_data.at[prev_index, col] - 1
					else:
						new_data.at[index, col] = row[col]'''

			if count % 20000 == 0 and count != 0:
				current_density_date = index
				density = 20000 * self.data_increment / (current_density_date - prev_density_date)
				density = int(density * 100) #to get density, it divides the number of points there are
				prev_density_date = current_density_date
				# in a given time frame by how many there should be in the same interval and multiplies 
				# by 100 to have a maximum 100 (no missing points) and a minimum of 0 (no data)
				delay = int(time.time() - previous_time)
				previous_time = delay + previous_time
				date = self.SetUnixToDate(index)
				print(f"date: {date} || delay: {delay} || density: {density}")

			prev_index = index
			count += 1

		print(new_data.head(50))

		#updates local index variable on new data
		index_item['datapoints'] = total_datapoints
		index_item['data_start'] = self.SetUnixToDate(start_time)
		index_item['data_end'] = self.SetUnixToDate(end_time)

		#updates training_index with newly updated local index_item data
		# and saves it to file
		self.training_index[filename_param] = index_item
		self.UpdateTrainingIndex()

		#This saves new_data to the f"{symbol_id}.csv" file
		new_data.to_csv(index_item['filepath'], index=False)

		return new_data



	def __AddTrainingIndex(self, exchange_id, max_filler_gap, currencies):
		'''
		This function adds an index_item to training_index based on given parameters
		parameters examples:
		- exchange_id = 'KRAKEN'
		- max_filler_gap = 1
		- currencies = ['BTC', 'ETH']

		training_index format: 

		[
			"KRAKEN_USD_1_BTC_ETH.csv" : {
				"filepath" : "database/training_data/KRAKEN/KRAKEN_USD_1_BTC_ETH.csv",
				"exchange_id" : "KRAKEN"
				"asset_id_quote" : "USD",
				"max_filler_gap" : 1,
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
									'max_filler_gap',
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
		filename = f"{exchange_id}_{asset_id_quote}_{max_filler_gap}_{currency_string}.csv"
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
			if key == 'max_filler_gap':
				index_item.update({key: max_filler_gap})
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


	
'''
	def UpdateTrainingData(self):

		
		There are many ways to interpret the data for training so it does not seem 
		worthwhile to create a structure in which all variations are accounted for.
		Because of this, training_data within database will only provide preprocessing
		that is shared between all variations in the data that will be used. Beyond that,
		further developement will need to be done in order to have variable style of
		preprocessing within the database class.

		Preprocessing:
		 1. converts market prices of cryptocurrency to a slope value that is calculated
		 	finding the difference between point x in relation to point x-1 and getting 
		 	the percent change with zero as the origin. 
		 	(ex: if f(x-1)=2 and f(x)=1 then f'(x)=(1/2-1)=-0.5 [not actually a derivative])
		 2. data averaging across gaps in the historical_data. This done by getting the 
			average of adjecent known datapoints that are no more than max_filler_gap 
			timesteps apart (larger gaps produce less reliable filler data)
		 	(ex: If f(x-1)=4 and f(x+1)=6, approximate f(x))
		 		f(x)=(6+4)/2
		 		f(x)=5
		

		self.__InitTrainingDir()

		if self.config['update_training_data'] == True:

			print('----------------------------------------------------')
			print('Updating Training Data')
			#overwrite_training_data == True simply means that if any difference in
			# data_end is found between training_data and historical_data. the training_data
			# is conmpletely re-generated for that f"{symbol_id}.csv
			if self.config['overwrite_training_data'] == True:
				print('self.config[\'overwrite_training_data\'] = True')
			else:
				print('self.config[\'overwrite_training_data\'] = False')
			print('----------------------------------------------------')

			#the following appends all f"{symbol_id}.csv" filenames that are going to be updated
			update_list = {}
			print('Update List:')
			for filename, update_item in self.training_index.items():
				print('      ', filename)

				#"unix" is the unix time variant and "date" refers to it being in the datetime format
				historical_unix_end = self.SetDateToUnix(self.historical_index[filename]['data_end'])#unix time
				historical_date_start = self.historical_index[filename]['data_start']#datetime

				#This if statement will delete existing data for self.training_index[filename]
				# if self.config['overwrite_training_data'] == True. Hence 'overwrite_training_data'
				if self.config['overwrite_training_data']:
					open(update_item['filepath'], 'w').close()
					self.training_index[filename]['datapoints'] = 0
					self.training_index[filename]['data_start'] = historical_date_start
					self.training_index[filename]['data_end'] = historical_date_start
					update_item = self.training_index[filename]#need this to update loop value for following code
					self.UpdateTrainingIndex()

				training_unix_end = self.SetDateToUnix(update_item['data_end'])#unix time
				#this needs to be declared after the overwrite_training_data if statement

				#The following "if" statements compare training_data['data_end'] with the historical_data['data_end'].
				#Since training_data works directly from the local database of historical_data
				# it should only ever be less than or equal to historical data in regards to the data_end
				if training_unix_end < historical_unix_end:
					update_list.update({filename: update_item})
				elif training_unix_end > historical_unix_end:
					#Obviously training_data should not be ahead of historical_data
					raise TypeError(f"Error: training_data is ahead of historical_data for {filename} ['data_end']")
				elif training_unix_end == historical_unix_end:
					print(f'{filename} is up to date with historical_data, data_end:', update_item['data_end'], "UTC")

			#number of items in update_list
			update_count = len(update_list)
			print(f'{update_count} total requests\n')

			#==============================================================
			#TRAINING DATA PREPROCESSING BEGINS
			#==============================================================

			for filename, update_item in update_list.items():

				print(f"Updating {filename}")
				historical_start = self.historical_index[filename]['data_start']
				historical_end = self.historical_index[filename]['data_end']
				print(f"Interval: [{historical_start}, {historical_end}]")


				#Loads the historical_data of the same filename as current update_list item
				# (training_index and historical_index filenames are identical for the same symbol_id)
				historical_path = self.historical_index[filename]['filepath']
				historical_data = pd.read_csv(historical_path)

				#converts time_period_start column (soon to be index) to int
				historical_data.time_period_start = historical_data.time_period_start.astype(int)

				#sets the index to the time_period_start column
				historical_data = historical_data.set_index('time_period_start', drop=False)

				#this drops all unused columns in local historical_data variable
				# so that training_data does not "contract it"
				historical_data = historical_data.drop(columns=['time_close', 'time_open'])

				
				The following iterates through historical_data starting at update_item['data_end']
				until historical_data['data_end']. Since the market prices are being converted to 
				slope values (secant slope calculated between adjacent points). If there is a missing point,
				the next datapoint will not be able to calculate the proper slope since there is a dependecy. 
				If this happens that next point will be assigned NaN on all market price values (high, low, open, close). 
				It can be thought of as a flag for gaps in the data.
				

				#New_data is declared with the same columns as historical_data
				# but has a NaN value for each cell at initialization. The index
				# count is also made to reflect the total number of timesteps
				# independent of any missing data.
				historical_data_start = self.SetDateToUnix(self.historical_index[filename]['data_start'])
				historical_data_end = self.SetDateToUnix(self.historical_index[filename]['data_end'])
				total_datapoints = int((historical_data_end - historical_data_start) / self.data_increment)

				#init_index is a list with length total_datapoints
				#Initializing the new_data with values increases compute time
				# by several orders of magnitude because all the memory addresses 
				# needed for the list have been registered before the loop rather
				# than during each iteration of it.
				init_index = []
				for x in range(total_datapoints):
					time_increment = int(x * self.data_increment + historical_data_start)
					init_index.append(time_increment)
				new_data = pd.DataFrame(columns=historical_data.columns, index=init_index)
				new_data['time_period_start'] = init_index

				init_time = time.time()
				previous_time = init_time

				#used to calculate the density
				prev_density_date = historical_data_start
				delay = 0
				missing_rows = 0

				prev_index = 0
				count = 0

				total_columns = len(historical_data.columns)
				for index, row in historical_data.iterrows():
					if index >= self.SetDateToUnix(update_item['data_end']):

						for col in historical_data.columns:

							if 'price' in col:
								if index == historical_data_start:
									pass
								elif prev_index == index - self.data_increment and prev_index != 0:
									prev_index = index - self.data_increment
									new_data.at[index, col] = row[col] / historical_data.at[prev_index, col] - 1
							else:
								new_data.at[index, col] = row[col]


					if count % 20000 == 0 and count != 0:
						current_density_date = index
						density = 20000 * self.data_increment / (current_density_date - prev_density_date)
						density = density * 100 #to get density, it divides the number of points there are
						prev_density_date = current_density_date
						# in a given time frame by how many there should be in the same interval and multiplies 
						# by 100 to have a maximum 100 (perfect) and a minimum of 0 
						#(just approaches zero if data is missing)
						delay = time.time() - previous_time
						previous_time = delay + previous_time
						date = self.SetUnixToDate(index)
						print(f"date: {date} || delay: {delay} || density: {density}")

					prev_index = index
					count += 1

				#This saves new_data to the f"{symbol_id}.csv" file
				new_data.to_csv(update_item['filepath'], index=False)

				#Updates datapoints and data_end values in update_item
				update_item['datapoints'] = len(new_data.index)
				update_item['data_end'] = self.SetUnixToDate(new_data['time_period_end'].tail(1))


				print(f"{filename} Update Duration:", (time.time() - init_time))
				print(f"{filename} up to date with historical_data at:", update_item['data_end'], "UTC")
				print('----------------------------------------------------')


				#The update_item (which now has the most recent changes) is saved to self.training_index
				self.training_index[filename] = update_item
				self.UpdateTrainingIndex()
				
		else:
			print('database.config[\'update_training_data\'] = false: not updating training data')
		'''