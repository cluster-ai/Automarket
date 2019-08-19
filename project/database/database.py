
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
		self.handbook_path = f'{self.historical_base_path}handbook.json'
		self.config_path = 'database/config.json'
		self.missing_data = False

		with open(self.handbook_path) as file:
			self.handbook = json.load(file)
			try:
				self.exchange_handbook = self.handbook['exchange_data']
				self.period_handbook = self.handbook['period_data']
			except:
				self.missing_data = True
				print('missing handbook.json data')

		with open(self.config_path) as file:
			self.config = json.load(file)
		

		if ((self.config['last_update'] + self.config['update_frequency']) < time.time() 
			or self.config['update_limiter'] == False or self.missing_data == True):
			print('Updating handbook.json...')
			self.UpdateHandbook()
		else:
			print('handbook.json up to date, next update after', 
				 self.SetUnixToDate(self.config['last_update'] + self.config['update_frequency'] - 36000), "HST")

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

	def ReloadHistoricalIndex(self):
		#only use this function to verify all exchange indexes (goes through all historical data)
		#it also clears out any indexes of files that no longer exist
		pass

	def UpdateHistoricalIndex(self):
		#use to update all (exchange_id)_index.json files with newest self.historical_index data
		for exchange_id, index_data in self.historical_index.items():
			index_file_path = self.historical_base_path+f"{exchange_id}/{exchange_id}_index.json"
			with open(index_file_path, 'w') as file:
				#when it is in the file, it will not have the "exchange_id" dictionary layer
				json.dump(index_data, file, indent=4)

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
		#if you change index_data_keys, you must change if statments accordingly below
		self.index_data_keys = ['filepath',
								'symbol_id',
								'exchange',
								'symbol_type',
								'asset_id_base',
								'asset_id_quote',
								'data_start',
								'data_end']

		#looks through all tracked exchanges in self.exchange_handbook 
		#(exchange_handbook == handbook['exchange_data'])
		for exchange_id, exchange_data in self.exchange_handbook.items():
			#following uses coin_api function to filter through exchange contents by specified filter.
			#contents of self.exchange_handbook are already filtered by asset_id_quote & tracked_exchanges
			exchange_items = self.coin_api.JsonFilter(exchange_data, 
												{'asset_id_base': self.config['tracked_crypto']}, False)

			#checks for historical/(exchange_id), creates dir if not found
			exchange_path = self.historical_base_path+f"{exchange_id}"
			if os.path.isdir(exchange_path) == False:
				os.mkdir(exchange_path)

			#checks for data/(exchange_id)/(exchange_id)_index.json, creates file if not found
			index_path = self.historical_base_path+f'{exchange_id}/{exchange_id}_index.json'
			if os.path.exists(index_path) == True:
				#if file is found, it loads its contents
				with open(index_path, 'r') as file:
					try:
						exchange_index = {exchange_id: json.load(file)}
					except:
						exchange_index = {exchange_id: {}}
					self.historical_index.update(exchange_index)
			else:
				#if no file is found it creates one
				open(index_path, 'w')
				exchange_index = {exchange_id: {}}
				self.historical_index.update(exchange_index)

			#extracts data from each item and uses it to create/load historical data files
			for item in exchange_items:
				coin_data_filename = ("{}_{}_{}").format(item['symbol_type'], 
												   item['asset_id_base'], 
												   item['asset_id_quote'])+".csv"
				coin_data_path = self.historical_base_path+f"{exchange_id}/{coin_data_filename}"
				#checks for historical/{exchange_id}/{symbol_id}.csv, creates file if not found
				if os.path.exists(coin_data_path) == False:
					open(coin_data_path, 'w')

					coin_data = {coin_data_filename: {}}
					for key in self.index_data_keys:
						if key == 'filepath':
							coin_data[coin_data_filename].update({key: coin_data_path})
						elif key == 'exchange':
							coin_data[coin_data_filename].update({key: exchange_id})
						elif key == 'symbol_id':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'symbol_type':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'asset_id_base':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'asset_id_quote':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'data_start':
							coin_data[coin_data_filename].update({key: item[key]})
						elif key == 'data_end':
							coin_data[coin_data_filename].update({key: item['data_start']})#this is because it is made with no data
					self.historical_index[exchange_id].update(coin_data)

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
		if self.config['backfill_historical'] == True:
			print('----------------------------------------------------')
			print('Backfilling Historical Data')
			print('----------------------------------------------------')

			#NOTE: all data is in increments of 60 seconds exclusively
			self.historical_time_interval = 60

			#the following finds the total number of backfilling request we are making
			#it then finds the limit on each request needed to use all remaining api requests
			#so that only one iteration is needed
			total_requests = 0
			print('Backfill List:')
			for exchange_id, exchange in self.historical_index.items():
				print('   ', exchange_id)
				for coin in exchange:
					print('      ', coin)
					total_requests += 1
			print(f'{total_requests} total requests\n')
			limit_per_request = int(self.coin_api.api_index['startup_key']['limit'] / total_requests * 100)
			limit_per_request = limit_per_request - (limit_per_request % 100)
			limit_per_request = 1000
			#one request is 100 datapoints so limit_per_request is made a multiple of 100

			#the following goes through each indexed historical dataset
			for exchange_id, exchange_indexes in self.historical_index.items():
				#the key for each dataset's index is the filename
				for filename, dataset in exchange_indexes.items():

					#settings for the historical data requests
					url_ext = self.config['historical_url_ext'].format(dataset['symbol_id'])
					queries = {'time_start': dataset['data_end'],
							   'limit': limit_per_request,
							   'period_id': self.FindPeriodId(self.historical_time_interval)}

					print(queries)

					#no filter, the default request size is 100 (100 datapoints: uses one request)
					response = self.coin_api.MakeRequest(url_ext=url_ext, queries=queries, api_key_id='startup_key')

					#puts response into an array and adds it to existing data for current dataset
					response_data = pd.DataFrame.from_dict(response, orient='columns')

					#==============================================================
					#SET DATES TO UNIX START
					#==============================================================
					count = 0
					prev_time = time.time()
					start_time = time.time()
					new_df = response_data.copy()

					print('changing time values to unix')
					for index, row in new_df.iterrows():
						for col in new_df.columns:

							if 'time' in col:#if true, needs to be changed to unix time
								new_df.at[index, col] = self.SetDateToUnix(row[col])
						count += 1
						if count == 5000:
							current_time = time.time()
							delay = current_time - prev_time
							print(f"index: {index} || delay: {delay}")
							count = 0
							prev_time = current_time

					#it then verifies the data has not changed
					print('verifying unix dates')

					timestamp = 1000000
					new_timestamp = self.SetUnixToDate(timestamp)
					new_timestamp = self.SetDateToUnix(new_timestamp)
					print(f'timestamp convertion test: {timestamp} || {new_timestamp}')

					count = 0
					prev_time = time.time()
					for index, row in new_df.iterrows():
						for col in new_df.columns:
							#print(self.SetUnixToDate(new_df.iloc[index][col]), " || ", response_data.iloc[index][col])
							if 'time' in col:
								if self.SetUnixToDate(row[col]) != response_data.iloc[index][col]:
									raise ValueError('An Error Occured: SetDataFrameToUnix is different from argument: response_data')
							elif row[col] != response_data.iloc[index][col]:
								raise ValueError('An Error Occured: SetDataFrameToUnix is different from argument: response_data')
						count += 1
						if count == 2000:
							current_time = time.time()
							delay = current_time - prev_time
							print(f"index: {index} || delay: {delay}")
							count = 0
							prev_time = current_time


					total_time = time.time() - start_time
					print(f'Time Format Change Duration: {total_time} seconds')

					response_data = new_df
					#==============================================================
					#SET DATES TO UNIX END
					#==============================================================

					#loads existing data if any
					try:
						existing_data = pd.read_csv(dataset['filepath'])
						existing_data = existing_data.append(response_data, ignore_index=True, sort=False)
					except(pd.errors.EmptyDataError):
						print('No existing data for:', dataset['filepath'])
						print('Creating New Dataframe')
						existing_data = response_data

					existing_data.to_csv(dataset['filepath'], index=False)

					print(filename, 'updated to: ', self.SetUnixToDate(existing_data.iloc[-1]['time_period_end']))
					print('----------------------------------------------------')

					#update currency index for current dataset
					#ONLY CHANGE TIME_END
					time_end = self.SetUnixToDate(existing_data.iloc[-1]['time_period_end'])
					self.historical_index[exchange_id][filename]['data_end'] = time_end
					self.UpdateHistoricalIndex()
		else:
			print('config.backfill_historical = false: not updating historical data')



