
import requests
from requests.exceptions import HTTPError

import json
import csv

import time

import os

class CoinAPI():
	def __init__(self):
		self.base_url = 'https://rest.coinapi.io/v1/'
		self.free_key = {'X-CoinAPI-Key': key here}
		self.startup_key = {'X-CoinAPI-Key': key here}
		self.api_keys = {'free_key': self.free_key, 'startup_key': self.startup_key}

		self.api_index_path = 'api_index.json'

		self.tracked_index_variables = ['limit', 'remaining', 'reset']
		self.api_index = {}#default created in for loop below
		current_time = time.time()
		#if you change the following, also change self.UpdateAPIIndex() Function accordingly
		for api_key, api_key_value in self.api_keys.items():
			limit = 0
			if api_key == 'free_key':
				limit = 100
			elif api_key == 'startup_key':
				limit = 1000
			index_values = {'api_key': api_key_value}#api_key
			#default values, must be the same as self.tracked_index_variables
			index_values.update({'limit': limit, 'remaining': limit, 'reset': 0})
			self.api_index.update({api_key: index_values})

		self.UpdateAPIIndex()

			
	def UpdateAPIIndex(self):
		#sets object variable to file data if available and without exceptions
		try:
			with open(self.api_index_path, 'r') as file:
				api_index_file = json.load(file)

			for api_key, api_item in self.api_index.items():
				for index_item in self.tracked_index_variables:
					api_item[index_item] = api_index_file[api_key][index_item]
		except:
			print("api_index.json failed to load data, setting to defaults")
			#if file does not exist, program will crash
			

		with open(self.api_index_path, 'w') as file:
			json.dump(self.api_index, file, indent=4)


	'''kwargs: NOT AN ACTUAL KWARG, it just gets handed kwargs from self.MakeRequest
	queries = dict("query_variable": "query_value", ...)
	'''
	def __RequestHandler(self, url_ext, api_key_id, queries):
		url = self.base_url + url_ext
		api_key = self.api_index[api_key_id]['api_key']
		try:
			print("Making API Request at:", url)
			response = requests.get(url, headers=api_key, params=queries)
			# If the response was successful, no Exception will be raised
			response.raise_for_status()
		except HTTPError as http_err:
			print(f'{http_err}')
			#if error code 429 (api limit has been reached) 
			#the limit in api_index is set to zero for the api key used
			if response.status_code == 429:
				self.api_index[api_key_id]['remaining'] = 0
				self.UpdateAPIIndex()
		except Exception as err:
			print(f'{err}')
		else:
			print(f'API Request Successful: code {response.status_code}')
			return response.json()

	def CheckForKey(self, key_ref, dictionary):
		has_key = False
		for key, item in dictionary.items():
			if key == key_ref:
				has_key = True
		return has_key

	#this filters through list of dictionaries based on given filter values 
	#example: (filters={filter_key: filter_item, ...})
	def JsonFilter(self, dict_list, filters, omit_filtered):
		requested_data = []

		if omit_filtered == True:
			for item in dict_list:
				item_score = 0#if it equals zero, it appends to requested_data

				for key, filter_values in filters.items():#for each filter
					if self.CheckForKey(key, item) == True:#checks to see if item has key
						for filter_item in filter_values:#compare item to each filter_item
							if item[key] == filter_item:
								item_score += 1#if they have the same value, add one to score
				if item_score == 0:#if any dict_list is equal to any filter, it is omitted
					requested_data.append(item)

		elif omit_filtered == False:
			for item in dict_list:
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

	queries = dict("query_variable": "query_value", ...)
	#queries not used by self.MakeRequest(), it is handed directly to self.__RequestHandler()
	'''
	def MakeRequest(self, **kwargs):
		try:
			try:
				api_key_id = kwargs["api_key_id"]
				print('using specified api key')
			except:
				api_key_id = 'free_key'
				print("using default api key")

			try:
				queries = kwargs['queries']
			except:
				print('no queries set')
				queries = {}
			response = self.__RequestHandler(kwargs["url_ext"], api_key_id, queries)
		except:
			print("Exception: request failed, check url_ext")
		else:
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
	
				if omit_filtered == True:
					print(filter_config, "searched terms isolated")
				elif omit_filtered == False:
					print(filter_config, "searched terms isolated")
				print("API Response Filter Executed")
				return filtered_response


			#put this at the end, will only proc when it is no other type of request
			print("General Request Executed")

			return response.json()