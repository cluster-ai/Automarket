import json
import time

import coin_api

'''Isolate each exchanges 
config using: 
avail_exchanges = list
current_exchange = string

each exchange (symbol_id)
[
{'symbol_id' :
	{
		avail_coins (only crypto
		transaction_fee
		
	}
}
]
'''

class Database():
	def __init__(self):
		self.coin_api = coin_api.CoinAPI()

		with open('data/handbook.json') as json_file:
			self.handbook = json.load(json_file)
			self.config = self.handbook['config']
			#self.exchanges = json.load(json_file)['exchanges']

		if self.config['last_update'] + self.config['update_frequency'] < int(time.time()):
			self.UpdateHandbook()
		else:
			print('Metadata.json up to date, next update at ', 
				 (self.metadata['config']['last_update'] + self.config['update_frequency']))

	def UpdateHandbook(self):
		url_ext = self.config['url_ext']
		response = self.coin_api.MakeRequest(url_ext, 'exchange_id', self.config['tracked_exchanges'])

		exchanges = {'exchanges': {}}
		for value in response:
			for ex in self.config['tracked_exchanges']:
				if ex == value['exchange_id']:
					exchanges['exchanges'].update(value)
		self.exchanges = exchanges

		updated_handbook = {}
		updated_handbook.update(self.config)
		updated_handbook.update(self.exchanges)
		self.handbook = updated_handbook
		with open('data/handbook.json', 'w') as json_file:
			json.dump(self.handbook, json_file)



data = Database()