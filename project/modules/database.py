
#standard libraries
import json
import os

import pandas as pd
import numpy as np

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

class Database():
	#immutable paths to different portions of database file structure
	historical_base_path = 'database/historical_data/'
	historical_index_path = (historical_base_path 
							 + 'historical_index.json')
	training_base_path = 'database/training_data/'
	training_index_path = (training_base_path
						   + 'training_index.json')
	settings_path = 'database/settings.json'

	#dict variables that track/index data in database
	historical_index = {}
	training_index = {}

	#used by the other modules to store program wide information
	settings = {}


	def __init__(self):
		#loads handbook and settings file to Database
		self.load_settings()


	def save_settings(self, settings=Database.settings):
		#saves settings dict class variable to file by default
		#can change parameter to custom settings dict
		with open(Database.settings_path, 'w') as file:
			json.dump(settings, file, indent=4)


	def load_settings(self):
		#loads contents of file with path, "Database.setting_path"
		with open(Database.settings_path) as file:
			Database.settings = json.load(file)


	def save_training_index(self):
		#saves training_index dict class variable to file
		with open(Database.training_index_path, 'w') as file:
			json.dump(Database.training_index, file, indent=4)


	def save_historical_index(self):
		#saves historical_index dict class variable to file
		with open(Database.historical_index_path, 'w') as file:
			json.dump(Database.historical_index, file, indent=4)


	def load_indexes(self):
		#loads indexes for training index
		print('Loading Training Index: '
			  + {Database.training_index_path})
		with open(Database.training_index_path) as file:
			Database.training_index = json.load(file)

		#loads indexes for historical index
		print('Loading Historical Index: '
			  + {Database.historical_index_path})
		with open(Database.training_index_path) as file:
			Database.training_index = json.load(file)


	def load_historical_data(self, index_id, interval=None):
		'''
		Parameters:
			index_id : (str) 
					   - key to select desired historical_index item
			interval : ([int, int]) None returns all available data
					   - converted to nearest time_period_start value
					   - [0] is unix time start, [1] is unix time end
		'''

		#verifies that index_id is valid
		item_index = Database.historical_index[index_id]