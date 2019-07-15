
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

	def MakeRequest(self, url_ext, search_key, search_ids):
		url = self.base_url + url_ext
		try:
			response = requests.get(url, headers=self.key)
			# If the response was successful, no Exception will be raised
			response.raise_for_status()
		except HTTPError as http_err:
			print(f'{http_err}')
		except Exception as err:
			print(f'{err}')
		else:
			print(f'Success!: {response.status_code}')
			response_json = response.json()
			requested_data = []
			for value in response_json:
				for search_id in search_ids:
					if value[search_key] == search_id:
						requested_data.append(value)

			return requested_data
