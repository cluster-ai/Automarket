
#third-party packages
import pandas as pd
import numpy as np

#local modules
from modules.database import Database

'''
Feature will be a class used to create a group of features for any
historical dataframe. The idea is to have the feature object be 
an instruction manuel/translator to convert historical data into 
the desired featured data.

The processed data will be saved to feature data.
The feature data will be grouped by coin-exchange pair and time_period.

file structure:
feature_data:
	coin_id1:
		feature1.csv
		feature2.csv
		feature3.csv
	coin_id2:
		feature1.csv
		feature2.csv
	feature_index.csv
'''

class Feature():
	#location of feature_data files/directories
	base_path = 'database/feature_data'
	index_path = base_path + '/feature_index.json'

	#dict with data regarding stored feature_data
	index = {}

	def __init__(self):
		#loads base paths
		if os.path.isdir(Feature.base_path) == False:
			os.mkdir(Feature.base_path)

		if os.path.isdir(Feature.index_path) == False:
			os.mkdir(Feature.index_path)

		#creates instance of database
		self.database = Database()

		#loads hand