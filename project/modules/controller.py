
#standard libraries
import json
import os
import time

#third-party packages
import pandas as pd
import numpy as np

#local modules
from define import *
from .preproc import unix_to_date, date_to_unix
import modules.feature as feature

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
controller.py design target:
	Any control with the potential to be facilitated 
	by the user is to be put in this class.
	This is the only function currently integrated
	with the grapher module (GUI)
'''

class Controller():

	def __init__(self):
		pass


	def backfill(self, coin_id, time_increment, limit=None):
		'''
		This function accepts a coin_id and backfills all 
		tracked exchanges for that coin unless a specific 
		exchange_id is given

		Parameters:
			coin_id        : (str) crytpocurrency id: 'BTC'
								   - the currency being backfilled
			limit          : (int) limit for each coinapi request
		'''

		#verifies coin_id and time_increment parameters
		if Coinapi.verify_increment(time_increment) == False:
			return None
		elif coin_id not in Database.settings['tracked_coins']:
			print(f'WARNING: "{coin_id}" is not being tracked')
			return None

		print('----------------------------------------------------')
		print('Backfilling Historical Data')

		#loads an index_id for each tracked exchange
		backfill = {}
		match_date = None
		no_match = False
		for tracked_exchange in Database.settings['tracked_exchanges']:
			#generates index_id
			index_id = Database.index_id(tracked_exchange, coin_id,
										 time_increment)
			#loads id into backfill dict
			backfill.update({index_id: tracked_exchange})

			#generates historical_item for current item
			#if it doesn't already exist
			if index_id not in Database.historical_index:
				Database.add_historical_item(tracked_exchange, coin_id, 
											 time_increment)

			#loads index of current item
			item_index = Database.historical_index[index_id]

			#determines index_id with most recent 'data_end' value
			if match_date == None:
				#initializes match_date for first item
				match_date = item_index['data_end']
			elif (date_to_unix(match_date) < 
					date_to_unix(item_index['data_end'])):
				no_match = True #true if data_end does not all match
				#determines if current item has more recent data_end
				#than the other items so far
				match_date = item_index['data_end']

		#period_id string equivalent to time_increments
		period_id = Coinapi.period_id(time_increment)

		if no_match == True:
			print(f"NOTICE: backfill items don't match")

		#The following backfills all items items in backfill
		for index_id, exchange_id in backfill.items():
			#loads the index of current item
			item_index = Database.historical_index[index_id]
			#location of historical_data file for current item
			filepath = item_index['filepath']

			#doesn't backfill past match_date if no_match==True
			new_limit = limit
			if no_match == True:
				#match_limit is the number of requests to reach match_date
				match_limit = (date_to_unix(match_date) - 
							   date_to_unix(item_index['data_end']))
				match_limit = match_limit / item_index['time_increment']
				#limit will not be higher the given parameter 'limit'
				if match_limit < limit:
					new_limit = match_limit

			#requests backfill data
			response = Coinapi.historical(item_index, new_limit)

			#extracts data and time_end from response
			data = response['data']
			time_start = response['time_start']
			time_end = response['time_end']

			#loads existing data and adds new data to it
			if (os.path.exists(filepath) == True and 
					item_index['datapoints'] > 0):
				#if there is existing_data, data is appended to it
				existing_data = pd.read_csv(filepath)

				#makes existing_data.index equal to 'time_period_start'
				existing_data.set_index('time_period_start', drop=False,
										inplace=True)

				#adds new data to existing
				existing_data = existing_data.append(data)
			else:
				#if no data is found then existing_data = response_data
				print('No existing data for:', filepath)
				existing_data = data

			#saves new data to file
			existing_data.to_csv(filepath, index=False)

			#loads index and changes values according to new data
			index_item = Database.historical_index[index_id]
			#datapoints
			index_item['datapoints'] = len(existing_data.index)
			#data_end 
			index_item['data_end'] = time_end

			#updates historical_index with changes and saves to file
			Database.historical_index[index_id] = index_item
			Database.save_files()

		print('Backfill Complete')


	def add_historical_item(self, exchange_id, coin_id, time_increment):
		'''
		Adds historical item to historical_index

		Parameters:
			coin_id        : (str) crytpocurrency id: 'BTC'
			time_increment : (int) time increment of data in seconds
						  - val must be supported by coinapi period_id
			exchange_id    : (str) name of exchange in bold: 'KRAKEN'
		'''
		#verifies that parameters are supported by coinapi
		if Coinapi.verify_increment(time_increment) == False:
			return None
		elif coin_id not in Database.settings['tracked_coins']:
			print(f'WARNING: "{coin_id}" is not being tracked')
			return None
		elif exchange_id != None:
			if (exchange_id not in 
					Database.settings['tracked_exchanges']):
				print(f'WARNING: "{exchange_id}" is not being tracked')
				return None

		#index_id used as a key for historical_index items
		index_id = Database.index_id(exchange_id, coin_id, time_increment)

		#stops function if item already found in historical_index
		if index_id in Database.historical_index:
			print(f'NOTICE: Historical Index already has {index_id}')
			return None

		#period_id string equivalent to time_increments
		period_id = Coinapi.period_id(time_increment)

		#the first dir is the period_id str associated to time_increment
		filepath = Database.historical_base_path + f'/{period_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)
		#the final dir is the coin_id
		filepath += f'/{coin_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)

		#loads coin_data for new index_item
		coin_data = Database.coin_index[exchange_id][coin_id]

		#filename-example: 'KRAKEN_BTC_5MIN.csv'
		filename = f'{index_id}.csv'
		filepath = filepath + f'/{filename}' #adds filename to dir
		#creates file if there is none
		if os.path.exists(filepath) == False:
			open(filepath, 'w')

		#fills out required information for new 
		#historical index_item
		index_item = {
			'filename': filename,
			'filepath': filepath,
			'symbol_id': coin_data['symbol_id'],
			'exchange_id': exchange_id,
			'asset_id_quote': coin_data['asset_id_quote'],
			'asset_id_base': coin_data['asset_id_base'],
			'period_id': period_id,
			'time_increment': time_increment,
			'datapoints': 0,
			'data_start': coin_data['data_start'],
			'data_end': coin_data['data_start']#not a typo
		}

		print(f'Added {index_id} to Historical Index')

		#updates historical_index
		Database.historical_index.update({index_id: index_item})
		#saves changes to file
		Database.save_files()


	def add_feature_group(self, index_id):
		'''
		creates a new feature group and adds it to features_index

		Parameters:
			index_id   : (str) id used for the feature group
						  (it is the same as historical_data)
			feature_id : (str) id used for a single feature
							   within a feature group
			data       : (pd.Series) data that will overwrite 
							the current items in feautre 
		'''

		#verifies given index_id
		if index_id not in Database.historical_index:
			raise KeyError(f'"{index_id}" not in Historical Index')

		#verifies index_id not already in features_index
		if index_id in Database.features_index:
			print(f'NOTICE: {index_id} already in Features Index')

		#historical index data from index_id
		hist_index = Database.historical_index[index_id]

		###################################################
		###Verify Feature Group

		#the first dir is the period_id str associated to time_increment
		filepath = Database.features_base_path + f'/{period_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)
		#the next dir is the coin_id
		filepath += f'/{coin_id}'
		if os.path.isdir(filepath) == False:
			os.mkdir(filepath)
		#the final dir is the index_id
		filename = f'{index_id}.csv'
		filepath += f'/{filename}'

		#if either index or file not found, re-initialize feature-group
		if (os.path.exists(filepath) == False or 
				index_id not in Database.features_index):

			#creates new file if one is not found
			if os.path.exists(filepath) == False:
				open(filepath, 'w')
			
			#overwrites file with time_period_start col from historical
			df = Database.historical(index_id).loc[:, ['time_period_start']]
			df.to_csv(filepath, index=False)

			index_item = {
				'filename': filename,
				'filepath': filepath,
				'features': {},
				'symbol_id': hist_index['symbol_id'],
				'exchange_id': hist_index['exchange_id'],
				'asset_id_quote': hist_index['asset_id_quote'],
				'asset_id_base': hist_index['asset_id_base'],
				'period_id': hist_index['period_id'],
				'time_increment': hist_index['time_increment'],
				'even_features': False,
				'data_start': hist_index['data_start'],
				'data_end': hist_index['data_start']#not a typo
			}

			print(f'Added {index_id} to Features Index')

			#updates historical_index
			Database.features_index.update({index_id: index_item})
			#saves changes to file
			Database.save_files()


	def create_feature(index_id, columns, name):
		'''
		Creates a custom feature with a single feature func.
		The user can request multiple columns be returned
		but it will be packaged as individual features with
		the same user given id extension.

		Parameters:

		'''
		#loads feature group
		group_index = Database.features_index[index_id]

		#verifies that feature does not exist
		if feature_id not in group_index['features']:
			#update features_index with feature
			Database.features_index[index_id]['features'].update(feature_id)
			print(f'Added {feature_id} to {index_id} Feature Group')
		else:
			print(f'NOTICE: {feauture_id} already exists for {index_id}')


	def update_feature(historical, feature_id):
		pass


	def generate_data(historical, feature_id):
		'''
		Generates feature data
		'''
		pass