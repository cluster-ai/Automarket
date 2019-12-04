
import time
import datetime
from multiprocessing import Process, Manager, Value

import multiprocessing

from multiprocessing import Process, Value, Lock, Manager
from collections import deque

import pandas as pd
import numpy as np

import math

class Preprocessor():
	proc_types = ['training_data']
	config = {}
	thread_count = multiprocessing.cpu_count()

	def __init__(self, conf={}):#initializes class variable config
		#if class has been initialized already, ignore conf
		if Preprocessor.config == {}:
			print('Loading Preprocessor')
			print('Processing Threads Found:', Preprocessor.thread_count)
			Preprocessor.config = conf

	def FeatureScale(self, target_array, feature_range=[0, 1], custom_min_max=[0, 0], return_params=False):
		#sets values between -1 and 1
		target_array = list(target_array)
		if custom_min_max != [0, 0]:
			min_value = custom_min_max[0]
			max_value = custom_min_max[1]
		else:
			min_value = float(min(target_array))
			max_value = float(max(target_array))
		feature_width = abs(feature_range[0] - feature_range[1])

		#sets values between 0 and 1
		scaled_data = np.divide(np.subtract(target_array, min_value), (max_value - min_value))

		if feature_range != [0, 1]:
			#adjusts to non-standard feature range
			scaled_data = np.add(np.multiply(scaled_data, feature_width), feature_range[0])

		if return_params == True:
			min_max = [min_value, max_value]
			scaled_zero = self.FeatureScale([0], custom_min_max=min_max, feature_range=feature_range)
			scaled_zero = scaled_zero[0]
			params = {'min_max': min_max, 
					  'feature_range': feature_range,
					  'scaled_zero': scaled_zero}
			return scaled_data, params

		return scaled_data

	def UndoFeatureScale(self, target_array, feature_range=[0, 1], min_max=[-1,1]):
		#sets values between -1 and 1
		unscaled_data = list(target_array)
		min_value = float(min_max[0])
		max_value = float(min_max[1])
		feature_width = abs(feature_range[0] - feature_range[1])

		#the following is the inverse of self.FeatureScale, see that function for context

		if feature_range != [0, 1]:
			unscaled_data = np.divide(np.subtract(unscaled_data, feature_range[0]), feature_width)

		unscaled_data = np.add(np.multiply(unscaled_data, (max_value - min_value)), min_value)

		return unscaled_data

	def SetUnixToDate(self, unix):#input unix time as string or int
		#when using to display on screen, add to UTC unix param to offset for your timezone
		return datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S.%f0Z')
		#RETURNS UTC, confirmed

	def SetDateToUnix(self, date):
		unix = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f0Z')
		unix = unix.timestamp() - 36000#sets it to UTC
		return unix

	def PrintProgressBar(self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 49, 
																				fill = '/', printEnd = "\r"):
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


	def Process(self, proc_type='', raw_data={}, data_index={}, historical_index={}):
		'''
		proc_type: general type of data processing
			ex: 'training_data' (all types are found in self.proc_types)
		raw_data: complete pandas dataframe of data to be changed
		data_index: literal index of the data used for preprocess parameters/settings 
			(Note: in the case of training_data, it is a dictionary of each currencies initial_data
			format example: {'BTC', bitcoin_dataframe, 'ETH': ethereum_dataframe}	
		'''

		#proc_type parameter verification
		if proc_type not in Preprocessor.proc_types:
			print(f"Invalid proc_type: {proc_type} | Preprocessor.Process()")
			raise

		self.proc_type = proc_type
		self.initial_data = raw_data
		self.new_data = self.initial_data
		self.data_index = data_index
		self.historical_index = historical_index

		#used to calculate time delay between iterations of following loop
		init_time = time.time()


		if self.proc_type == 'training_data':
			self.InitTrainingData()


		#this sets up a batch of data for each processing thread so that all data is processed once
		#the last thread is reserved for monitoring progress and does not receive a batch of data
		proc_threads = Preprocessor.thread_count - 1
		proc_length = math.ceil(self.data_index['datapoints'] / proc_threads)
		proc_intervals = []
		last_index = self.initial_data.index[-1]
		start_index = 0
		for thread in range(proc_threads):
			end_index = start_index + proc_length
			custom_start = start_index - self.data_index['prediction_steps']

			if thread == 0:
				proc_intervals.append(self.initial_data.index[start_index:end_index])
			elif thread == proc_threads-1:
				end_index = self.initial_data.index[-1]
				#by default python array slicing ignores last point so add one index value worth
				proc_intervals.append(self.initial_data.index[custom_start:end_index])
			elif custom_start < 0:
				custom_start = 0
				proc_intervals.append(self.initial_data.index[custom_start:end_index])
			else:
				proc_intervals.append(self.initial_data.index[custom_start:end_index])

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


		self.initial_data = self.new_data.copy()

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

	def MultiprocTrainingSetup(self, proc_interval=[], proc_data={}, proc_status={}, proc_num=0):
		count = 0
		start = proc_interval[0]
		end = proc_interval[-1]
		initial_data = self.initial_data.loc[start:end, :]
		new_data = initial_data.copy()
		for index, row in initial_data.iterrows():
			for col in initial_data.columns:

				if 'is_nan' in col:
					if np.isnan(row[col]):
						new_data.at[index, col] = 1 #is_nan = true

				if 'average_price' in col:
					low = initial_data.at[index, col.replace('average_price', 'price_low')]
					high = initial_data.at[index, col.replace('average_price', 'price_high')]
					average = (low + high) / 2
					new_data.at[index, col] = average

			if count % 1000 == 0:
				proc_status[proc_num] = count
			count += 1

		proc_status[proc_num] = count
		proc_data[proc_num] = new_data

	def MultiprocTrainingFinal(self, proc_interval=[], prediction_steps=0, proc_data={}, proc_status={}, proc_num=0):
		if prediction_steps == 0:
			print("database.MultiprocFinal argument, prediction_steps, cannot be 0")
			raise

		start = proc_interval[0]
		end = proc_interval[-1]
		start = start - (prediction_steps * self.data_index['data_increment'])
		initial_data = self.initial_data.loc[start:end, :]
		new_data = initial_data.copy()
		count = 0
		for index, row in initial_data.iterrows():
			for col in initial_data.columns:

				if 'trend' in col:
					trend_index = index - (prediction_steps * self.data_index['data_increment'])
					if trend_index in proc_interval:
						#this gathers all relevant points between current index and trend_index
						average_col =  col.replace('trend', 'average_price')
						is_nan_col = col.replace('trend', 'is_nan')
						data = {'y_values': list(initial_data.loc[trend_index:index, average_col]),
								'is_nan': list(initial_data.loc[trend_index:index, is_nan_col])}
						trend_data = pd.DataFrame(data)
						#this drops all rows where is_nan == 1 
						trend_data = trend_data[trend_data.is_nan == 0]#drops all is_nan==1 rows

						n = len(trend_data.index)
						data_density = n / prediction_steps
						if data_density < .1:
							new_data.at[trend_index, col] = np.nan
							data_density = n / prediction_steps
							#print(f'{data_density}%')
							continue

						x_values = np.array(trend_data.index)
						y_values = np.array(trend_data['y_values'])
						#components
						x_mean = np.mean(x_values, dtype=np.float64)
						y_mean = np.mean(y_values, dtype=np.float64)
						x_sum = np.sum(x_values)
						y_sum = np.sum(y_values)
						xy_sum = np.sum((x_values*y_values))
						x_sqr_sum = np.sum((x_values**2))
						x_sum_sqr = np.sum(x_values) ** 2
						#slope
						m = (xy_sum - (x_sum*y_sum)/n)/(x_sqr_sum - x_sum_sqr/n)
						new_data.at[trend_index, col] = m

			if count % 1000 == 0:
				proc_status[proc_num] = count
			count += 1

		proc_status[proc_num] = count
		proc_data[proc_num] = new_data



	def InitTrainingData(self):
		'''
		This function preps self.raw_data in the format {'BTC': bitcoin_initial_data, ...}
		by consolidating it to the same self.initial_data pandas array with coin specific 
		columns being prefaced with f"{coin}|{col}" ex: "BTC_0|price_high" where the number after 
		BTC is the order of currencies left to right. EX: [BTC_0 columns, ETH_1 columns, DASH_2 columns]
		'''

		#creates currency key list IN ORDER OF CURRENCIES, NETWORK WILL FAIL WITHOUT ORDER
		#The second loop is needed to make sure each item is in order
		#The currency key list gives us accurate, in-order calling of initial_data
		currency_order = []
		for order_num in range(0, len(self.initial_data)):
			for key, dataset in self.initial_data.items():
				if str(order_num) in key:
					currency_order.append(key)
		
		#Generates list of columns in order of currency_order
		columns = ['time_period_start']
		# starting with time_period_start
		for coin in currency_order:
			for col in self.data_index['column_order']:
				columns.append(f"{coin}|{col}")

		#This finds the interval where data from all coins overlap
		#If there is existing_data, the start_data is self.data_index['data_end']
		#Else, the start time must be found.
		#  It must be the most recent initial_data data_start of all coins
		start_time = 0
		end_time = 0
		for coin in currency_order:
			coin_index = self.historical_index[self.data_index['currencies'][coin]]
			coin_start_time = self.SetDateToUnix(coin_index['data_start'])
			coin_end_time = self.SetDateToUnix(coin_index['data_end'])
			if coin_start_time > start_time:
				start_time = coin_start_time
			if coin_end_time < end_time or end_time == 0:
				end_time = coin_end_time

		#SORT OF IRRELAVENT COMMENT
		#self.new_data is declared with the same columns as initial_data
		# but has a NaN value for each cell at initialization. The index
		# count is also made to reflect the total number of timesteps
		# independent of any missing data starting at start_time
		total_datapoints = int(end_time - start_time) / self.data_index['data_increment']
		if total_datapoints - int(total_datapoints) != 0:
			print('data_increment calculation error, preprocessor.TrainingDataSetup()')
		else:
			#this gets rid of .0 at the end of number so further calculations with
			#it are not considered floating points
			total_datapoints = int(total_datapoints)


		#init_index is a list with length total_datapoints
		#Initializing the self.new_data with values increases compute time
		# by several orders of magnitude because all the memory addresses 
		# needed for the list have been registered before the loop rather
		# than during each iteration of it.
		init_index = []
		for x in range(total_datapoints):
			time_increment = int(x * self.data_index['data_increment'] + start_time)
			init_index.append(time_increment)
		self.new_data = pd.DataFrame(columns=columns, index=init_index)
		self.new_data.time_period_start = self.new_data.index


		#updates local index variable on new data
		self.data_index['datapoints'] = total_datapoints
		self.data_index['data_start'] = self.SetUnixToDate(start_time)
		self.data_index['data_end'] = self.SetUnixToDate(end_time)


		for coin in currency_order:

			#The following changes the index of initial_data to equal time_period_start
			#=============================================================================
			#=============================================================================
			#converts time_period_start column (soon to be index) to int
			self.initial_data[coin].time_period_start = self.initial_data[coin].time_period_start.astype(int)
			
			#sets the index to the time_period_start column and drops time_period_start
			self.initial_data[coin] = self.initial_data[coin].set_index('time_period_start', drop=False)

			#adds self.data_index['column_order'] to initial_data if not already included
			for col in self.data_index['column_order']:
				if col not in self.initial_data[coin].columns:
					self.initial_data[coin][col] = np.nan
			
			#this drops all unused columns in local initial_data variable
			# so that training_data does not have it
			drop_columns = []
			for col in self.initial_data[coin].columns:
				if col not in self.data_index['column_order']:
					drop_columns.append(col)
			self.initial_data[coin] = self.initial_data[coin].drop(columns=drop_columns)

			#renames columns in local initial_data variable to match training_data
			new_columns = {}
			for col in self.initial_data[coin].columns:
				new_columns.update({col: f"{coin}|{col}"})
			self.initial_data[coin] = self.initial_data[coin].rename(columns=new_columns)

			for col in self.initial_data[coin].columns:
				#BEFORE adding initial_data to self.new_data, this sets all initial_data is_nan to False (0)
				#Additionally, all self.new_data is_nan is set to True (1)
				#That way, when merged,self.new_data will start with False and only datapoints 
				#  with data will be set to True
				if 'is_nan' in col:
					self.new_data[col] = 1 #True, is_nan
					self.initial_data[coin][col] = 0 #False, not is_nan

				#adds values to self.new_data from initial_data
				self.new_data.loc[:, col] = self.initial_data[coin].loc[:, col]


		#self.new_data = self.new_data.head(300)
		#total_datapoints = 300
		self.initial_data = self.new_data.copy()