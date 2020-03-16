
#standard library
import json
import time
import math
import os
from string import Template
import requests
from requests.exceptions import HTTPError

#packages
import pandas as pd
import numpy as np
	
#local modules
from define import *
from .preproc import unix_to_date, date_to_unix


'''
Module - coinapi.py

Last Refactor: Alpha-v1.0


CONTENTS:

class Coinapi():
	TOOLS:
		def load_files():
			#loads all coinapi files into database

		def save_files():
			#saves all coinapi database indexes to database

		def update_key(key_id, headers=None):
			#Updates Rate Limit values of specified key in database

		def increment_to_period(time_increment):
			#converts time_increment (int) to period_id (str)

		def period_to_increment(period_id):
			#converts period_id (str) to time_increment (int)

		def verify_period(period_id):
			#confirms whether period_id is supported by Coinapi.io

		def verify_increment(time_increment):
			#confirms whether time_increment is supported by Coinapi.io

		def verify_exchange(exchange_id):
			#confirms whether exchange is supported by Coinapi.io

		def verify_coin(coin_id):
			#confirms whether coin is supported by Coinapi.io

		def filter(request, filters, remaining=False):
			#filters request data and returns filtered or remaining

	REQUESTS:
		def request(key_id, url='', queries={}, 
					filters={}, omit_filtered=False):
			#makes api requests

		def backfill(key_id, index_id, limit=None):
			#backfills historical data for specified index_id

		def reload_coins(key_id):
			#reloads index of all coins for USD in database

		def reload_exchanges(key_id):
			#reloads index of all exchanges in database

		def reload_periods(key_id):
			#reloads index of all periods in database
'''


#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################


class Coinapi():
	base_url = 'https://rest.coinapi.io/v1/'
	#base url for coinapi.io requests
	index_path = 'database/coinapi.json'
	#path to coinapi.json file

	#url_extensions for various coinapi requests
	historical_url = Template(base_url + 'ohlcv/${symbol_id}/history')
	period_url = base_url + 'ohlcv/periods'
	exchange_url = base_url + 'exchanges'
	coin_url = base_url + 'symbols'

	#constant
	asset_id_quote = 'USD'


	def __init__():
		Coinapi.load_files()


	def load_files():
		#loads all coinapi files to database

		###API_INDEX###
		def try_func(json):
			Database.api_index = json
		def fail_func():
			Database.api_index = {}
		Database.load_file(Database.api_index_path, try_func, fail_func)

		###COIN_INDEX###
		def try_func(json):
			Database.coin_index = json
		def fail_func():
			Coinapi.reload_coins('free_key')
		Database.load_file(Database.coin_index_path, try_func, fail_func)

		###EXCHANGE_INDEX###
		def try_func(json):
			Database.exchange_index = json
		def fail_func():
			Coinapi.reload_exchanges('free_key')
		Database.load_file(Database.exchange_index_path, try_func, fail_func)

		###PERIOD_INDEX###
		def try_func(json):
			Database.period_index = json
		def fail_func():
			Coinapi.reload_periods('free_key')
		Database.load_file(Database.period_index_path, try_func, fail_func)


	def save_files():
		#commits all coinapi indexes to file in database

		###COIN_INDEX###
		Database.save_file(Database.coin_index_path, 
						   Database.coin_index)
		###EXCHANGE_INDEX###
		Database.save_file(Database.exchange_index_path, 
						   Database.exchange_index)
		###PERIOD_INDEX###
		Database.save_file(Database.period_index_path, 
						   Database.period_index)
		###API_INDEX###
		Database.save_file(Database.api_index_path, 
						   Database.api_index)


	def update_key(key_id, headers=None):
		'''
		Updates the X-RateLimit-[limit, remaining, reset] data in 
		Database for specified key. Does not update if X-RateLimit-Reset 
		if not greater than existing.

		Parameters:
			- key_id  : (str) user given id to each coinapi api-key
							  used to access api_index in database
			- headers : (dict) request.headers from latest request
		NOTE: If headers are not given, api_id is updated based on
			the last X-RateLimit_Reset time
		'''

		#the current stored api information in database
		key_index = Database.api_index[key_id]

		if headers == None:
			#the unix value of key_index['reset']
			unix_reset = date_to_unix(key_index['reset'])

			#if no header given
			if unix_reset <= time.time():
				#reset key_inex['remaining'] information in database
				Database.api_index[key_id]['remaining'] = key_index['limit']
		else:
			#headers given from new request
			for header, value in headers.items():
				#if a header matches, update that value in database
				if 'limit' in header:
					Database.api_index[key_id]['limit'] = value
				elif 'remaining' in header:
					Database.api_index[key_id]['remaining'] = value
				elif 'reset' in header:
					Database.api_index[key_id]['reset'] = value

		#commits changes
		Coinapi.save_files()


	def increment_to_period(time_increment):
		'''
		Converts increment (int, in seconds) to 
		period_id (human readable str)

		Parameter:
			time_increment : (int) int of time_step value in seconds
		'''

		#loads period_index from database and looks through list
		#of dict for a matching period to given time_increment
		for index_item in Database.period_index:
			if index_item['length_seconds'] == time_increment:
				#matching period_id found
				return index_item['period_id']

		raise ValueError(f'period_id not found for "{time_increment}"')


	def period_to_increment(period_id):
		'''
		Converts period_id (human readable str) to 
		time_increment (int, seconds)

		Parameter:
			period_id : (str) str of time_step value EX:"5MIN"
		'''

		for index_item in Coinapi.period_index:
			if index_item['period_id'] == period_id:
				return index_item['length_seconds']

		raise ValueError(f'period_id not found for "{time_increment}"')


	def verify_period(period_id):
		'''
		Parameters:
			period_id : (str) period_id str supported by coinapi

		returns period_id if valid time_increment
		'''
		for index_item in Database.period_index:
			if index_item['period_id'] == period_id:
				return True

		print(f'WARNING: "{period_id}" not found in period_index')
		return False


	def verify_increment(time_increment):
		'''
		Parameters:
			time_increment : (int) value used to match against
								   period_index['length_seconds']
		'''
		for index_item in Database.period_index:
			if index_item['length_seconds'] == time_increment:
				return True

		raise KeyError(f'{time_increment} not found in period_index')


	def verify_exchange(exchange_id):
		'''
		Parameters:
			exchange_id : (str) Name of exchange in coinapi format
								ex: 'KRAKEN'
		'''
		for index_item in Coinapi.exchange_index:
			if index_item['exchange_id'] == exchange_id:
				return True
				
		raise KeyError(f'{exchange_id} not found in exchange_index')


	def verify_coin(coin_id):
		'''
		Parameters:
			coin_id : (str) Name of exchange in coinapi format
							ex: 'BTC'
		'''
		if coin_id in Database.coin_index.keys():
			return True

		raise KeyError(f'{exchange_id} not found in coin_index.json')


	def filter(request, filters, remaining=False):
		'''
		Parameters:
			request   : (list of dicts) coinapi json request data
			filters   : (dict) dict of filters that need to be passed
							   for data to be added to filtered
			remaining : (bool) returns remaining instead of filtered if True

		NOTE: each item needs to pass ALL filters to be in filtered,
		The rest is appended to remaining
		'''

		if filters == {}:
			print('NOTICE: no filters given, returning items')
			return request

		#prints filter request config to console
		print('Request Filters:')
		for key, val in filters.items():
			print(f'   - {key} | {val}')

		#filtered items have passed all given filters
		filtered_items = []
		#remaining items have failed at least one filter
		remaining_items = []

		#total items in request
		total = len(request)
		print(f'filtering {total} items')

		#iterates through request items for filtering
		for item in request:
			mismatch = False #default val is False

			#iterates through each filter for current item
			for filter_key, filter_val in filters.items():
				if filter_key in item:
					#current item has the filter key
					if item[filter_key] != filter_val:
						#value of item does not match current filter
						mismatch = True
				else:
					#item does not have filter_key
					mismatch = True

			if mismatch == False:
				#item passed all filteres
				filtered_items.append(item)
			else:
				#item did not pass all filters
				remaining_items.append(item)

		if remaining_items == True:
			print('Notice: returning remaining items')
			return remaining_items

		print('Notice: returning filtered items')
		return filtered_items


	def request(key_id, url='', queries={}, 
				filters={}, remaining=False):
		'''
		Parameters:
			url_ext   : (str) is added to Coinapi.base_url in request
			key_id    : (str) name of the api_key being used
			queries   : (dict) a premade dict of params for the request
			filters   : (dict) dict of filters that need to be passed
							 for data to be added to filtered
			remaining : (bool) returns remaining instead of filtered if True

		queries example: {
			'time_start': '2018-02-15T12:53:50.0000000Z',
			'limit': 100,
			'period_id': 'KRAKEN_BTC_5MIN'
		}
		'''

		#update api key index in database
		Coinapi.update_key(key_id)

		#creates a local api index with only "key_id" data 
		key_index = Database.api_index[key_id]

		try:
			print("\nMaking API Request at:", url)
			response = requests.get(url, headers=key_index['api_key'], 
									params=queries)
			# If the response was successful, no Exception will be raised
			response.raise_for_status()
		except HTTPError as http_err:
			#catches http errors
			print(f'{http_err}')
			raise ValueError('HTTPError: Killing Process')
		except requests.ConnectionError as connection_err:
			#no connection to internet/coinapi.io
			print(f'{connection_err}')
			raise requests.ConnectionError('HTTP Connection Error')
		except Exception as err:
			#catches any other exceptions
			print(f'{err}')
			raise Exception(f'Exception Occured During HTTP Request')
		else:
			print(f'API Request Successful: code {response.status_code}')
			
			#updates key_index rate limit information in database 
			Coinapi.update_key(key_id, response.headers)

			#converts response to json
			response = response.json()

			#response is converted to json and filtered
			if filters != {}:
				response = Coinapi.filter(response, filters, remaining)
			else:
				print('NOTICE: no filter')

			print()#spacer

			return response


	def backfill(key_id, index_id, limit=None):
		'''
		backfills historical data for specified index_id 
		and saves it to database

		Parameters:
			key_id   : (str) name of the api key being used
			index_id : (dict) historical_index of item being requested
			limit    : (int) request limit set by user
		return: (pd.DataFrame) the data that was requested
		'''

		print('----------------------------------------------------')
		print('Backfilling Historical Data')
		init_time = time.time()

		#updates specified api key
		Coinapi.update_key(key_id)

		#loads the api key information
		key_index = Database.api_index[key_id]
		#loads historical index of data being requested
		hist_index = Database.historical_index[index_id]
		#loads start time for request
		time_start = date_to_unix(hist_index['data_end'])#unix time
		#loads the end time for request (latest increment time value)
		remainder = init_time % hist_index['time_increment']
		time_end = init_time - remainder

		#verifies given limit is valid
		if limit < 0:
			#limit is negative
			raise ValueError(f'limit cannot be negative')
		elif isinstance(limit, int) == False:
			#limit is not an int
			limit_tp = type(limit)
			raise ValueError(f'limit cannot be {limit_tp}, must be int')
		elif limit > key_index['remaining']:
			#given limit is larger than remaining requests for key_id
			print('WARNING: given limit exceeds available requests')
			limit = key_index['remaining']

		#generates request parameters
		queries = {
			'limit': limit,
			'time_start': unix_to_date(time_start),
			'time_end': unix_to_date(time_end),
			'period_id': hist_index['period_id']
		}

		#load url
		url = Coinapi.historical_url.substitute(
					symbol_id=hist_index['symbol_id'])

		#make the api request
		response = Coinapi.request(key_id, url=url, queries=queries)
		#converts response to pandas dataframe
		df = pd.DataFrame.from_dict(response.json(), 
										  orient='columns')

		#verifies df has data and converts dates to unix
		if df.empty == False:
			#df is not empty
			#
			#convertes time_period_start to unix values
			print('converting timestamps to unix')

			#iterates each row
			for index, row in df.iterrows():
				#iterates each column
				for col in df.columns:

					if 'time' in col:
						#current column has a time value
						#
						#converts date to unix
						df.at[index, col] = date_to_unix(row[col])

			#calculates price_average column
			price_low = df.loc[:, 'price_low'].values
			price_high = df.loc[:, 'price_high'].values
			price_average = np.divide(np.add(price_low, price_high), 2)
		else:
			#no data in response (df)
			print(f'NOTICE: request has no data')

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

			#re-initializes df with columns
			df = pd.DataFrame(columns=columns)
			price_average = np.nan

		#inserts price_average into df at column index = 2
		df.insert(2, 'price_average', price_average)
		#initializes isnan with False for every row with data
		df['isnan'] = False
		#sets index of df to equal 'time_period_start'
		df.set_index('time_period_start', inplace=True, drop=False)

		#creates an empty dataframe (historical) with no missing 
		#indexes, start and end times match request queries
		datapoints = (time_end - time_start) / hist_index['time_increment']
		index = range(datapoints) + time_start
		historical = pd.DataFrame(columns=df.columns, index=index)

		#load time_period_start data into column
		historical['time_period_start'] = historical.index
		#load time_period_end data into column
		historical['time_period_end'] = np.add(historical.index,
											   hist_index['time_increment'])
		#apply df data to historical
		historical.update(df)
		#set empty rows to isnan = True
		new_df.isnan.fillna(True, inplace=True)

		#load existing data from database
		existing_data = Database.historical(index_id)
		#combine existing data and historical
		historical = existing_data.append(historical)

		#updates hist_index
		hist_index['datapoints'] = len(historical.index)
		hist_index['data_end'] = unix_to_date(time_end)
		#updates Database.historical_index with hist_index
		Database.historica_index[index_id] = hist_index
		#commits changes to file
		Database.save_files()

		#saves new data to file
		historical.to_csv(filepath, index=False)

		print(f'\nDuration:', time.time() - init_time)
		print('----------------------------------------------------')


	def reload_coins(key_id):
		'''
		Parameters:
			key_id : (str) name of api_key to use for request

		reloads index of all coins offered by coinapi.io in USD
		organized by coin_id

		Example coin_index.json: {
			'BTC' : {
				'exchanges' : ['KRAKEN', 'BINANCE', ...],
				...
			},
			...
		}
		'''

		print('\nReloading Coin Index...')
		init_time = time.time()

		#requests all currency data and filters by USD
		response = Coinapi.request(key_id, url=Coinapi.coin_url,
								   filters={'asset_id_quote': 'USD'})

		#sets index to empty dict
		Database.coin_index = {}

		#iterates through coins and adds them to coin_index by exchange
		#if exchanges are added as needed
		for item_index in response:

			#loads coin_id from item_index
			coin_id = item_index['asset_id_base']

			#determines if exchange exists in coin_index
			if coin_id not in Database.coin_index:
				#coin_id not found in coin_index
				#
				#creates new coin and adds it to coin_index
				Database.coin_index.update({coin_id: []})
			
			#adds item_index to coin_index
			Database.coin_index[coin_id].append(item_index)

		#saves coin_index to file
		Coinapi.save_files()

		print(f'Duration:', (time.time() - init_time))
		print('----------------------------------------------------')


	def reload_exchanges(key_id):
		'''
		Parameters:
			key_id : (str) name of api key being used

		#reloads index of all exchanges in database

		Example of exchange_index: {
			'KRAKEN' : {
				...
			},
			...
		}
		'''

		print('\nReloading Exchange Index...')
		init_time = time.time()

		#requests all exchange data
		response = Coinapi.request(key_id, url=Coinapi.exchange_url)

		#sets index to empty dict
		Database.exchange_index = {}

		#iterates through response and adds it to exchange_index
		for item_index in response:
			#creates exchange item
			exchange = {item_index['exchange_id']: item_index}

			#adds exchange to exchange_index
			Database.exchange_index.update(exchange)

		#saves exchange_index to file
		Coinapi.save_files()

		print(f'Duration:', (time.time() - init_time))
		print('----------------------------------------------------')


	def reload_periods(key_id):
		'''
		Parameters:
			key_id : (str) name of api key being used

		#reloads index of all periods in database

		Example of exchange_index: [
			{
				#period1 item_index#
			},
			...
		]
		'''

		print('\nReloading Period Index...')
		init_time = time.time()

		#requests all period data and filters unusable items
		response = Coinapi.request(key_id, 
								   url=Coinapi.period_url,
								   filters={'length_seconds': 0},
								   remaining=True)
		#sets period_index to response
		Database.period_index = response

		#saves period_index to file
		Coinapi.save_files()

		print(f'Duration:', (time.time() - init_time))
		print('----------------------------------------------------')