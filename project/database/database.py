
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
				self.handbook['excahnge_data']
			except:
				print(f'self.handbook_data failed to load, resetting...')
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
			#limit_per_request = 100

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

				print(filename, 'updated to: ', self.SetUnixToDate(existing_data.iloc[-1]['time_period_end']))
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


	def LoadTrainingData(self, filename):
		return pd.read_csv(self.training_index[filename]['filepath'])


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

		#if you change training_index_keys, you must change the "if" statments below accordingly
		self.training_index = {}
		#self.training_index_keys does not have to equal self.historical_index_keys
		self.training_index_keys = ['filepath',
								'symbol_id',
								'exchange_id',
								'symbol_type',
								'asset_id_base',
								'asset_id_quote',
								'datapoints',
								'data_start',
								'data_end']

		#For loop checks for training_data/(exchange_id), creates dir if not found.
		#Since non-tracked data is not deleted they should already have directories.
		#This means program only needs to generate tracked data outlined in config.json
		for exchange_id in self.config['tracked_exchanges']:
			exchange_path = self.training_base_path+f"{exchange_id}"
			if os.path.isdir(exchange_path) == False:
				os.mkdir(exchange_path)


		#This adds goes through all tracked currencies and initializes and index 
		# if one is not found
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


		#Checks for training_index.json, creates file if not found
		#The training_index file data will overwrite the newly initialized
		# self.training_index dictionary if it exists
		if os.path.exists(self.training_index_path) == True:
			#if file is found, it loads its contents
			with open(self.training_index_path, 'r') as file:
				index = json.load(file)
				self.training_index.update(index)
		else:
			#if no file is found it creates a new one and saves self.training_index to it
			open(self.training_index_path, 'w')
			index = {}
			self.training_index.update(index)

		self.UpdateTrainingIndex()

	def UpdateTrainingData(self):

		'''
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
		'''

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
					print(f'{filename} is up to date with historical_data, data_end:', update_item['data_end'])

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

				'''
				The following iterates through historical_data starting at update_item['data_end']
				until historical_data['data_end']. Since the market prices are being converted to 
				slope values (secant slope calculated between adjacent points). If there is a missing point,
				the next datapoint will not be able to calculate the proper slope since there is a dependecy. 
				If this happens that next point will be assigned NaN on all market price values (high, low, open, close). 
				It can be thought of as a flag for gaps in the data.
				'''

				#New_data is declared as a copy of historical_data.
				#That way historical_data can be used as a reference
				new_data = historical_data.copy()

				init_time = time.time()
				previous_time = init_time
				delay = 0
				for index, row in historical_data.iterrows():
					if row['time_period_start'] >= self.SetDateToUnix(update_item['data_end']):
						for col in historical_data.columns:

							#this part is exclusively for cryptocurrency market price, hence 'price'
							if 'price' in col:
								#if it is the first item there is no x-1 value so x=NaN
								if index == 0:
									new_data.at[index, col] = 0#float('NaN')
								elif (abs(historical_data.at[index-1, 'time_period_start'] - row['time_period_start']) 
																								== self.data_increment):
									new_data.at[index, col] = row[col] / historical_data.at[index-1, col] - 1
								else:
									new_data.at[index, col] = 0#float('NaN')

					if index % 20000 == 0 and index != 0:
						density_start = historical_data.at[index-20000, 'time_period_start']
						density_end = historical_data.at[index, 'time_period_start']
						density = 20000 * self.data_increment / (density_end - density_start)
						density = density * 100 #to get density, it divides the number of points there are
						# in a given time frame by how many there should be in the same interval and multiplies 
						# by 100 to have a maximum 100 (perfect) and a minimum of 0 
						#(just approaches zero if data is missing)
						delay = time.time() - previous_time
						previous_time = delay + previous_time
						print(f"index: {index} || delay: {delay} || density: {density}")


				#This saves new_data to the f"{symbol_id}.csv" file
				new_data.to_csv(update_item['filepath'], index=False)

				#Updates datapoints and data_end values in update_item
				update_item['datapoints'] = len(new_data.index)
				update_item['data_end'] = self.SetUnixToDate(new_data.iloc[-1]['time_period_end'])


				print(f"{filename} Update Duration:", (time.time() - init_time))
				print(f"{filename} up to date with historical_data at:", update_item['data_end'])
				print('----------------------------------------------------')


				#The update_item (which now has the most recent changes) is saved to self.training_index
				self.training_index[filename] = update_item
				self.UpdateTrainingIndex()
				
		else:
			print('database.config[\'update_training_data\'] = false: not updating training data')