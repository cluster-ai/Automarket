
import requests
from requests.exceptions import HTTPError

import json
import csv

'''url = 'https://rest.coinapi.io/v1/assets'
headers = {'X-CoinAPI-Key' : '4364DC07-0336-4C8A-A43C-2BD216B1B285'}
response = requests.get(url, headers=headers)

print(response)'''


class CoinAPI():
	def __init__(self):
		self.base_url = 'https://rest.coinapi.io/v1/'
		self.free_key = get your own
		self.paid_key = get your own

	def __RequestHandler(self, url_ext, api_key):
		url = self.base_url + url_ext
		try:
			print("Making API Request at:", url)
			response = requests.get(url, headers=api_key)
			# If the response was successful, no Exception will be raised
			response.raise_for_status()
		except HTTPError as http_err:
			print(f'{http_err}')
		except Exception as err:
			print(f'{err}')
		else:
			print(f'API Request Successful: code {response.status_code}')
			return response

	def CheckForKey(self, key_ref, dictionary):
		has_key = False
		for key, item in dictionary.items():
			if key == key_ref:
				has_key = True
		return has_key


	def ResponseFilter(self, response, filters, omit_filtered):
		requested_data = []

		if omit_filtered == True:
			for response_item in response.json():
				response_item_score = 0#if it equals zero, it appends to requested_data

				for key, filter_values in filters.items():#for each filter
					if self.CheckForKey(key, response_item) == True:
						for filter_item in filter_values:#compare response_item to each filter_item
							if response_item[key] == filter_item:
								response_item_score += 1
				if response_item_score == 0:
					requested_data.append(response_item)

		elif omit_filtered == False:
			for response_item in response.json():
				response_item_score = 0#if it equals to number of filters it appends to requested_data

				for key, filter_values in filters.items():#for each filter
					if self.CheckForKey(key, response_item) == True:
						for filter_item in filter_values:#compare response_item to each filter_item
							if response_item[key] == filter_item:
								response_item_score += 1
				if response_item_score >= len(filters):
					requested_data.append(response_item)
			#print(requested_data)
		return requested_data

	#def TypeError

	'''kwargs: 
	url_ext=str, 
	omit_filtered=bool, 
	filters={str(search_term): list(search_values)}, 
	api_key={'X-CoinAPI-Key': 'actual_api_key_code'}...}'''
	def MakeRequest(self, **kwargs):
		try:
			try:
				api_key = kwargs["api_key"]
			except:
				api_key = self.free_key
				print("using default api key")
			else:
				print("using specified api_key")
			response = self.__RequestHandler(kwargs["url_ext"], api_key)
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
				filtered_response = self.ResponseFilter(response, filters, omit_filtered)
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