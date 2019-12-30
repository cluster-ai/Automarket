
#standard libraries
import math
import time
import datetime

import numpy as np
import pandas as pd
import multiprocessing
from multiprocessing import Manager


'''
The compute() function is the primary object used in this module
and handles management of threads. Call it for any/all multiproc
applications.

The functions made for compute() can be used on their own with the 
right implementation. It is still recommended to use compute()
with threads=1 when single threaded processing is needed.
'''


def proc_id(part, proc_num):
	return f'{part}|{proc_num}'


def compute(data, func, data_index={}, threads=multiprocessing.cpu_count(), name=''):
	'''
	Note: This funtion assumes that the df increment is constant and missing data
		  values are equal to np.nan

	parameters:
		data       : (dict) {key: pd.DataFrame(), ...} key == filename in data_index
		func       : (funct obj) the function each thread will execute on "data"
		data_index : (dict) data index of ALL given data (if func explicitly needs it)
		threads    : (int) num threads that will be created, minimum is implicitly 2
		name       : (str) name of computation, only used to print

	NOTE: the "func" parameter is only designed to accept functions purpose built 
		  for the compute() function object argument 

	Assumptions:
		- Each "data" dataframe is paired with the same key used to access the data_index
	'''

	#total number of df rows to compute
	compute_total = 0
	for key, df in data.items():
		compute_total += len(df.index)

	#instance of multiprocessing.Manager for shared variables
	manager = Manager()
	#this determines total computations and creates shared dict "progress"
	progress = manager.dict()
	#printed by thread monitor, updated by main thread
	progress.update({'part': 'initializing'}) 
	#used to track number of completed items
	progress.update({'count': manager.dict()})
	#each thread will create an item with key=proc_id and value=proc_num
	#	main thread will wipe this after every part
	progress.update({'threads': manager.dict()})

	#the thread_monitor is not included in proc_threads and takes up one thread
	proc_threads = threads - 1
	if proc_threads < 1:
		proc_threads = 1

	print(f'\nComputing {name} / {compute_total} items')

	#initializes monitoring thread
	proc_monitor = Process(target=thread_monitor, args=(progress, compute_total, threads))
	proc_monitor.start()

	for key, df in data.items():
		#resets the index of df
		df.reset_index(drop=True, inplace=True)
		
		#current df total rows
		df_len = len(df.index)
		#rough number of rows each thread is responsible for computing
		proc_len = int(df_len / proc_threads)

		if proc_threads > df_len:
			print('WARNING: More threads than compute items, dproc.compute()')

		#initializes threads with a specified proc interval and proc_num
		start_index = 0
		last_index = df_len - 1
		procs = []
		for proc_num in range(proc_threads):
			proc_id = proc_id(key, proc_num)

			#determines the last index for compute interval
			end_index = start_index + proc_len
			if end_index > last_index:
				end_index = last_index

			interval = df.index[start_index:end_index]

			if data_index == {}:#has data index
				proc = Process(target=func, args=(interval, df, data_index, 
												  progress, proc_id,))
			else:#does not have data index
				proc = Process(target=func, args=(interval, df, progress, proc_id,))
			procs.append(proc)
			proc.start()

			start_index = end_index 

		#ends multithreaded processes
		for proc in procs:
			proc.join()

		#wipes threads in shared dict
		progress['threads'] = manager.dict()


def print_progress_bar(iteration, total, prefix = '', suffix = ''):
	#these varibales used to be parameters but there is no need to have them change
	length = 49
	fill = '/'
	printEnd = "\r"
	decimals = 1

	'''
	Call in a loop to create terminal progress bar
	Parameters:
		iteration   - Required : (Int) current iteration
		total       - Required : (Int) total iterations
		prefix      - Optional : (Str) prefix string
		suffix      - Optional : (Str) suffix string
		decimals    - Optional : (Int) positive number of decimals in percent complete
		length      - Optional : (Int) character length of bar
		fill        - Optional : (Str) bar fill character
		printEnd    - Optional : (Str) end character (e.g. "\r", "\r\n")
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
		progress      : (Manager.dict()) number of computed items from each thread
		compute_total : (int) total number of items to be computed
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


def update_progress(progress, proc_id):
	'''
	Note: Used by processing threads to update their progress

	Parameters:
		progress : (Manager.dict()) see dproc.compute() for details
		proc_id  : (str) unique identifier for progress dict
	'''

	#updates completed computaion count for specified proc_id
	if proc_id in progress['count']:
		progress['count'][proc_id] += 1
	else:
		progress['count'].update({proc_id: 1})

	#creates an indicator of this threads existance if one does not exist
	if proc_id not in progress['threads']:
		progress['threads'].update({proc_id: 0})


#################################################################
###multiproc.compute() OBJECTS BEYOND THIS POINT


def trend(interval, df, df_index, progress, proc_id=0):
	'''
	Parameters:
		interval : (list) list of indexes this thread will compute from df
		df       : (pd.DataFrame()) the DataFrame that this thread will work off
		df_index : (dict) the data index regarding only the given df
		progress : (Manager.dict()) shared dict for tracking progress across threads
		proc_num : (int) number used to identify each thread in progress dict

	Assumptions:
		- df.index values are incrementing by 1 continuously
		- df_index['predictions_steps'] is a positive integer greater than 0
		- df has the following columns: ['time_period_start', 
										 'price_average', 
										 'isnan']
		- df.isnan values are 0 if False and 1 if True
	'''

	#creates the trend column and initializes values as np.nan
	df['trend'] = np.nan

	init_index = df.index[0]
	last_index = len(df.index)-1 + init_index

	#slices the df so that only df[interval] rows remain in df_slice
	df_slice = df.loc[interval, :]

	#df_index data used for following computation
	pred_steps = df_index['prediction_steps']

	#iterates through df_slice and calculates trend data based on 
	#	the next "predictions_steps" datapoints from df(not the slice)
	first_index = df_slice.index[0]
	for index, row in df_slice.iterrows():
		#updates shared dict for thread monitor
		update_progress(progress, proc_id)

		pred_index = index + pred_index

		if pred_index > last_index:
			#if the next set of future data is not in the bounds of df,
			#	skip this row
			continue

		#creates df of all data needed for computing target val for current row
		future_df = df.loc[range(index, pred_index), :]

		#isnan is 1 if true and 0 if false so adding row gives you an isnan total
		isnan_percent = np.sum(future_df.isnan) / pred_steps * 100
		#filters out rows with more than specified number of missing datapoints (isnan==1)
		if isnan_percent > 10:
			continue

		#drops all rows with missing datapoints (the index at each row is unchanged)
		future_df = future_df[future_df.is_nan == 0]

		x_values = future_df.index
		y_values = future_df.price_average
		#components of linear regression
		x_mean = np.mean(x_values, dtype=np.float64)
		y_mean = np.mean(y_values, dtype=np.float64)
		x_sum = np.sum(x_values)
		y_sum = np.sum(y_values)
		xy_sum = np.sum((x_values*y_values))
		x_sqr_sum = np.sum((x_values**2))
		x_sum_sqr = np.sum(x_values) ** 2
		#linear regression calculation
		m = (xy_sum - (x_sum*y_sum)/n)/(x_sqr_sum - x_sum_sqr/n)

		#saves trend value to current index of df_slice
		df_slice.at[index, col] = m

	return df_slice