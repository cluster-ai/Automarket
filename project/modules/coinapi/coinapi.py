

#standard library
import json
import csv
import time
import os
import requests
from requests.exceptions import HTTPError

from modules.dproc.dproc import unix_to_date, date_to_unix

class CoinAPI():
	#the api index is shared across all CoinAPI objects
	api_index = {}

	def __init__(self):
		self.base_url = 'https://rest.coinapi.io/v1/'

		self.api_index_path = 'modules/coinapi/api_index.json'
		with open(self.api_index_path, 'r') as file:
			CoinAPI.api_index = json.load(file)


	def __RequestHandler(self, url_ext, api_key_id, queries):
		'''
		HTTP Errors:
			400	Bad Request – There is something wrong with your request
			401	Unauthorized – Your API key is wrong
			403	Forbidden – Your API key doesn’t have enough privileges 
							to access this resource
			429	Too many requests – You have exceeded your API key rate limits
			550	No data – You requested specific single item that we don’t 
						  have at this moment.

		200 - Successful Request

		Parameters:
			url_ext     : is added to self.base_url in request (str)
			api_key_id  : the dict key for what api key to use (str)
			queries     : a premade dict of params for the request (dict)
		'''
		update_headers = ['X-RateLimit-Request-Cost',
						  'X-RateLimit-Remaining',
						  'X-RateLimit-Limit', 
						  'X-RateLimit-Reset']

		#creates a local api index with only "api_key_id" data 
		api_index = CoinAPI.api_index[api_key_id]
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
			for header_key in update_headers:
				#Only updates reset time if the current reset time is expired
				#	That way the reset time is when remaining will be full again
				if header_key == 'X-RateLimit-Reset' and header_key in api_index:
					if date_to_unix(api_index[header_key]) < time.time():
						api_index[header_key] = response.headers[header_key]
				else:
					api_index[header_key] = response.headers[header_key]
				print(f'	{header_key}:', api_index[header_key])

			#updates the class variable api_index
			CoinAPI.api_index[api_key_id] = api_index
			#then saves the api_index to file
			with open(self.api_index_path, 'w') as file:
				json.dump(CoinAPI.api_index, file, indent=4)

			return response.json()


	#this filters through list of dictionaries based on given filter values 
	#example: (filters={filter_key: filter_item, ...})
	def JsonFilter(self, raw_json, filters, omit_filtered):
		requested_data = []

		if omit_filtered == True:
			for item in raw_json:
				item_score = 0#if it equals zero, it appends to requested_data

				for key, filter_values in filters.items():#for each filter
					if self.CheckForKey(key, item) == True:#checks to see if item has key
						for filter_item in filter_values:#compare item to each filter_item
							if item[key] == filter_item:
								item_score += 1#if they have the same value, add one to score
				if item_score == 0:#if any raw_json value is equal to any filter value, it is omitted
					requested_data.append(item)

		elif omit_filtered == False:
			for item in raw_json:
				item_score = 0#if it equals to number of filters it appends to requested_data

				for key, filter_values in filters.items():#for each filter
					if self.CheckForKey(key, item) == True:#checks to see if item has key
						for filter_item in filter_values:#compare item to each filter_item
							if item[key] == filter_item:
								item_score += 1#if item has the same value as filter, add one to score
				if item_score >= len(filters):#if the item has equivalent filter values it "passes"
					requested_data.append(item)
			#print(requested_data)
		return requested_data

	'''kwargs: 
	url_ext=str, 
	omit_filtered=bool, 
	filters={str(search_term): list(search_values), ...}, 
	api_key_id=str(api_key_id)
	return_type=str(return_type) ex:'json'
	
	queries = dict("query_variable": "query_value", ...)
	#queries not used by self.MakeRequest(), it is handed directly to self.__RequestHandler()
	'''
	def MakeRequest(self, **kwargs):
		if 'return_type' not in kwargs:
			kwargs['return_type'] = ''

		try:
			api_key_id = kwargs["api_key_id"]
			print('using specified api key:', api_key_id)
		except:
			api_key_id = 'free_key'
			print("using default api key:", api_key_id)

		try:
			queries = kwargs['queries']
		except:
			print('no queries set')
			queries = {}

		response = self.__RequestHandler(kwargs["url_ext"], api_key_id, queries)

		try:#Response Filter
			filters = kwargs["filters"]
			for key, item in filters.items():
				if type(item) is not list:
					filters_list = []
					filters_list.append(filters[key])
					filters[key] = filters_list
			try:
					omit_filtered = bool(kwargs["omit_filtered"])
			except:
				omit_filtered = False
			filtered_response = self.JsonFilter(response, filters, omit_filtered)
		except:
			print("no datastream filter")
		else:
			filter_config = ""
			for key, item in filters.items():
				filter_config = filter_config + f"{key}, {item} | "
			print("API Response Filter Executed:")
			if omit_filtered == True:
				print('   ', filter_config, "filtered terms omitted\n")
			elif omit_filtered == False:
				print('   ', filter_config, "filtered terms added\n")
			return filtered_response


		#put this at the end, will only proc when it is no other type of request
		if kwargs['return_type'] == 'json':
			return response.json()
		else:
			return response