
import requests
from requests.exceptions import HTTPError

import json

'''url = 'https://rest.coinapi.io/v1/assets'
headers = {'X-CoinAPI-Key' : '4364DC07-0336-4C8A-A43C-2BD216B1B285'}
response = requests.get(url, headers=headers)

print(response)'''


class CoinAPI():
	def __init__(self):
		self.base_url = 'https://rest.coinapi.io/v1/'
		self.key = {'X-CoinAPI-Key' : '4364DC07-0336-4C8A-A43C-2BD216B1B285'}

	def __RequestHandler(self, url_ext):
		url = self.base_url + url_ext
		try:
			print("Making API Request at:", url)
			response = requests.get(url, headers=self.key)
			# If the response was successful, no Exception will be raised
			response.raise_for_status()
		except HTTPError as http_err:
			print(f'{http_err}')
		except Exception as err:
			print(f'{err}')
		else:
			print(f'API Request Successful: code {response.status_code}')
			return response

	def RequestFilter(self, response, search_term, search_values, inverse_search):
		requested_data = []
		for value in response.json():
			inverse_search_counter = 0#needed if you have more than one search_term for inverse_search = True
			for search_value in search_values:
				if inverse_search == False and value[search_term] == search_value:
					requested_data.append(value)
				elif inverse_search == True and value[search_term] != search_value:
					inverse_search_counter += 1
					if inverse_search_counter == len(search_values):
						requested_data.append(value)

		return requested_data

	#def TypeError

	'''kwargs: url_ext, inverse_search (if true, omitt searched. default false), 
	(search_term, search_values) - package deal for search pair'''
	def MakeRequest(self, **kwargs):
		try:
			response = self.__RequestHandler(kwargs["url_ext"])
		except:
			print("Exception: request failed, check url_ext")
		else:
			try:#Filtered Search
				search_term = kwargs["search_term"]
				search_values = kwargs["search_values"]
				if type(search_values) is not list:
					print("TypeError, search_values not a list: filter failed")
					raise Exception(TypeError)
				try:
					inverse_search = bool(kwargs["inverse_search"])
				except:
					inverse_search = False
				filtered_response = self.RequestFilter(response, search_term, search_values, inverse_search)
			except:
				print("no datastream filter")
			else:
				print(f"search_term = {search_term} | search_values = {search_values}")
				if inverse_search == True:
					print("Filtered Request Executed: inverse_search = True")
				else:
					print("Filtered Request Executed: inverse_search = False")
				return filtered_response


			#put this at the end, will only proc when it is no other type of request
			print("General Request Executed")

			return response.json()