
#dproc
from ._proctools import *

#standard libraries
import math
import time
import datetime

import numpy as np


def unix_to_date(self, unix):#input unix time as string or int
	#when using to display on screen, add to UTC unix param to offset for your timezone
	return datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S.%f0Z')
	#RETURNS UTC, confirmed


def date_to_unix(self, date):
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


def compute(raw_data, func, threads=multiprocessing.cpu_count(), name='...'):
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
		pass


	#=======================================old code past this point


	'''
	self.new_data = raw_data
	self.data_index = data_index

	#used to calculate time delay between iterations of following loop
	init_time = time.time()


	if self.proc_type == 'training_data':
		self.InitTrainingData()


	#This sets up a batch of data for each processing thread so that all data is 
	#   processed once the last thread is reserved for monitoring progress and 
	#   does not receive a batch of data
	proc_threads = Preprocessor.thread_count - 1
	proc_length = math.ceil(self.data_index['datapoints'] / proc_threads)
	proc_intervals = []
	last_index = raw_data.index[-1]
	start_index = 0
	for thread in range(proc_threads):
		end_index = start_index + proc_length
		custom_start = start_index - self.data_index['prediction_steps']

		if thread == 0:
			proc_intervals.append(raw_data.index[start_index:end_index])
		elif thread == proc_threads-1:
			end_index = raw_data.index[-1]
			#by default python array slicing ignores last point so add one index value worth
			proc_intervals.append(raw_data.index[custom_start:end_index])
		elif custom_start < 0:
			custom_start = 0
			proc_intervals.append(raw_data.index[custom_start:end_index])
		else:
			proc_intervals.append(raw_data.index[custom_start:end_index])

		start_index = end_index

	manager = Manager()
	new_proc_data = manager.dict()
	proc_status = manager.dict()

	#uses proc_data_all in loop to set up each process for multithreading, order does not matter
	#MULTIPROC SETUP
	print("Preping Data...")
	procs = []

	#initializes the monitoring thread
	proc_monitor = Process(target=self.ProcMonitor, args=(proc_status,))
	procs.append(proc_monitor)
	procs[0].start()
	for proc_num, proc_interval in enumerate(proc_intervals):
		if self.proc_type == 'training_data':
			proc = Process(target=self.MultiprocTrainingSetup, args=(proc_interval, 
																	new_proc_data,
																	proc_status,
																	proc_num,))
			procs.append(proc)
			proc.start()

	#ends multithreaded processes
	for proc in procs:
		proc.join()
	for proc_num, dataframe in new_proc_data.items():
		self.new_data.loc[proc_intervals[proc_num], :] = dataframe.loc[proc_intervals[proc_num], :]


	raw_data = self.new_data.copy()

	#wipes new_proc_data and proc_status
	new_proc_data = manager.dict()
	proc_status = manager.dict()

	print("\nProcessing Data...")
	#MULTIPROC FINAL
	procs = []
	#initializes the monitoring thread
	proc_monitor = Process(target=self.ProcMonitor, args=(proc_status,))
	procs.append(proc_monitor)
	procs[0].start()
	for proc_num, proc_interval in enumerate(proc_intervals):
		if self.proc_type == 'training_data':
			proc = Process(target=self.MultiprocTrainingFinal, args=(proc_interval, 
																	self.data_index['prediction_steps'],
																	new_proc_data,
																	proc_status,
																	proc_num,))
		procs.append(proc)
		proc.start()
	#ends multithreaded processes
	for proc in procs:
		proc.join()
	for proc_num, dataframe in new_proc_data.items():
		self.new_data.loc[proc_intervals[proc_num], :] = dataframe.loc[proc_intervals[proc_num], :]


	total_time = time.time() - init_time
	print(f"\nTotal Duration: {total_time}")

	print(self.new_data.head(30))

	return self.new_data
	'''