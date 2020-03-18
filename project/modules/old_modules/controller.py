
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