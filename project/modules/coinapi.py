
#standard library
import json
import csv
import time
import math
import os
import requests
from requests.exceptions import HTTPError
	
#local modules
from .preproc import unix_to_date, date_to_unix
from .multiproc import print_progress_bar

#packages
import pandas as pd
import numpy as np

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
Coinapi.py Design Target:
	An abstraction of coinapi.io requests used
	primarily by the database to backfill historical
	data.
'''

class Coinapi():
	base_url = 'https://rest.coinapi.io/v1/'
	#base url for coinapi.io requests
	index_path = 'database/coinapi.json'
	#path to coinapi.json file

	#url_extensions for various coinapi requests
	#use .format to add content to brackets in use
	historical_url = base_url + 'ohlcv/{}/history'
	periods_url = base_url + 'ohlcv/periods'
	exchanges_url = base_url + 'exchanges'
	coins_url = base_url + 'symbols'

	#constant
	asset_id_quote = 'USD'

	api_index = {}
	#keeps track of each api key data for reference
	exchange_index = []
	#entire available pool of exchanges and their coins
	period_index = []
	#keeps track of coinapi period_id's


	def __init__():
		Coinapi.update_keys()
		Coinapi.load_files()


	def load_files():
		#NOTE: All coinapi indexes are share the same file
		#Checks to see if index_path exists, if not creates one
		if os.path.exists(Coinapi.index_path) == False:
			open(Coinapi.index_path, 'w')
			#uploads empty index variables to file
			Coinapi.save_files()

		print('Loading Coinapi Files: ' + Coinapi.index_path)
		#loads contents of file with path, "Coinapi.index_path"
		with open(Coinapi.index_path) as file:
			indexes = json.load(file)

			#loads api_index if it exists
			if indexes['api_index'] != {}:
				Coinapi.api_index = indexes['api_index']
			else:
				Coinapi.api_index = {}
				print('WARNING: No API Keys in Coinapi.api_index')

			#loads period_index
			if indexes['period_index'] != []:
				Coinapi.period_index = indexes['period_index']
			else:
				filters = {
					'length_seconds': 0
				}
				new_index = Coinapi.request('free_key', 
											url=Coinapi.periods_url,
										 	filters=filters,
										 	omit_filtered=True)
				Coinapi.period_index = new_index

			#loads exchange_index
			if indexes['exchange_index'] != []:
				Coinapi.exchange_index = indexes['exchange_index']
			else:
				new_index = Coinapi.request('free_key', 
										 	url=Coinapi.exchanges_url)
				Coinapi.exchange_index = new_index

		#the class variables may have changed so this updates files
		Coinapi.save_files()


	def save_files():
		#NOTE: All coinapi indexes are share the same file

		#consolidates all coinapi indexes to single dict and
		#saves it to coinapi.json
		indexes = {}
		indexes.update({'api_index': Coinapi.api_index})
		indexes.update({'exchange_index': Coinapi.exchange_index})
		indexes.update({'period_index': Coinapi.period_index})

		#Checks to see if path exists, if not it creates one
		if os.path.exists(Coinapi.index_path) == False:
			open(Coinapi.index_path, 'w')
		#saves settings dict class variable to file by default
		#can change settings parameter to custom settings dict
		with open(Coinapi.index_path, 'w') as file:
			json.dump(indexes, file, indent=4)


	def update_keys():
		#checks on api_key X-RateLimit-Reset
		#if expired, sets X-RateLimit-Remaining to X-RateLimit-Limit
		for api_id, item_index in Coinapi.api_index.items():
			reset_time = date_to_unix(item_index['X-RateLimit-Reset'])
			if reset_time <= time.time():
				limit = item_index['X-RateLimit-Limit']
				Coinapi.api_index[api_id]['X-RateLimit-Remaining'] = limit


	def period_id(time_increment):
		'''
		Parameters:
			- time_increment : (int) time_interval of data in 
									 unix time (seconds)

		returns coinapi period_id assuming input is valid
		'''
		for index_item in Coinapi.period_index:
			if index_item['length_seconds'] == time_increment:
				return index_item['period_id']

		raise ValueError(f'period_id not found for "{time_increment}"')


	def verify_period(period_id):
		'''
		Parameters:
			period_id : (str) period_id str supported by coinapi

		returns period_id if valid time_increment
		'''
		for index_item in Coinapi.period_index:
			if index_item['period_id'] == period_id:
				return True

		print(f'WARNING: "{period_id}" not found in period_index')
		return False


	def verify_increment(time_increment):
		'''
		Parameters:
			time_increment : (int) value used to match against
								   period_index['length_seconds']

		Returns False if time_increment is not in period_index
		Returns True if time_increment is in period_index
		'''
		for index_item in Coinapi.period_index:
			if index_item['length_seconds'] == time_increment:
				return True

		print(f'WARNING: {time_increment} not found in period_index')
		return False


	def verify_exchange(exchange_id):
		'''
		Parameters:
			exchange_id : (str) Name of exchange in coinapi format
								ex: 'KRAKEN'

			returns True given ID is found in exchange_index
					False of not found
		'''
		for index_item in Coinapi.exchange_index:
			if index_item['exchange_id'] == exchange_id:
				return True
				
		print(f'WARNING: {exchange_id} Not Found in coinapi.json')
		return False


	def filter(data, filters, omit_filtered):
		'''
		Parameters:
			data         : (list of dict) 
						   - values that will be filtered and returned
			filters      : (dict) 
						   - filtered items are added to return value
			omit_fitered : (bool) 
						   - if True: omits filtered instead of adding
		Assumptions:
			- "data" param is a list of dictionaries

		NOTE: each item needs to pass ALL filters to be returned/omited
		'''

		#prints filter data to console
		print('Data Filters:')
		if filters == {}:
			print('   - NONE')
		for key, val in filters.items():
			print(f'   - {key} | {val}')

		filtered = []
		remaining = []

		count = 0
		total = len(data)
		print(f'filtering {total} items')
		for item in data:
			#mismatch is True if it does not match filter values
			mismatch = False
			for filter_key, filter_val in filters.items():
				#if filter matches item val, no mismatch
				if filter_key in item:
					if item[filter_key] != filter_val:
						mismatch = True
				else:#item does not have filter_key
					mismatch = True
			#mismatched items are appended to remaining
			if mismatch == False:
				filtered.append(item)
			else:
				remaining.append(item)

			if total >= 10000:#not worth printing for less than 10000
				#updates count and print loading bar
				count += 1
				print_progress_bar(count, total)

		if omit_filtered == True:
			print('Notice: omiting filtered')
			return remaining

		return filtered


	def request(api_key_id, url='', queries={}, 
				filters={}, omit_filtered=False):
		'''
		HTTP Codes:
			200 - Successful Request
		HTTP Errors:
			400	Bad Request – There is something wrong with your request
			401	Unauthorized – Your API key is wrong
			403	Forbidden – Your API key doesn’t have enough privileges 
							to access this resource
			429	Too many requests – You have exceeded API key rate limit
			550	No data – You requested unavailable specific single item

		Parameters:
			url_ext      : (str)
						   - is added to Coinapi.base_url in request
			api_key_id   : (str)
						   - the dict key for what api key to use
			queries      : (dict)
						   - a premade dict of params for the request
			filters      : (dict) 
						   - filtered items are added to return value
			omit_fitered : (bool)
						   - if True: omits filtered instead of adding

		NOTE: queries include: ['time_start', 'limit', 'period_id']
		'''
		print('----------------------------------------------------')

		tracked_headers = ['X-RateLimit-Cost',
						   'X-RateLimit-Remaining',
						   'X-RateLimit-Limit', 
						   'X-RateLimit-Reset']

		#creates a local api index with only "api_key_id" data 
		api_key_index = Coinapi.api_index[api_key_id]

		try:
			print("Making API Request at:", url)
			response = requests.get(url, headers=api_key_index['api_key'], 
									params=queries)
			# If the response was successful, no Exception will be raised
			response.raise_for_status()
		except HTTPError as http_err:
			print(f'{http_err}')
			raise ValueError('HTTPError: Killing Process')
		except requests.ConnectionError as connection_err:
			print(f'{connection_err}')
			raise requests.ConnectionError('HTTP Connection Error')
		except Exception as err:
			print(f'{err}')
			raise Exception(f'Exception Occured During HTTP Request')
		else:
			print(f'API Request Successful: code {response.status_code}')
			
			#updates RateLimit info in api_key_index with response.headers
			for header in tracked_headers:
				#verifies tracked_header is in response.headers
				if header in response.headers:
					#updates api_id 
					api_key_index[header] = response.headers[header]
					print(f'	{header}:', api_key_index[header])

			#updates the class variable api_key_index
			Coinapi.api_index[api_key_id] = api_key_index
			Coinapi.save_files()

			#response errors are no longer being handled so it is assigned
			#to its json value and filtered
			response = response.json()
			if filters != {}:
				response = Coinapi.filter(response, filters, omit_filtered)
			else:
				print('Notice: no response filter')

			print('----------------------------------------------------')

			return response


	def prep_historical(response):
		'''
		this function adds an isnan and average_price column
		to the given df and appends empty rows for missing
		datapoints so that each timestep is equal spacing and
		equal to 'time_increment' in seconds.

		Parameters:
			response : (dict) data required for function 
							  (see Coinapi.historical())

		return: {
			'data': new_df,
			'time_start': time_start,
			'time_end': time_end
		}
		'''

		#isolates relevant response dict items
		time_increment = response['data_index']['time_increment']
		time_start = response['time_start']
		time_end = response['time_end']
		df = response['data']

		if df.empty == False:
			#converters time_period_start to unix values
			print('converting timestamps to unix')

			#tracks duration
			prev_time = time.time()
			for index, row in df.iterrows():
				for col in df.columns:

					if 'time' in col:#dates are converted to unix format
						df.at[index, col] = date_to_unix(row[col])
						
				if index % 5000 == 0 and index != 0:
					current_time = time.time()
					delay = current_time - prev_time
					print(f"index: {index} || delay: {delay}")
					prev_time = current_time

			#determines the values of the price_average column and inserts it
			#into df
			price_low = df.loc[:, 'price_low'].values
			price_high = df.loc[:, 'price_high'].values
			price_average = np.divide(np.add(price_low, price_high), 2)
		else:
			columns = {
				'price_close',
				'price_high',
				'price_low',
				'price_open',
				'time_close',
				'time_open',
				'time_period_end',
				'time_period_start',
				'trades_count',
				'volume_traded'
			}
			df = pd.DataFrame(columns=columns)
			price_average = np.nan

		df['price_average'] = price_average

		#initializes isnan with False for every row
		df['isnan'] = False

		#finds the total number of expected datapoints (if none were missing)
		#(time_end - time_start) / time_increment
		datapoints = int((date_to_unix(time_end) - 
						  date_to_unix(time_start)) / time_increment)
		#create the index of new_df (continuous)
		interval = np.multiply(range(datapoints), time_increment)
		interval = np.add(interval, date_to_unix(time_start))

		#creates new_df with index (the index is also time_period_start)
		new_df = pd.DataFrame(columns=df.columns, index=interval)

		#changes df index so that it is based on time_period_start as
		#new_df is
		df.set_index('time_period_start', inplace=True, drop=False)

		#overwrite df data onto new_df
		new_df.update(df)

		#df has missing time_period_start values, need to be filled
		new_df.loc[:, 'time_period_start'] = new_df.index

		#load all time_period_end values
		new_df['time_period_end'] = np.add(new_df.loc[:, 'time_period_start'], 
										   time_increment)

		#update isnan values for new data
		new_df.isnan.fillna(True, inplace=True)

		#print('OLD DF:\n\n\n', df)
		#print('NEW DF:\n\n\n', new_df)

		#saves response with only the necessary information
		response = {
			'data': new_df,
			'time_start': time_start,
			'time_end': time_end
		}

		return response


	def historical(data_index, requests=None):
		'''
		Parameters:
			index : (dict) historical_index of item being requested
			requests : (int) number of timesteps (datapoints) 
							 being requested

		return : (dict) {
			"data": pd.DataFrame(),
			"time_start": (str),
			"time_end": (str)
		}
		'''
		#updates api keys
		Coinapi.update_keys()

		#the key bing used
		api_id = 'startup_key'
		remaining = Coinapi.api_index[api_id]['X-RateLimit-Remaining']
		remaining = int(remaining)#converts to int

		if requests == None:
			requests = remaining * 100

		#determines time_start and time_end values for request
		time_start = data_index['data_end']
		time_interval = requests * data_index['time_increment']
		print('requests:', requests)
		time_end = unix_to_date(date_to_unix(time_start) + time_interval)

		#shorts function if no data exists
		if requests == 0:
			response = {
				'data': pd.DataFrame(),
				'time_start': time_start,
				'time_end': time_end
			}
			return response

		#queries for request
		queries = {
			'limit': remaining,
			'time_start': time_start,
			'time_end': time_end,
			'period_id': data_index['period_id']
		}

		#api request
		url = Coinapi.historical_url.format(data_index['symbol_id'])
		response = Coinapi.request(api_id, url=url, queries=queries)

		#format the json response into a dataframe
		response = pd.DataFrame.from_dict(response, orient='columns')

		#formats response for 'prep_historical'
		response = {
			'data': response,
			'time_start': time_start,
			'time_end': time_end,
			'data_index': data_index
		}

		#preps historical data
		response = Coinapi.prep_historical(response)

		#prep data for historical database and return df
		return response

