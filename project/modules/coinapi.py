
#standard library
import json
import csv
import time
import os
import requests
from requests.exceptions import HTTPError

from .preproc import unix_to_date, date_to_unix, prep_historical

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

class Coinapi():
	base_url = 'https://rest.coinapi.io/v1/'
	#base url for coinapi.io requests
	index_path = 'database/coinapi.json'
	#path to coinapi.json file

	api_index = {}
	#keeps track of each api key data for reference
	exchange_index = []
	#entire available pool of exchanges and their coins
	period_index = []
	#keeps track of coinapi period_id's


	def __init__(self):
		#url_extensions for various coinapi requests
		#use .format to add content to brackets in use
		self.historical_url = Coinapi.base_url + 'ohlcv/{}/history'
		self.periods_url = Coinapi.base_url + 'ohlcv/periods'
		self.exchanges_url = Coinapi.base_url + 'exchanges'

		#constant
		self.asset_id_quote = 'USD'

		self.update_keys()
		self.load_files()


	def load_files(self):
		#NOTE: All coinapi indexes are share the same file
		#Checks to see if index_path exists, if not creates one
		if os.path.exists(Coinapi.index_path) == False:
			open(Coinapi.index_path, 'w')
			#uploads empty index variables to file
			self.save_files()

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
				new_index = self.request('free_key', 
										 url=self.periods_url,
										 filters=filters,
										 omit_filtered=True)
				Coinapi.period_index = new_index

			#loads exchange_index
			if indexes['exchange_index'] != []:
				Coinapi.exchange_index = indexes['exchange_index']
			else:
				new_index = self.request('free_key', 
										 url=self.exchanges_url)
				Coinapi.exchange_index = new_index

		#the class variables may have changed so this updates files
		self.save_files()


	def save_files(self):
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


	def update_keys(self):
		#checks on api_key X-RateLimit-Reset
		#if expired, sets X-RateLimit-Remaining to X-RateLimit-Limit
		for api_id, item_index in Coinapi.api_index.items():
			reset_time = date_to_unix(item_index['X-RateLimit-Reset'])
			if reset_time <= time.time():
				limit = item_index['X-RateLimit-Limit']
				Coinapi.api_index[api_id]['X-RateLimit-Remaining'] = limit


	def period_id(self, unix):
		'''
		Parameters:
			- unix : (int) time_interval of data in unix time (seconds)

		returns coinapi period_id assuming unix imput is valid
		'''
		for item in self.handbook['period_data']:
			if item['length_seconds'] == unix:
				return item['period_id']
		print('Error: period_id not found for unix_time value:', unix)
		return ''


	def filter(self, data, filters, omit_filtered):
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


		if omit_filtered == True:
			print('Notice: omiting filtered')
			return remaining

		return filtered


	def request(self, api_key_id, url='', queries={}, 
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
						   - is added to self.base_url in request
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
		except Exception as err:
			print(f'{err}')
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
			#then saves the api_key_index to file
			with open(Coinapi.index_path, 'w') as file:
				json.dump(Coinapi.api_index, file, indent=4)

			#response errors are no longer being handled so it is assigned
			#to its json value and filtered
			response = response.json()
			if filters != {}:
				response = self.filter(response, filters, omit_filtered)
			else:
				print('Notice: no response filter')

			return response


	def historical(self, item_indexes, match_data=False):
		'''
		Parameters:
			item_indexes : (list) list of indexes from historical_index
								  that are going to be backfilled
			match_data   : (bool) if true: backfills all items so that
								  data_end matches the biggest one
								  - does not go past 'biggest' one

		return : (dict) ex: {index_id: pd.DataFrame(), ...}
				 		this function returns a dict of dataframes
				 		of the new data it picked up for each item
				 		that was backfilled.
		'''
		print('----------------------------------------------------')
		print('Backfilling Historical Data')
		print('----------------------------------------------------')

		#updates api_keys
		self.update_keys()

		#the key being used is loaded
		api_id = 'startup_key'

		#finds the most recent data_end value and determines the number
		#of datapoints each other coin needs to be caught up
		#
		#this value is stored as 'match_val' in each index item
		match_date = 0 #the unix val of largest data_end val
		match_val_total = 0
		print('backfill list:')
		for x in range(2):
			#loops indexes twice, first loop is to find largest data_end
			for index_id, item_index in item_indexes.items():
				data_end = date_to_unix(item_index['data_end'])
				if x == 0:
					print(f'   - {index_id}')
					#data_end is stored as date, converted to unix
					if data_end > match_date:
						match_date = data_end
				elif x == 1:
					#saves new match_val to each index
					match_val = (match_date - data_end)
					match_val_total += match_val #updates match_val_total
					match_val = {'match_val': match_val}
					#match_val is num_timesteps away from match_date
					item_indexes['index_id'].update(match_val)

		#remaining limit of current key

		#compares remaining_limit to match_val_total / 100
		if (match_val_total / 100 < 
				Coinapi.api_index[api_id]['X-RateLimit-Remaining']):
			print('''NOTICE: Not Enough Remaining Requests for 
					 "data_end" Match''')

		#backfills each item for 'match_val' datapoints or until
		#remaining requests run out
		backfill_data = {}
		for index_id, item_index in item_indexes.items():
			#one request is 100 datapoints so this accounts for that
			remaining = Coinapi.api_index[api_id]['X-RateLimit-Remaining']
			requests = ceil(item_index['match_val'] / 100)
			#caps requests at remaining
			if requests > remaining:
				requests = remaining

			#queries for request
			queries = {
				'limit': requests,
				'period_id': self.period_id(item_index['time_interval']),
			}

			if Coinapi.api_index[api_id]['X-RateLimit-Remaining'] <= 0:
				print('WARNING: Ran Out of Requests')
				break