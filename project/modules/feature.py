
#standard libraries
import datetime
import time

#third-party packages
import pandas as pd
import numpy as np

#local modules
import modules.feature_func as func

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
Feature.py Design Target:
	A tool for creating feature data and
	the mechanism used to update those features.

	Features is primarily used by database to create
	features. The features and their corresponding
	item_index (used for remembering parameters) is fed 
	back into the feature class for updating. Control of 
	the stored features is facilitated by the 
	database class. An instance of the Feature class
	only controls and individual feature.

	Data fed into any feature function can be categorized 
	into 2 different camps: categorical and numerical.
	These camps are important to consider when stacking
	feature functions but may still be joinable in some
	manner. The idea behind the camps is to differentiate
	numerical data (price) and categorical data (weekday).

	Example of merging numerical and categorical features: 
		isolate one-hot encoded categorical data to 
		individual columns of bool values (1 and 0) and 
		compute it with a numerical column somehow.

	The "default" feature functions are located below, 
	outside of the feature class. They can, however, come 
	from anywhere as long as they can be used the same way.


Scope of Feature module (avoid making it a class):
 - computation that ends up with ONE column worth of 
tabular data.
 - ability to stack feature functions at initialization
 - feature id in a format that has a user given element.
 EX: {historical col}_{feature_function}_{user given id}
'''
	
'''
NOTE: for now this function CANNOT stack features

	  When I eventually incorporate custom features
	  we can have the user name the new one and store
	  the information needed to generate that data.
	  Perhaps I can only allow stacking features when
	  initially creating the feature but not allowing
	  stacking of existing features.
'''


def create_feature(columns, func, id):
	'''
	Creates a custom feature with a single feature func.
	The user can request multiple columns be returned
	but it will be packaged as individual features with
	the same user given id extension.

	Parameters:

	'''
	pass


def update_feature(historical, feature_id):
	pass


def generate_data(historical, feature_id):
	'''
	Generates feature data
	'''
	pass