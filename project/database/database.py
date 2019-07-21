
import json

import time
import datetime

import coin_api

class Database():
	def __init__(self):
		self.coin_api = coin_api.CoinAPI()
		self.handbook_path = 'data/handbook.json'
		self.config_path = 'config.json'
		self.missing_data = False

		with open(self.handbook_path) as file:
			self.handbook = json.load(file)
			try:
				self.exchange_data = self.handbook['exchange_data']
				self.period_data = self.handbook['period_data']
			except:
				self.missing_data = True

		with open(self.config_path) as file:
			self.config = json.load(file)
				

		'''if int(self.config['last_update']) + self.config['update_frequency'] < int(time.time())
			   or self.config['update_limiter'] == False or self.missing_data == True:'''
		print('Updating handbook.json...')
		self.UpdateHandbook()
		'''else:
			print('handbook.json up to date, next update after', 
				 self.SetUnixToDate(self.handbook['config']['last_update'] + 
				 					self.config['update_frequency']), "HST")'''

	'''only supports "SPOT" exchanges so far
	{
		"KRAKEN" :
		{
			"symbol_ids":
			[
				"KRAKEN_SPOT_BTC_USD",
				...
			],
			"KRAKEN_SPOT_BTC_USD" :
			{
				"symbol_type": "SPOT",
            	"asset_id_base": "BTC",
            	"asset_id_quote": "USD",
            	"data_start": "2015-01-14",
            	"data_end": "2019-07-21",
			}
		},
		and again for each exchange
	}
	'''

	def ExtractExchangeData(self, raw_exchange_data):
		extracted_data = {}
		for tracked_exchange in self.config['tracked_exchanges']:
			extracted_data.update({tracked_exchange : {}})

		for item in raw_exchange_data:
			for exchange_id, exchange_data in extracted_data.items():
				if exchange_id == item['exchange_id']:
					extracted_data[exchange_id].update({item["symbol_id"] : item})
					break

		return extracted_data


	#def ExtractPeriodData(self, periods):


	def UpdateHandbook(self):
		exchanges_response = self.coin_api.MakeRequest(url_ext=self.config['exchanges_url_ext'], 
									filters={'exchange_id': self.config['tracked_exchanges']})

		#periods_response = self.coin_api.MakeRequest(url_ext=self.config['periods_url_ext'])

		updated_handbook = {}
		#updated_handbook.update({'period_data' : periods_response})
		updated_handbook.update({'exchange_data' : self.ExtractExchangeData(exchanges_response)})

		self.handbook = updated_handbook
		with open(self.handbook_path, 'w') as file:
			json.dump(self.handbook, file, indent=4)

		self.config['last_update'] = int(time.time())
		self.exchange_data = self.handbook['exchange_data']
		#self.period_data = self.handbook['period_data']

		updated_config = {}
		updated_config.update(self.config)
		
		self.config = updated_config
		#handbook_json = json.dumps(self.handbook, indent=4, separators=(',', ': '))
		with open(self.config_path, 'w') as file:
			json.dump(self.config, file, indent=4)
		print("Finished: handbook.json up to date, next update after",
					self.SetUnixToDate(self.config['last_update'] + 
				 					self.config['update_frequency']), "HST")

	def SetUnixToDate(self, unix):#input unix time as string or int
		unix = unix - 36000 #UTC(default unix timezone) to HST time difference
		return datetime.datetime.utcfromtimestamp(unix).strftime(' %m/%d/%Y %I:%M %p')



data = Database()