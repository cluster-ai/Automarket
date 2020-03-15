
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

		def filter(request, filters, remaining=False):
			#filters request data and returns filtered or remaining

	REQUESTS:
		def request(key_id, url='', queries={}, 
					filters={}, omit_filtered=False):
			#makes api requests

		def historical(key_id, index_id, requests=None):
			#requests and formats historical data

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
		is not greater than existing.

		Parameters:
			- key_id  : (str) user-given id to each coinapi api-key
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

		Returns False if time_increment is not in period_index
		Returns True if time_increment is in period_index
		'''
		for index_item in Database.period_index:
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


	def historical(key_id, index_id, requests=None):
		'''
		Parameters:
			key_id   : (str) name of the api key being used
			index_id : (dict) historical_index of item being requested
			requests : (int) number of timesteps (datapoints) 
							 being requested times 100
						- 100 datapoints = 1 request
		return: (pd.DataFrame) the data that was requested
		'''
		#updates specified api key
		Coinapi.update_key(key_id)

		#loads the key_index
		key_index = Database.api_index[key_id]
		#loads historical index of data being requested
		hist_index = Database.historical_index[index_id]

		if requests == None:
			#requests value not given
			requests = key_index['remaining']
		elif requests > key_index['remaining']:
			#requests parameter larger than remaining
			requests = key_index['remaining']
			print(f'NOTICE: only {requests} requests left for {key_id}')

		#sets start time based on last datapoint
		time_start = hist_index['data_end']
		#determines interval based on number of requests
		time_interval = requests * hist_index['time_increment'] * 100
		print('requests:', requests)
		#time_end is the date of the last datapoint being requested
		time_end = unix_to_date(date_to_unix(time_start) + time_interval)

		#catches time_end values that go past current date
		current_time = time.time()
		if date_to_unix(time_end) > current_time:
			#current time is less than time_end
			remainder = current_time % hist_index['time_interval']
			#new time_end rounded down to nearest multiple of interval
			time_end = current_time - remainder

		#shorts function if no data exists
		if requests == 0:
			print(f'NOTICE: no requests left')
			response = {
				'data': pd.DataFrame(),
				'time_start': time_start,
				'time_end': time_start
			}
			return response

		#queries for request
		queries = {
			'limit': key_index['remaining'],
			'time_start': time_start,
			'time_end': time_end,
			'period_id': hist_index['period_id']
		}

		#load url
		url = Coinapi.historical_url.substitute(
			symbol_id=hist_index['symbol_id']
		)

		#make the api request
		response = Coinapi.request(key_id, url=url, queries=queries)

		#json response data into a pandas dataframe (df)
		df = pd.DataFrame.from_dict(df, orient='columns')

		################################################
		###Formats Historical Data


		if df.empty == False:
			#convertes time_period_start to unix values
			print('converting timestamps to unix')

			#iterates each row
			for index, row in df.iterrows():
				#iterates each column
				for col in df.columns:

					if 'time' in col:#dates are converted to unix format
						df.at[index, col] = date_to_unix(row[col])

			#calculates price_average using price_low and price_high
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

		#create price_average column and set it to local variable
		df['price_average'] = price_average

		#initializes isnan with False for every row with data
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

		#overwrite df onto new_df
		new_df.update(df)

		#df has missing time_period_start values, need to be filled
		new_df.loc[:, 'time_period_start'] = new_df.index

		#load all time_period_end values
		new_df['time_period_end'] = np.add(new_df.loc[:, 'time_period_start'], 
										   time_increment)

		#update 'isnan' values for new new_df
		new_df.isnan.fillna(True, inplace=True)

		#prep new_df for historical database and return df
		return new_df


	def reload_coins(key_id):
		'''
		Parameters:
			key_id : (str) name of api_key to use for request

		reloads index of all coins offered by coinapi.io in USD
		organized by exchange

		Example coin_index.json: {
			'KRAKEN' : {
				'BTC' : {},
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

			#loads exchange_id from item_index
			exchange_id = item_index['exchange_id']

			#determines if exchange exists in coin_index
			if exchange_id not in Database.coin_index:
				#creates new exchange and adds it to coin_index
				Database.coin_index.update({exchange_id: {}})

			#creates dict item: {coin_id, item_index}
			coin = {item_index['asset_id_base']: item_index}
			
			#adds coin to corresponding exchange in coin_index
			Database.coin_index[exchange_id].update(coin)

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