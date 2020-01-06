

#standard libraries
import math
import time
import datetime

import numpy as np


def unix_to_date(unix):
	#the datetime package is only accurate to 6 decimals but 7 are 
	#needed for date format being used. Since the decimal value is 
	#the same regardless of unix or date, I have it copied over
	#from unix and converted to string then added to date between
	#the '.' and 'Z' characters

	#gets the string of int(unix_decimal * 10^7)
	decimal = str(int(round(unix % 1 * (10**7))))
	#leads decimal with zeros so total digit count is 7
	decimal = decimal.zfill(7)

	#drops the decimal from unix
	unix = int(unix)

	#integer unix value converted to date string
	date = datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S')
	#decimal string added to datetime
	date = date + f'.{decimal}Z'

	#return format: 'yyyy-mm-ddTHH:MM:SS.fffffffZ'
	return date


def date_to_unix(date):
	#the datetime package is only accurate to 6 decimals but 7 are 
	#needed for date format being used. Since the decimal value is 
	#the same regardless of unix or date, I have it copied over
	#from date and converted to float then added to unix
	start = date.find('.') + 1 #first decimal value index
	end = date.find('Z') #the index of value that ends decimal string

	#extracts first 7 digits of decimal
	decimal = str(round(float(date[start:end])))

	#new date without decimal
	date = date[0:start-1]

	#date string is converted to datetime value
	unix = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
	#datetime value is converted to unix value in UTC timezone as int
	unix = str(int(unix.replace(tzinfo=datetime.timezone.utc).timestamp()))
	#adds decimal to unix
	unix = float(f'{unix}.{decimal}')

	return unix


def prep_historical(data):
	'''
	Parameters:
		data : {key/id: pd.DataFrame(), ...}
	'''
	for key, df in data.items():

		#determines the values of the price_average column and inserts it into df
		price_low = df.loc[:, 'price_low'].values
		price_high = df.loc[:, 'price_high'].values
		price_average = np.divide(np.add(price_low, price_high), 2)

		#finds index of price_low column in df
		insert_index = df.columns.index('price_low')

		df.insert(2, 'price_average', price_average)

		#iterates through df columns to see if all np.nan values are in the same places
		prev_tf_list = []
		for col in df.columns:
			tf_list = np.isnan(df.loc[:, col].values)

			if prev_tf_list == []:
				prev_tf_list = tf_list
			elif tf_list != prev_tf_list:
				raise AssertionError(f'np.isnan(df.{col}) != np.isnan(df.{col})')
			else:
				prev_tf_list = tf_list

		#takes last tf_list and uses it to generate an "isnan" column in df where 
		#	isnan == True has a value of 1 and isnan == False has a value of 0
		isnan_values = prev_tf_list
		for index, val in enumerate(prev_tf_list):
			if val == True:
				isnan_values[index] = 1
			elif val == False:
				isnan_values[index] = 0

		df.insert(len(df.columns), 'isnan', isnan_values)

		#updates data with new df
		data[key] = df

	return data


def scale(data, new_range=[0, 1], custom_scale=[0, 0], return_params=False):
	'''
	Parameters:
		data          : (list) data being scaled
		new_range     : ([float, float]) the target min max vals of scale
		custom_scale  : ([float, float]) optional - acts as custom min max vals of scale
		return_params : (bool) returns scaled_data, params instead of scaled data if True
	'''
	data = list(data)
	if custom_scale != [0, 0]:
		min_val = min(custom_scale)
		max_val = max(custom_scale)
	else:
		min_val = min(data)
		max_val = max(data)
	new_width = abs(new_range[0] - new_range[1])

	#sets data values between 0 and 1
	scaled_data = np.divide(np.subtract(data, min_val), (max_val - min_val))

	if new_range != [0, 1]:
		#adjusts to non-standard new_range if requested
		scaled_data = np.add(np.multiply(scaled_data, new_width), new_range[0])

	if return_params == True:
		orig_range = [min_val, max_val]
		scaled_zero = self.scale([0], orig_range=orig_range, new_range=new_range)
		scaled_zero = scaled_zero[0]
		params = {'orig_range': orig_range, 
				  'new_range': feature_range,
				  'scaled_zero': scaled_zero}
		return scaled_data, params

	return scaled_data