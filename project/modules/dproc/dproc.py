
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


def compute(raw_data, func, threads=multiprocessing.cpu_count(), name=''):
	'''
	parameters:
		raw_data  : {key: pd.DataFrame(), ...} (dict) key is printed to console
		func      : the function each thread will perform to "raw_data" (lambda)
		threads   : Total threads that will be created (int) min is implicitly 2
		name      : Name of computation, only used to print
	'''

	#instance of multiprocessing.Manager for shared variables
	manager = Manager()

	#this determines total computations and creates shared dict "progress"
	compute_total = 0
	progress = manager.dict()
	progress.update({'part': 'initializing'}) 
	#printed by thread monitor, updated by main thread
	progress.update({'count': manager.dict()})
	#used to track number of completed items
	progress.update({'threads': manager.dict()})
	#each thread will create an item with key=proc_id and value=0 at initialization
	#	(except for thread_monitor) unless an item already exists with their proc_id

	#the thread_monitor is not included in proc_threads and takes up one thread
	proc_threads = threads - 1
	if proc_threads < 1:
		proc_threads = 1

	print(f'\nComputing {name} / {compute_total} items')

	#initializes monitoring thread
	proc_monitor = Process(target=thread_monitor, args=(progress, compute_total, threads))
	proc_monitor.start()

	for key, df in raw_data.items():
		
		#current df total rows
		df_len = len(df.index)
		#rough number of rows each thread is responsible for computing
		proc_len = int(df_len / proc_threads)

		if proc_threads > df_len:
			print('WARNING: More threads than compute items, dproc.compute()')

		#first index of the df (may not be 0)
		init_index = df.index[0]
		#end index of the df (may not be df_len)
		last_index = df.index[-1]

		#initializes threads with a specified proc interval and proc_num
		start_index = 0
		procs = []
		for proc_num in range(proc_threads):
			#determines the last index for compute interval
			end_index = start_index + proc_len
			if end_index > last_index - init_index:
				end_index = last_index - init_index

			proc_interval = df.index[start_index:end_index]

			proc = Process(target=func, args=(proc_interval, df, progress, proc_num,))
			procs.append(proc)
			proc.start()

		#ends multithreaded processes
		for proc in procs:
			proc.join()


			start_index = end_index


def proc_id(part, proc_num):
	return f'{part}|{proc_num}'


def prep_train_data(interval, df, progress, proc_num=0):
	'''
	Parameters:
		interval      : list of indexes that this function will compute (list(int))
		df            : complete dataset, is only read for reference (pd.DataFrame())
		progress      : shared dict for tracking progress across threads (Manager.dict())
		proc_num      : unique thread id assigned by dproc.compute() when multithreading

	returns computed slice of ref_df outlined by proc_interval
	'''

	proc_id = proc_id(progress['part'], proc_num)

	#data that will be computed
	df_slice = df.loc[proc_interval, :]

	#iterates through target df_slice rows
	init_index = df_slice.index[0]
	for index, row in df_slice.iterrows():
		for col in initial_data.columns:

			if 'is_nan' in col:
				if np.isnan(row[col]):
					new_data.at[index, col] = 1 #is_nan = true

			if 'average_price' in col:
				low = initial_data.at[index, col.replace('average_price', 'price_low')]
				high = initial_data.at[index, col.replace('average_price', 'price_high')]
				average = (low + high) / 2
				new_data.at[index, col] = average

		if (index - init_index) % 1000 == 0:
			progress[]