
#dproc
from ._proctools import *

#standard libraries
import math
import time
import datetime

import numpy as np
import pandas as pd

import multiprocessing
from multiprocessing import Manager


def prep_train_data(data):
	'''
	Parameters:
		data  : {key: pd.DataFrame(), ...}
	'''

	for filename

	#determines the values of the price_average column and inserts it into df
	price_low = df.loc[:, 'price_low'].values
	price_high = df.loc[:, 'price_high'].values
	price_average = np.divide(np.add(price_low, price_high), 2)

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

	return df


def compute(data, func, data_index={}, threads=multiprocessing.cpu_count(), name=''):
	'''
	Note: This funtion assumes that the df increment is continuous and empty rows are
			have np.nan values for all columns with no data

	parameters:
		data        : {key: pd.DataFrame(), ...} (dict) key == filename to df index
		func        : the function each thread will perform to "data" (lambda)
		data_index  : the entire index of ALL given data (not all computaions need it)
		threads     : Total threads that will be created (int) min is implicitly 2
		name        : Name of computation, only used to print

	Assumptions:
		- "data" (parameter) keys can be used to access that df's data_index
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


def gen_trend_data(interval, df, df_index, progress, proc_id=0):
	'''
	Parameters:
		interval  : list of indexes this thread will compute from df (list)
		df        : the DataFrame that this thread will work off (pd.DataFrame())
		df_index  : the data index regarding only the given df (dict)
		progress  : shared dict for tracking progress across threads (Manager.dict())
		proc_num  : number used to identify each thread in progress dict (int)

	Assumptions:
		- df.index values are incrementing by 1
		- df_index['predictions_steps'] is a positive integer greater than 0
		- df has the following columns:
			[time_period_start', 'price_average', 'isnan']
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