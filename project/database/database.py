
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
			self.config = self.handbook['config']
			#self.exchanges = self.handbook['exchanges']

		if int(self.config['last_update']) + self.config['update_frequency'] < int(time.time()):
			print('Updating handbook.json')
			self.UpdateHandbook()
		else:
			print('handbook.json up to date, next update after', 
				 self.SetUnixToDate(self.handbook['config']['last_update'] + 
				 					self.config['update_frequency']))

	def UpdateHandbook(self):
		url_ext = self.config['url_ext']
		response = self.coin_api.MakeRequest(url_ext, 'exchange_id', 
											self.config['tracked_exchanges'])
		exchanges = {}
		for value in response:
			for ex in self.config['tracked_exchanges']:
				if ex == value['exchange_id']:
					exchange = {value['exchange_id'] : value}
					exchanges.update(exchange)
		self.exchanges = exchanges

		self.config['last_update'] = int(time.time())

		updated_handbook = {}
		updated_handbook.update({'config' : self.config})
		updated_handbook.update({'exchanges' : self.exchanges})
		self.handbook = updated_handbook
		#handbook_json = json.dumps(self.handbook, indent=4, separators=(',', ': '))
		with open(self.handbook_pwd, 'w') as json_file:
			json.dump(self.handbook, json_file, indent=4)

	def SetUnixToDate(self, unix):#input unix time as string or int
		return datetime.datetime.utcfromtimestamp(unix).strftime(' %m/%d/%Y %I:%M %p')



data = Database()