
import json
import os

import time
import datetime

import database.coin_api as coin_api

import pandas as pd

class Database():
	def __init__(self):
		self.coin_api = coin_api.CoinAPI()
		self.historical_base_path = "database/historical_data/"
		self.historical_index_path = f"{self.historical_base_path}historical_index.json"
		self.training_base_path = "database/training_data/"
		self.training_index_path = f"{self.training_base_path}training_index.json"
		self.handbook_path = f'{self.historical_base_path}handbook.json'
		self.config_path = 'database/config.json'
		self.data_interval = 300

		missing_handbook_data = False
		with open(self.handbook_path) as file:
			self.handbook = json.load(file)
			try:
				self.exchange_handbook = self.handbook['exchange_data']
				self.period_handbook = self.handbook['period_data']
			except:
				missing_handbook_data = True
				print('missing handbook.json data')

		with open(self.config_path) as file:
			self.config = json.load(file)
		

		if ((self.config['last_update'] + self.config['update_frequency']) < time.time() 
			or self.config['update_limiter'] == False or missing_handbook_data == True):
			print('Updating handbook.json...')
			self.UpdateHandbook()
		else:
			print('handbook.json up to date, next update after', 
				 self.SetUnixToDate(self.config['last_update'] + self.config['update_frequency'] - 36000), "HST")

		self.BackfillHistoricalData()
		self.UpdateTrainingData()




	def SetUnixToDate(self, unix):#input unix time as string or int
		#when using to display on screen, add to UTC unix param to offset for your timezone
		return datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S.%f0Z')
		#RETURNS UTC, confirmed

	def SetDateToUnix(self, date):
		unix = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f0Z')
		unix = unix.timestamp() - 36000#sets it to UTC
		return unix
		

	def UpdateHandbook(self):
		exchanges_response = self.coin_api.MakeRequest(url_ext=self.config['exchanges_url_ext'], 
									filters={'exchange_id': self.config['tracked_exchanges'],
											 'asset_id_quote': self.config['asset_id_quote']},
											 return_type='json')

		periods_response = self.coin_api.MakeRequest(url_ext=self.config['periods_url_ext'],
									filters={'length_seconds': 0}, omit_filtered=True, return_type='json')

		#filters out irrelevant exchange data, only keeps whats specified in relevant_data_keys
		extracted_data = {}
		for tracked_exchange in self.config['tracked_exchanges']:
			extracted_data.update({tracked_exchange : []})

		relevant_data_keys = ['symbol_id', 'symbol_type', 'asset_id_base', 'asset_id_quote', 'data_start', 'data_end']
		for item in exchanges_response:
			for exchange_id, exchange_data in extracted_data.items():
				if exchange_id == item['exchange_id']:
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

		exchange_response = extracted_data
		#END OF EXCHANGE_DATAD EXTRACTION

		updated_handbook = {}
		updated_handbook.update({'period_data' : periods_response})
		updated_handbook.update({'exchange_data' : exchange_response})

		self.handbook = updated_handbook
		with open(self.handbook_path, 'w') as file:
			json.dump(self.handbook, file, indent=4)

		self.config['last_update'] = time.time()
		self.exchange_handbook = self.handbook['exchange_data']
		self.period_handbook = self.handbook['period_data']

		#handbook_json = json.dumps(self.handbook, indent=4, separators=(',', ': '))
		with open(self.config_path, 'w') as file:
			json.dump(self.config, file, indent=4)
		print("Finished: handbook.json up to date, next update after",
				self.SetUnixToDate(self.config['last_update'] + self.config['update_frequency'] - 36000), "HST")


	def UpdateHistoricalIndex(self):
		#updates historical_data/historical_index.json file with self.historical_index
		with open(self.historical_index_path, 'w') as file:
				#when it is in the file, it will not have the "exchange_id" dictionary layer
				json.dump(self.historical_index, file, indent=4)


	def __InitHistoricalDir(self):

		'''
		The following looks at all tracked exchanges and crypto-coins in config and filters through
		handbook to find matches in config data. If any are found and there is no existing dir for 
		that currency pair from specified exchange (ex: BTC in USD on KRAKEN | symbol_id = KRAKEN_SPOT_BTC_USD)\

		Since handbook.json only has tracked exchanges on the specified fiat/asset_id_quote, we can skip searching 
		for those and instead cycle through self.exchange_handbook (exchange_handbook shows all historical data 
		available from coinapi for tracked exchanges at specified reference fiat (USD), handbook update frequency 
		set in config.json)
		'''

		self.historical_index = {}
		#if you change historical_index_keys, you must change if statments accordingly below
		self.historical_index_keys = ['filepath',
								'symbol_id',
								'exchange_id',
								'symbol_type',
								'asset_id_base',
								'asset_id_quote',
								'datapoints',
								'data_start',
								'data_end']

		#checks for self.historical_index_path defined in database.__init__()
		#creates file if not found
		if os.path.exists(self.historical_index_path) == True:
			#if file is found, it loads its contents
			with open(self.historical_index_path, 'r') as file:
				index = json.load(file)
				self.historical_index.update(index)
		else:
			#if no file is found it creates one
			open(self.historical_index_path, 'w')
			index = {}
			self.historical_index.update(index)


		#looks through all tracked exchanges in self.exchange_handbook 
		#(exchange_handbook == handbook['exchange_data'])
		for exchange_id, exchange_data in self.exchange_handbook.items():
			#following uses coin_api function to filter through exchange contents by specified filter.
			#contents of self.exchange_handbook are already filtered by asset_id_quote & tracked_exchanges
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
		for item in self.period_handbook:
			if item['length_seconds'] == unix:
				return item['period_id']
		print('Error: period_id not found for unix_time value:', unix)
		return ''

	def BackfillHistoricalData(self):
		self.__InitHistoricalDir()

		#the current version only supports 'balanced' backfilling of data
		#in other words it updates all currencies in all exchanges evenly and at the same time
		if self.config['backfill_historical_data'] == True:
			print('----------------------------------------------------')
			print('Backfilling Historical Data')
			print('----------------------------------------------------')

			#the following finds the total number of backfilling request we are making
			#it then finds the limit on each request needed to use all remaining api requests
			#so that only one iteration is needed
			#
			#It also provides the next part of the algorithm with all the index_items from 
			#self.historical_index.items() that are needed via backfill_index.
			backfill_index = {}
			print('Backfill List:')
			for filename, index_item in self.historical_index.items():
				print('   ', filename)
				backfill_index.update({filename: index_item})

			backfill_count = len(backfill_index)
			print(f'{backfill_count} total requests\n')

			#calculate number of datapoints each backfill_item needs to request to max out available api_requests
			#available with one iteration
			limit_per_request = int(self.coin_api.api_index['startup_key']['limit'] / backfill_count * 100 * 0.985)
			limit_per_request = limit_per_request - (limit_per_request % 100)
			#limit_per_request = 100
			#one request is 100 datapoints so limit_per_request is made a multiple of 100
			#because of this it rounds to the nearest 100 in order to maximize data given per api request used

			#the following goes through each item within backfill_index
			#the key for each index_item's index is the filename
			for filename, index_item in backfill_index.items():

				#settings for the historical data requests
				url_ext = self.config['historical_url_ext'].format(index_item['symbol_id'])
				queries = {'time_start': index_item['data_end'],
						   'limit': limit_per_request,
						   'period_id': self.FindPeriodId(self.data_interval)}

				print(queries)

				#no filter, the default request size is 100 (100 datapoints: uses one request)
				response = self.coin_api.MakeRequest(url_ext=url_ext, queries=queries, api_key_id='startup_key')

				#puts response into an array and adds it to existing data for current index_item
				response_data = pd.DataFrame.from_dict(response, orient='columns')

				#==============================================================
				#SET DATES TO UNIX
				#==============================================================
				prev_time = time.time()
				start_time = time.time()
				new_df = response_data.copy()

				print('changing time values to unix')
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
				#VERIFY CONTINUITY OF UNIX TIME CONVERSION
				#==============================================================
				print('verifying unix dates')

				#timestamp = arbitrary unix number to test date-unix conversion
				timestamp = 1000000
				new_timestamp = self.SetUnixToDate(timestamp)
				new_timestamp = self.SetDateToUnix(new_timestamp)
				print(f'timestamp convertion test: {timestamp} || {new_timestamp}')

				#the following goes back and converters the unix time back to date in memory 
				#and compares to original request data
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


				#loads existing data if any
				try:
					existing_data = pd.read_csv(index_item['filepath'])
					existing_data = existing_data.append(response_data, ignore_index=True, sort=False)
				except(pd.errors.EmptyDataError):
					print('No existing data for:', index_item['filepath'])
					print('Creating New Dataframe')
					existing_data = response_data

				existing_data.to_csv(index_item['filepath'], index=False)

				#update datapoints value for this item
				index_item['datapoints'] = len(existing_data.index)

				print(filename, 'updated to: ', self.SetUnixToDate(existing_data.iloc[-1]['time_period_end']))
				print('----------------------------------------------------')

				#update currency index for current index_item
				#ONLY CHANGE TIME_END
				index_item['data_end'] = self.SetUnixToDate(existing_data.iloc[-1]['time_period_end'])


				#This updates self.historical_index['symbol_id.csv'] (symbol_id.csv = filename) with index_item
				self.historical_index[filename] = index_item
				#print(self.historical_index)

				self.UpdateHistoricalIndex()
		else:
			print('database.config[\'backfill_historical_data\'] = false: not updating historical data')



	def UpdateTrainingIndex(self):
		#updates historical_data/training_index.json file with self.training_index
		with open(self.training_index_path, 'w') as file:
			#when it is in the file, it will not have the "exchange_id" dictionary layer
			json.dump(self.training_index, file, indent=4)
		
	def __InitTrainingDir(self):
		'''
		This function is similar to self.__InitHistoricalDir in that it only updates 
		currencies for each exchange being tracked as defined within config.json.
		'''

		#if you change training_index_keys, you must change the "if statments below accordingly
		self.training_index = {}
		self.training_index_keys = ['filepath',
								'symbol_id',
								'exchange_id',
								'symbol_type',
								'asset_id_base',
								'asset_id_quote',
								'datapoints',
								'data_start',
								'data_end']

		#checks for training_data/(exchange_id), creates dir if not found
		#since non-tracked data is not deleted they should already have directories
		#because of this we only need to worry about tracked assets in self.config
		for exchange_id in self.config['tracked_exchanges']:
			exchange_path = self.training_base_path+f"{exchange_id}"
			if os.path.isdir(exchange_path) == False:
				os.mkdir(exchange_path)


		#this adds elements to training_data according to elements in tracked_crypto
		#that are also in historical_index
		for filename, index_item in self.historical_index.items():

			if (index_item['exchange_id'] in self.config['tracked_exchanges'] and
				index_item['asset_id_base'] in self.config['tracked_crypto']):

				coin_data_path = self.training_base_path+index_item['exchange_id']+f"/{filename}"
				#checks for training_data/{exchange_id}/{filename}.csv, creates file if not found
				if os.path.exists(coin_data_path) == False:
					open(coin_data_path, 'w')

					coin_data = {filename: {}}
					for key in self.training_index_keys:
						if key == 'filepath':
							coin_data[filename].update({key: coin_data_path})
						elif key == 'exchange_id':
							coin_data[filename].update({key: index_item[key]})
						elif key == 'symbol_id':
							coin_data[filename].update({key: index_item[key]})
						elif key == 'symbol_type':
							coin_data[filename].update({key: index_item[key]})
						elif key == 'asset_id_base':
							coin_data[filename].update({key: index_item[key]})
						elif key == 'asset_id_quote':
							coin_data[filename].update({key: index_item[key]})
						elif key == 'datapoints':
							coin_data[filename].update({key: 0})
						elif key == 'data_start':
							coin_data[filename].update({key: index_item['data_start']})
						elif key == 'data_end':
							coin_data[filename].update({key: index_item['data_start']})

					self.training_index.update(coin_data)


		#checks for training_index.json, creates file if not found
		#this will overwrite any existing data in memory with the correct self.training_index data
		if os.path.exists(self.training_index_path) == True:
			#if file is found, it loads its contents
			with open(self.training_index_path, 'r') as file:
				index = json.load(file)
				self.training_index.update(index)
		else:
			#if no file is found it creates one
			open(self.training_index_path, 'w')
			index = {}
			self.training_index.update(index)

		self.UpdateTrainingIndex()

	def UpdateTrainingData(self):
		#this function processes historical_data so that no further data processing is required for the 
		#network to run effectively. The only thing left to do after is set the index and drop unneccesary columns

		'''
		Since many datapoints are missing in early parts of historical_data, the program will likely need to omit
		the beginning of that data until the frequency of missing points is below a specified threshold. 
		When updating the training_index, this function will change data_end according to the latest historical
		datapoint it saw even if no data was actually saved to a training_data folder (due to missing datapoints).
		In order to track how many datapoints we have to train from, I have added a 'datapoints' item to index for
		each training_index item to track exactly how much reliable data we have to train from. It will also update
		data_start to be in accordance with first training_data datapoint and not with first historical_data datapoint.
		If no data is present, data_start will continue to equal data_end.
		'''


		self.__InitTrainingDir()


		if self.config['update_training_data'] == True:


			print('----------------------------------------------------')
			print('Updating Training Data')
			print('----------------------------------------------------')

			#the following appends all symbol_id's that are going to be updated
			update_index = {}
			print('Update List:')
			for filename, index_item in self.training_index.items():
				print('      ', filename)

				training_data_end = self.SetDateToUnix(index_item['data_end'])
				historical_data_end = self.SetDateToUnix(self.historical_index[filename]['data_end'])

				#the following if statements compare training data_end with the historical data_end
				#
				#since training data works directly from the local database of historical data
				#it should only ever be less than or equal to historical data in regards to the data_end
				if training_data_end < historical_data_end:
					update_index.update({filename: index_item})

				if training_data_end > historical_data_end:
					#Obviously training_data should not be ahead of historical_data, this flags that
					raise TypeError(f"Error: training_data is ahead of historical_data for {filename} ['data_end']")

				if training_data_end == historical_data_end:
					print(f'{filename} is up to date with historical_data, data_end:', index_item['data_end'])

			update_count = len(update_index)
			print(f'{update_count} total requests\n')



			'''
			There are many ways to interpret the data for training so it does not seem 
			worthwhile to create a structure in which all variations are accounted for.
			Because of this, training_data within database will only provide preprocessing
			is shared between all variations in the data that will be used.

			Preprocessing:
			 1. converts market value of cryptocurrency to a slope value that is calculated
			 	finding the difference between point x in relation to point x-1 and getting 
			 	the percent change. (ex: if f(x-1)=2 and f(x)=1 then f(x)=-0.5)
			 2. 
			'''

			for filename, index_item in update_index.items():

				print(f"Updating {filename}")
				historical_start = self.historical_index[filename]['data_start']
				historical_end = self.historical_index[filename]['data_end']
				print(f"Interval: [{historical_start}, {historical_end}]")

				#All items in update_index are not up to date:
				#	training_item['data_end'] < historical_item['data_end']

				#loads the historical_data of the same filename as current update_index item
				#(training_index and historical_index filenames are identical for the same symbol_id)
				historical_path = self.historical_index[filename]['filepath']
				historical_data = pd.read_csv(historical_path)


				#The following iterates through historical_data starting at index_item['data_end']
				# until historical_data['data_end']. Since the market data is being converted to 
				# slope values (secant slope calculated between adjacent points). If there is a missing point,
				# the next datapoint will not be able to calculate the proper slope since the 
				# previous point does not exist. If this happens that next point will be assigned NaN on
				# all market data values (high, low, open, close). It can be thought of as a flag for missing data
				new_data = historical_data.copy()
				init_time = time.time()
				previous_time = init_time
				delay = 0
				for index, row in historical_data.iterrows():
					if row['time_period_start'] >= self.SetDateToUnix(index_item['data_end']):
						for col in historical_data.columns:

							#this part is exclusively for cryptocurrency market value, hence 'price'
							if 'price' in col:
								#if it is the first item there is no x-1 value so x=NaN
								if index == 0:
									new_data.at[index, col] = float('NaN')
								elif (abs(historical_data.at[index-1, 'time_period_start'] - row['time_period_start']) 
																								== self.data_interval):
									new_data.at[index, col] = row[col] / historical_data.at[index-1, col] - 1
								else:
									new_data.at[index, col] = float('NaN')

						if index % 20000 == 0 and index != 0:
							delay = time.time() - previous_time
							previous_time = delay + previous_time
							print(f"index: {index} || delay: {delay}")


				#This overwrites all new data to corresponding .csv file and updates index
				new_data.to_csv(index_item['filepath'], index=False)

				#update datapoints value for this item
				index_item['datapoints'] = len(new_data.index)
				index_item['data_end'] = self.SetUnixToDate(new_data.iloc[-1]['time_period_end'])


				print(f"{filename} Update Duration:", (time.time() - init_time))
				print(f"{filename} up to date with historical_data at:", index_item['data_end'])
				print('----------------------------------------------------')


				#This updates self.training_index['symbol_id.csv'] (symbol_id.csv = filename) with index_item
				self.training_index[filename] = index_item

				self.UpdateTrainingIndex()
				
		else:
			print('database.config[\'update_training_data\'] = false: not updating training data')