
#standard library
import json
import csv
import time
import os
import requests
from requests.exceptions import HTTPError

from .preproc import unix_to_date, date_to_unix

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

class Coinapi():
	base_url = 'https://rest.coinapi.io/v1/'
	#base url for coinapi.io requests

	coinapi_path = 'database/coinapi.json'
	#path to coinapi.json file

	api_index = {}
	#keeps track of each api key data for reference
	exchange_index = {}
	#used for initializing historical index items
	period_index = {}
	#keeps track of coinapi period_id's


	def __init__(self):
		self.load_files()


	def load_files(self):
		#NOTE: All coinapi indexes are share the same file
		#Checks to see if coinapi_path exists, if not creates one
		if os.path.exists(Coinapi.coinapi_path) == False:
			open(Coinapi.coinapi_path, 'w')

		print('Loading Coinapi Files: ' + Coinapi.coinapi_path)
		#loads contents of file with path, "Coinapi.coinapi_path"
		with open(Coinapi.coinapi_path) as file:
			indexes = json.load(file)

			#loads api_index if it exists
			if 'api_index' in indexes:
				Coinapi.api_index = indexes['api_index']
			else:
				Coinapi.api_index = {}

			#loads exchange_index
			if 'exchange_index' in indexes:
				Coinapi.exchange_index = indexes['exchange_index']
			else:
				Coinapi.exchange_index = {}

			#loads period_index
			if 'period_index' in indexes:
				Coinapi.period_index = indexes['period_index']
			else:
				Coinapi.period_index = {}


	def save_files(self):
		#NOTE: All coinapi indexes are share the same file

		#consolidates all coinapi indexes to single dict and
		#saves it to coinapi.json
		indexes = {}
		indexes['api_index'] = Coinapi.api_index
		indexes['exchange_index'] = Coinapi.exchange_index
		indexes['period_index'] = Coinapi.period_index

		#Checks to see if path exists, if not it creates one
		if os.path.exists(Coinapi.coinapi_path) == False:
			open(Coinapi.coinapi_path, 'w')
		#saves settings dict class variable to file by default
		#can change settings parameter to custom settings dict
		with open(Coinapi.coinapi_path, 'w') as file:
			json.dump(indexes, file, indent=4)


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


	def make_request(self, api_key_id, url_ext='', queries={}, 
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
		'''
		tracked_headers = ['X-RateLimit-Request-Cost',
						   'X-RateLimit-Remaining',
						   'X-RateLimit-Limit', 
						   'X-RateLimit-Reset']

		#creates a local api index with only "api_key_id" data 
		api_index = Coinapi.api_index[api_key_id]
		url = self.base_url + url_ext

		try:
			print("Making API Request at:", url)
			response = requests.get(url, headers=api_index['api_key'], 
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
			
			#updates RateLimit info in api_index with response.headers
			for header in tracked_headers:
				#Updates reset time if the current reset time is expired
				if header == 'X-RateLimit-Reset' and header in api_index:
					if date_to_unix(api_index[header]) < time.time():
						api_index[header] = response.headers[header]
				else:
					api_index[header] = response.headers[header]
				print(f'	{header}:', api_index[header])

			#updates the class variable api_index
			Coinapi.api_index[api_key_id] = api_index
			#then saves the api_index to file
			with open(self.api_index_path, 'w') as file:
				json.dump(Coinapi.api_index, file, indent=4)

			#response errors are no longer being handled so it is assigned
			#to its json value and filtered
			response = response.json()
			if filters != {}:
				response = self.filter(response, filters, omit_filtered)
			else:
				print('Notice: no response filter')

			return response