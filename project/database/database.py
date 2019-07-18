
import json

import time
import datetime

import coin_api

class Database():
	def __init__(self):
		self.coin_api = coin_api.CoinAPI()
		self.handbook_pwd = 'data/handbook.json'

		with open(self.handbook_pwd) as json_file:
			self.handbook = json.load(json_file)
			try:
				self.config = self.handbook['config']
			except KeyError:
				print("KeyError: handbook['config'] not found, check handbook.json")
			else:
				print("loading handbook config...")

		if int(self.config['last_update']) + self.config['update_frequency'] < int(time.time()):
			print('Updating handbook.json...')
			self.UpdateHandbook()
		else:
			print('handbook.json up to date, next update after', 
				 self.SetUnixToDate(self.handbook['config']['last_update'] + 
				 					self.config['update_frequency']), "HST")

	def UpdateHandbook(self):
		exchanges_response = self.coin_api.MakeRequest(url_ext=self.config['exchanges_url_ext'], 
													  search_term='exchange_id', 
													  search_values=self.config['tracked_exchanges'])
		periods_response = self.coin_api.MakeRequest(url_ext=self.config['periods_url_ext'],
													  search_term='length_seconds',
													  search_values=[0],
													  inverse_search=True)

		exchanges = {}
		for value in exchanges_response:
			for ex in self.config['tracked_exchanges']:
				if ex == value['exchange_id']:
					exchange = {value['exchange_id'] : value}
					exchanges.update(exchange)

		self.config['last_update'] = int(time.time())
		self.exchanges = exchanges
		self.periods = periods_response

		updated_handbook = {}
		updated_handbook.update({'config' : self.config})
		updated_handbook.update({'exchanges' : self.exchanges})
		updated_handbook.update({'periods' : self.periods})
		self.handbook = updated_handbook
		#handbook_json = json.dumps(self.handbook, indent=4, separators=(',', ': '))
		with open(self.handbook_pwd, 'w') as json_file:
			json.dump(self.handbook, json_file, indent=4)

	def SetUnixToDate(self, unix):#input unix time as string or int
		unix = unix - 36000 #UTC time difference with Hawaii
		return datetime.datetime.utcfromtimestamp(unix).strftime(' %m/%d/%Y %I:%M %p')



data = Database()