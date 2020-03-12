
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
from .preproc import unix_to_date, date_to_unix


'''
Module - coinapi.py

Last Refactor: Alpha-v1.0 (in progress)


Table of Contents:

class Coinapi():
	MISC TOOLS:
		def update_key(key_id, headers=None):
			#Updates Rate Limit values of specified key in database

		def increment_to_period(time_increment):
			#converts time_increment to period_id

		def period_to_increment(period_id):
			#converts period_id to time_increment

		def verify_period(period_id):
			#makes sure period_id is supported by Coinapi.io

		def verify_increment(time_increment):
			#makes sure time_increment is supported by Coinapi.io

		def verify_exchange(exchange_id):
			#makes sure exchange is supported by Coinapi.io

	REQUEST TOOLS:
		def filter(request, filters, remaining=False):
			#filters request data and returns filtered or remaining
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
	periods_url = base_url + 'ohlcv/periods'
	exchanges_url = base_url + 'exchanges'
	coins_url = base_url + 'symbols'

	#constant
	asset_id_quote = 'USD'


	def __init__():
		#Coinapi.update_keys()
		pass


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

		#the unix value of key_index['reset']
		unix_reset = date_to_unix(key_index['reset'])

		if headers == None:
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


#############################################################
###Alpha-v1.0 progress stops here
#############################################################


	def filter(request, filters, remaining=False):
		'''
		Parameters:
			request      : (list of dicts) coinapi json request data
			filters      : (dict) dict of filters that need to be passed
								  for data to be added to filtered
			remaining : (bool) returns remaining instead of filtered if True

		NOTE: each item needs to pass ALL filters to be in filtered,
		The rest is appended to remaining
		'''

		#prints filter request to console
		print('Request Filters:')
		if filters == {}:
			print('   - NONE')
		for key, val in filters.items():
			print(f'   - {key} | {val}')

		#filtered items have passed all given filters
		filtered = []
		#remaining items have failed at least one filter
		remaining = []

		count = 0
		total = len(request)
		print(f'filtering {total} items')
		for item in request:
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


	def request(key_id, url='', queries={}, 
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
			#Coinapi.save_files()

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

