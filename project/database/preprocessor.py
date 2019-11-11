
import time
import datetime
from multiprocessing import Process, Manager, Value

from sklearn import preprocessing

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
		if Preprocessor.config != {}:
			print('Loading Preprocessor')
			print('Processing Threads Found:', Preprocessor.thread_count)
			Preprocessor.config = conf


	def SetUnixToDate(self, unix):#input unix time as string or int
		#when using to display on screen, add to UTC unix param to offset for your timezone
		return datetime.datetime.utcfromtimestamp(unix).strftime('%Y-%m-%dT%H:%M:%S.%f0Z')
		#RETURNS UTC, confirmed

	def SetDateToUnix(self, date):
		unix = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f0Z')
		unix = unix.timestamp() - 36000#sets it to UTC
		return unix


	def Process(self, proc_type='', raw_data={}, data_index={}, historical_index={}):
		'''
		proc_type: general type of data processing
			ex: 'training_data' (all types are found in self.proc_types)
		raw_data: complete pandas dataframe of data to be changed
		data_index: literal index of the data used for preprocess parameters/settings 
			(Note: in the case of training_data, it is a dictionary of each currencies historical_data
			format example: {'BTC', bitcoin_dataframe, 'ETH': ethereum_dataframe}	
		'''

		#proc_type parameter verification
		if proc_type not in Preprocessor.proc_types:
			print(f"Invalid proc_type: {proc_type} | Preprocessor.Process()")
			raise

		self.proc_type = proc_type
		self.historical_data = raw_data
		self.new_data = raw_data
		self.data_index = data_index
		self.historical_index = historical_index

		#used to calculate time delay between iterations of following loop
		init_time = time.time()


		if self.proc_type == 'training_data':
			self.TrainingDataSetup()

			#this sets up a batch of data for each processing thread so that all data is processed once
			proc_length = math.ceil(self.data_index['datapoints'] / Preprocessor.thread_count)
			proc_interval = []
			proc_intervals = []
			last_index = self.historical_data.index[-1]
			for index in self.historical_data.index:
				proc_interval.append(index)
				if len(proc_interval) == proc_length or index == last_index:
					proc_intervals.append(proc_interval)
					proc_interval = []

			manager = Manager()
			new_proc_data = manager.dict()
			lock = Lock()

			#uses proc_data_all in loop to set up each process for multithreading, order does not matter
			#MULTIPROC SETUP
			print("preping data..")
			procs = []
			for proc_num, proc_interval in enumerate(proc_intervals):
				print(proc_num)
				proc = Process(target=self.MultiprocTrainingSetup, args=(proc_interval, 
																new_proc_data, 
																lock,
																proc_num,))
				procs.append(proc)
				proc.start()
			#ends multithreaded processes
			for proc in procs:
				proc.join()
			for proc_num, dataframe in new_proc_data.items():
				self.new_data.loc[proc_intervals[proc_num], :] = dataframe.loc[proc_intervals[proc_num], :]


			self.historical_data = self.new_data.copy()

			#wipes new_proc_data
			new_proc_data = manager.dict()

			print("preprocessing...")
			#MULTIPROC FINAL
			procs = []
			for proc_num, proc_interval in enumerate(proc_intervals):
				proc = Process(target=self.MultiprocTrainingFinal, args=(proc_interval, 
																self.data_index['prediction_steps'],
																new_proc_data,
																lock,
																proc_num,))
				procs.append(proc)
				proc.start()
			#ends multithreaded processes
			for proc in procs:
				proc.join()
			for proc_num, dataframe in new_proc_data.items():
				self.new_data.loc[proc_intervals[proc_num], :] = dataframe.loc[proc_intervals[proc_num], :]


			total_time = time.time() - init_time
			print(f"Total Duration: {total_time}")

			#==============================================================
			#Data Processor End
			#==============================================================

			print(self.new_data.head(150))

			#normalization
			'''
			for col in self.new_data.columns:
				if 'is_nan' not in col and 'trend' not in col:
					print(self.new_data[col].values)
					self.new_data[col] = preprocessing.scale(self.new_data[col].values)
			'''

		return self.new_data



	def MultiprocTrainingSetup(self, proc_interval=[], proc_data=[], lock=0, proc_num=0):
		count = 0
		start = proc_interval[0]
		end = proc_interval[-1]
		historical_data = self.historical_data.loc[start:end, :]
		new_data = historical_data.copy()
		for index, row in historical_data.iterrows():
			for col in historical_data.columns:

				if 'is_nan' in col:
					if np.isnan(row[col]):
						new_data.at[index, col] = 1 #is_nan = true

				if 'average_price' in col:
					low = historical_data.at[index, col.replace('average_price', 'price_low')]
					high = historical_data.at[index, col.replace('average_price', 'price_high')]
					average = (low + high) / 2
					new_data.at[index, col] = average
			count += 1
		proc_data[proc_num] = new_data

	def MultiprocTrainingFinal(self, proc_interval=[], prediction_steps=0, proc_data=[], lock=0, proc_num=0):
		if prediction_steps == 0:
			print("database.MultiprocFinal argument, prediction_steps, cannot be 0")
			raise

		start = proc_interval[0]
		end = proc_interval[-1]
		start = start - (prediction_steps * self.data_index['data_increment'])
		historical_data = self.historical_data.loc[start:end, :]
		new_data = historical_data.copy()
		for index, row in historical_data.iterrows():
			for col in historical_data.columns:

				if 'trend' in col:
					trend_index = index - (prediction_steps * self.data_index['data_increment'])
					if trend_index in proc_interval:
						#this gathers all relevant points between current index and trend_index
						average_col =  col.replace('trend', 'average_price')
						is_nan_col = col.replace('trend', 'is_nan')
						data = {'y_values': list(historical_data.loc[trend_index:index, average_col]),
								'is_nan': list(historical_data.loc[trend_index:index, is_nan_col])}
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
		proc_data[proc_num] = new_data



	def TrainingDataSetup(self):
		'''
		This function preps self.raw_data in the format {'BTC': bitcoin_historical_data, ...}
		by consolidating it to the same self.historical_data pandas array with coin specific 
		columns being prefaced with f"{coin}|{col}" ex: "BTC_0|price_high" where the number after 
		BTC is the order of currencies left to right. EX: [BTC_0 columns, ETH_1 columns, DASH_2 columns]
		'''

		#creates currency key list IN ORDER OF CURRENCIES, NETWORK WILL FAIL WITHOUT ORDER
		#The second loop is needed to make sure each item is in order
		#The currency key list gives us accurate, in-order calling of historical_data
		currency_order = []
		for order_num in range(0, len(self.historical_data)):
			for key, dataset in self.historical_data.items():
				if str(order_num) in key:
					currency_order.append(key)
		
		#Generates list of columns in order of currency_order
		columns = ['time_period_start']
		# starting with time_period_start
		for coin in currency_order:
			for col in self.data_index['currency_columns']:
				columns.append(f"{coin}|{col}")

		#loads existing data if any
		existing_data = pd.DataFrame()
		try:
			existing_data = pd.read_csv(self.data_index['filepath'])

			#verifies that existing_data is not missing_columns
			'''
			missing_columns = []
			for col in columns:
				if col not in existing_data.columns:
					missing_columns.append(col)
			if len(missing_columns) > 0:
				print('Existing data on', self.data_index['filename'], 'is missing columns:')
				print(missing_columns)
				raise
			#there cannot be extra columns from here on
			extra_columns = len(existing_data.columns) - len(columns)
			if extra_columns > 0:
				print(extra_columns, 'Extra Columns Found')
				raise
			'''
		except:
			existing_data = pd.DataFrame(columns=columns)

		#returns data if the data is up to date
		matches = 0
		for coin in currency_order:
			coin_index = self.historical_index[self.data_index['currencies'][coin]]
			if self.data_index['data_end'] == coin_index['data_end']:
				matches += 1
		if matches == len(currency_order):
			print('training_data up to date')
			print(existing_data.head(10))
			return existing_data

		#This finds the interval where data from all coins overlap
		#If there is existing_data, the start_data is self.data_index['data_end']
		#Else, the start time must be found.
		#  It must be the most recent historical_data data_start of all coins
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
		#self.new_data is declared with the same columns as historical_data
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

			#The following changes the index of historical_data to equal time_period_start
			#=============================================================================
			#=============================================================================
			#converts time_period_start column (soon to be index) to int
			self.historical_data[coin].time_period_start = self.historical_data[coin].time_period_start.astype(int)
			
			#sets the index to the time_period_start column and drops time_period_start
			self.historical_data[coin] = self.historical_data[coin].set_index('time_period_start', drop=False)

			#adds self.data_index['currency_columns'] to historical_data if not already included
			for col in self.data_index['currency_columns']:
				if col not in self.historical_data[coin].columns:
					self.historical_data[coin][col] = np.nan
			
			#this drops all unused columns in local historical_data variable
			# so that training_data does not have it
			drop_columns = []
			for col in self.historical_data[coin].columns:
				if col not in self.data_index['currency_columns']:
					drop_columns.append(col)
			self.historical_data[coin] = self.historical_data[coin].drop(columns=drop_columns)

			#renames columns in local historical_data variable to match training_data
			new_columns = {}
			for col in self.historical_data[coin].columns:
				new_columns.update({col: f"{coin}|{col}"})
			self.historical_data[coin] = self.historical_data[coin].rename(columns=new_columns)

			for col in self.historical_data[coin].columns:
				#BEFORE adding historical_data to self.new_data, this sets all historical_data is_nan to False (0)
				#Additionally, all self.new_data is_nan is set to True (1)
				#That way, when merged,self.new_data will start with False and only datapoints 
				#  with data will be set to True
				if 'is_nan' in col:
					self.new_data[col] = 1 #True, is_nan
					self.historical_data[coin][col] = 0 #False, not is_nan

				#adds values to self.new_data from historical_data
				self.new_data.loc[:, col] = self.historical_data[coin].loc[:, col]


		#self.new_data = self.new_data.head(300)
		#total_datapoints = 300
		self.historical_data = self.new_data.copy()