
#standard libraries
import math
import time
import datetime

import numpy as np
import pandas as pd


def unix_to_date(unix):
	#the datetime package is only accurate to 6 decimals but 7 are 
	#needed for date format being used. Since the decimal value is 
	#the same regardless of unix or date, I have it copied over
	#from unix and converted to string then added to date between
	#the '.' and 'Z' characters

	#gets the string of int(unix_decimal * 10^7)
	decimal = round((unix % 1 * (10**7)))
	decimal = str(int(decimal))
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
	#This function accepts two formats:
	#   "%Y-%m-%dT%H:%M:%" and "%Y-%m-%d"
	if 'T' in date:
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
	else:
		#this assumes format is "%Y-%m-%d"
		#date string is converted to datetime value
		unix = datetime.datetime.strptime(date, '%Y-%m-%d')
		#datetime value is converted to unix value in UTC timezone as int
		unix = unix.replace(tzinfo=datetime.timezone.utc).timestamp()

	return unix


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