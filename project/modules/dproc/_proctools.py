

#standard libraries
import math
import time
import datetime

import numpy as np


def unix_to_date(unix):#input unix time as string or int
	#when using to display on screen, add to UTC unix param to offset for your timezone
	return datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S.%f0Z')
	#RETURNS UTC, confirmed


def date_to_unix(date):
	unix = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f0Z')
	unix = unix.timestamp() - 36000#sets it to UTC
	return unix


def scale(self, target_array, new_range=[0, 1], custom_scale=[0, 0], return_params=False):
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


def print_progress_bar(iteration, total, prefix = '', suffix = ''):
	#these varibales used to be parameters but there is no need to have them change
	length = 49
	fill = '/'
	printEnd = "\r"
	decimals = 1

	'''
	Call in a loop to create terminal progress bar
	Parameters:
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


def thread_monitor(progress, compute_total, thread_total):
	'''
	Parameters:
		progress       : number of computed items from each thread (shared dict)
		compute_total  : total number of items to be computed (int)
	'''
	prog_count = 0
	threads = 1
	while prog_count < compute_total:
		prog_part = progress['part']
		print_progress_bar(prog_count, compute_total, 
						   suffix=f' | {prog_part}, threads: {threads}/{thread_total}')

		for key, val in progress.items():
			if key == 'threads':
				#counts number of items in progress['threads']
				threads = len(val) + 1 #plus 1 for monitoring thread
			elif key == 'count':
				#adds all the item values in progress['count']
				prog_count += sum(val.values())


def proc_id(part, proc_num):
	return f'{part}|{proc_num}'


def update_progress(progress, proc_id):
	'''
	Note: Used by processing threads to update their progress

	Parameters:
		progress  : Shared Manager.dict() (see compute() for details)
		proc_id   : unique identifier so threads access correct dict items
	'''

	#updates completed computaion count for specified proc_id
	if proc_id in progress['count']:
		progress['count'][proc_id] += 1
	else:
		progress['count'].update({proc_id: 1})

	#creates an indicator of this threads existance if one does not exist
	if proc_id not in progress['threads']:
		progress['threads'].update({proc_id: 0})