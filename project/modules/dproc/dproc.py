
#dproc
from _multiproc.py import *

#standard libraries
import math
import time
import datetime

import numpy as np


def SetUnixToDate(self, unix):#input unix time as string or int
	#when using to display on screen, add to UTC unix param to offset for your timezone
	return datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S.%f0Z')
	#RETURNS UTC, confirmed


def SetDateToUnix(self, date):
	unix = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f0Z')
	unix = unix.timestamp() - 36000#sets it to UTC
	return unix


def Scale(self, target_array, new_range=[0, 1], custom_scale=[0, 0], return_params=False):
	'''
	Parameters:

	target_array   : one dimension array "target" for scaling
	new_range      : value range of data after scaling
	custom_scale   : optional - value range reference
		This is used when user wants to scale based on custom values not in target_array
	return_params  : "return scaled_data, params" rather than "return scaled_data"
	'''
	target_array = list(target_array)
	if custom_scale != [0, 0]:
		min_val = min(custom_scale)
		max_val = max(custom_scale)
	else:
		min_val = min(target_array)
		max_val = max(target_array)
	new_width = abs(new_range[0] - new_range[1])

	#sets target_array values between 0 and 1
	scaled_data = np.divide(np.subtract(target_array, min_val), (max_val - min_val))

	if new_range != [0, 1]:
		#adjusts to non-standard new_range if requested
		scaled_data = np.add(np.multiply(scaled_data, new_width), new_range[0])

	if return_params == True:
		orig_range = [min_val, max_val]
		scaled_zero = self.FeatureScale([0], orig_range=orig_range, new_range=new_range)
		scaled_zero = scaled_zero[0]
		params = {'orig_range': orig_range, 
				  'new_range': feature_range,
				  'scaled_zero': scaled_zero}
		return scaled_data, params

	return scaled_data


def PrintProgressBar(self, iteration, total, prefix = '', suffix = ''):
	#these varibales used to be parameters but there is no need to have them change
	length = 49
	fill = '/'
	printEnd = "\r"
	decimals = 1

	'''
	Call in a loop to create terminal progress bar
	@params:
		iteration   - Required  : current iteration (Int)
		total       - Required  : total iterations (Int)
		prefix      - Optional  : prefix string (Str)
		suffix      - Optional  : suffix string (Str)
		decimals    - Optional  : positive number of decimals in percent complete (Int)
		length      - Optional  : character length of bar (Int)
		fill        - Optional  : bar fill character (Str)
		printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
	'''
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
	# Print New Line on Complete
	if iteration == total: 
		print()


def ProcMonitor(self, proc_status={}):
	status = 0
	while status < self.data_index['datapoints']:
		if proc_status != {}:
			self.PrintProgressBar(0, self.data_index['datapoints'])
			while status < self.data_index['datapoints']:
				status = 0
				for proc_num, count in proc_status.items():
					status += count
					time.sleep(0.05)
				if status > self.data_index['datapoints']:
					status = self.data_index['datapoints']
				self.PrintProgressBar(status, self.data_index['datapoints'])


