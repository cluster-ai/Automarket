
import pandas as pd
import numpy as np
from collections import deque

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization

import matplotlib.pyplot as plt

from scipy.stats import norm
from scipy.optimize import curve_fit

from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler

import os

import time

import random

import copy

import math

##############################

## GPU MEMORY ALLOCATION CONFIG
from keras import backend as k
config = tf.compat.v1.ConfigProto()

config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction = 0.95 #percentage of max gpu memory allocation

tf.compat.v1.Session(config=config)

###############################

import database.coin_api as coin_api
import database.database as database

class NeuralNet():
	def __init__(self, database):
		self.database = database

		self.SEQ_LEN = 200
		self.training_data = self.database.QueryTrainingData(prediction_steps=100, 
														exchange_id='KRAKEN', 
														currencies=['BTC'])

		self.datapoints = len(self.training_data['x'].index)
		if self.datapoints != len(self.training_data['y'].index):
			raise

		self.train_datapoints = int(self.datapoints * 0.95)
		self.test_datapoints = self.datapoints - self.train_datapoints

		#instance copy of train data (oldest 95% of self.training_data)
		self.train_data_x = self.training_data['x'].head(self.train_datapoints)
		self.train_data_y = self.training_data['y'].head(self.train_datapoints)
		
		#instance copy of test data (newest 95% of self.training_data)
		self.test_data_x = self.training_data['x'].tail(self.test_datapoints)
		self.test_data_y = self.training_data['y'].tail(self.test_datapoints)

		self.GenerateSequences()

		self.TrainNetwork()


	def EstimateMapIndex(self, value, balance_map=pd.DataFrame(), min_value=0, max_value=0):
		map_resolution = len(balance_map.index)
		#rel_value is the value parameter translated along the "x-axis" so that min_value == 0
		#EX: value_range == [-1, 1]   so...   rel_value_range == [0, 2]
		#EX: value == 0               so...   rel_value == value - min_value == 1
		value_range = abs(max_value - min_value)
		rel_value = value - min_value

		estimated_index = math.floor(rel_value / value_range * map_resolution)

		#prevents index overflow
		if estimated_index >= map_resolution:
			estimated_index = map_resolution - 1
		if estimated_index < 0:
			estimated_index = 0

		#since estimated_index can be off by one,
		#  this shifts the value to appropriate category if needed
		if value < balance_map.at[estimated_index, 'min']:
			estimated_index -= 1
		elif value >= balance_map.at[estimated_index, 'max'] and estimated_index != map_resolution-1:
			estimated_index += 1

		#this verifies the value is actually in the correct category
		if value < balance_map.at[estimated_index, 'min']:
			print(f"est_index: {estimated_index} | value: {value}")
			print(balance_map[estimated_index])
			raise
		elif value >= balance_map.at[estimated_index, 'max'] and estimated_index != map_resolution-1:
			raise

		return estimated_index


	def CreateDensityMap(self, target_array=[], map_resolution=1000):
		#only works on a single dimension of data

		max_val = 1   #max(target_array)
		min_val = -1  #min(target_array)

		increment = abs(max_val - min_val) / map_resolution

		balance_map = pd.DataFrame(columns=['max', 'min', 'area', 'quantity'], 
																index=range(map_resolution))
		for col in balance_map.columns:
			balance_map[col].values[:] = 0

		prev_max = min_val
		for index, row in balance_map.iterrows():
			new_min = prev_max
			if index+1 == map_resolution:
				new_max = max_val
			else:
				new_max = prev_max + increment

			#values are >= min but < max. only the last index can be equal to max
			balance_map.at[index, 'max'] = new_max
			balance_map.at[index, 'min'] = new_min

			prev_max = new_max

		isnan = 0
		#index quantity of data for each category
		for value in target_array:

			if np.isnan(value) == True:
				isnan += 1
				continue

			index = self.EstimateMapIndex(value, balance_map=balance_map, 
														min_value=min_val, 
														max_value=max_val)

			balance_map.at[index, 'quantity'] += 1

		self.total_area = 0
		prev_y = 0
		for index, row in balance_map.iterrows():
			x_diff = abs(row['max'] - row['min'])
			#this gets the area under curve from 0 to x_val of each point.
			low_y = min([prev_y, row['quantity']])
			high_y = max([prev_y, row['quantity']])
			y_diff = abs(low_y - high_y)
			balance_map.at[index, 'area'] = self.total_area
			self.total_area += y_diff*x_diff/2 + low_y*x_diff

			prev_y = row['quantity']

		values = balance_map['quantity'].values
		values = values.reshape((len(balance_map['quantity']), 1))
		scaler = MinMaxScaler(feature_range=(0,10))
		#print(col, '| Min: %f, Max: %f' % (scaler.data_min_, scaler.data_max_))
		normalized = np.squeeze(scaler.fit_transform(values))
		balance_map['quantity'] = normalized

		return balance_map


	def BalanceData(self, data, density_map):
		init_time = time.time()

		self.overall_min = -1
		self.overall_max = 1
		self.balance_range = abs(self.overall_min - self.overall_max)

		new_data = []
		map_indexes = []
		for index, trend_x in enumerate(data):
			if np.isnan(trend_x):
				new_data.append(np.nan)
				map_indexes.append(np.nan)
				continue

			map_index = self.EstimateMapIndex(trend_x, balance_map=density_map,
															min_value=self.overall_min,
															max_value=self.overall_max)

			approx_area = density_map.at[map_index, 'area']

			#x and y are the current points values. x2 and y2 are the next datapoints values
			x = density_map.at[map_index, 'min']
			x2 = density_map.at[map_index, 'max']

			y = density_map.at[map_index, 'quantity']
			y2 = 0
			if map_index != len(density_map.index) - 1:
				y2 = density_map.at[map_index+1, 'quantity']
	
			m = (y - y2) / (x - x2)
			b = y
			if m != 0:
				b = y - m*x

			#excess_area is the area between the actual point and the max of its category
			trend_y = (m*trend_x + b)
			area_offset = abs(trend_x-x)*min([trend_y, y]) + abs(trend_x-x)*abs(trend_y-y)/2

			area = approx_area + area_offset

			new_trend = (area / self.total_area) * self.balance_range + self.overall_min

			new_data.append(new_trend)
			map_indexes.append(map_index)

			if index % 50000 == 0 and index != 0:
				print(index)

		duration = time.time() - init_time
		print(f"Balance Duration: {duration}")

		return new_data, map_indexes


	def UnbalanceData(self, data, density_map, map_indexes):
		init_time = time.time()

		new_data = []
		for index, trend_x in enumerate(data):
			if np.isnan(trend_x):
				new_data.append(np.nan) 
				continue

			area = (abs(trend_x - self.overall_min) / self.balance_range) * self.total_area

			#finds map index
			map_index = map_indexes[index]

			x = density_map.at[map_index, 'min']
			x2 = density_map.at[map_index, 'max']

			y = density_map.at[map_index, 'quantity']
			y2 = 0
			if map_index != len(density_map.index):
				y2 = density_map.at[map_index, 'quantity']

			approx_area = density_map.at[map_index, 'area']

			rel_total_area = abs(x-x2)*min([y,y2]) + abs(x-x2)*abs(y-y2)/2
			rel_area = abs(area - approx_area)
			
			new_trend = x
			if rel_total_area != 0 and map_index != len(density_map.index) - 1:
				new_trend = (rel_area / rel_total_area) * abs(x-x2) + x

			new_data.append(new_trend)

			if index % 50000 == 0 and index != 0:
				print(index)

		duration = time.time() - init_time
		print(f"Unbalance Duration: {duration}")

		return new_data


	def GenerateSequences(self):
		
		self.density_map = self.CreateDensityMap(list(self.train_data_y['BTC_0|trend'].values), 
																				map_resolution=45000)

		############################################################
		###Grapher


		remapped_data, remapped_indexes = self.BalanceData(list(self.train_data_y['BTC_0|trend']), 
																					self.density_map)

		remapped_data = self.UnbalanceData(remapped_data, self.density_map, remapped_indexes)

		unbalanced_map = self.CreateDensityMap(remapped_data, map_resolution=45000)

		'''x = list(unbalanced_map['min'].values)
		y = list(unbalanced_map['quantity'].values)
		plt.plot(x, y)

		x = list(self.density_map['min'].values)
		y = list(self.density_map['quantity'].values)
		plt.plot(x, y)'''

		error_list = []
		error_map_approx = []
		error_map_actual = []
		for index, value in enumerate(remapped_data):
			if np.isnan(value):
				continue
			init_train_index = self.train_data_y.index[0]
			train_value = self.train_data_y.at[index+init_train_index, 'BTC_0|trend']
			error = abs((value - train_value) / train_value)

			if error > 0:
				error_map_approx.append(value)
				error_map_actual.append(train_value)

			error_list.append(error)

		error = np.sum(error_list) / len(error_list) * 100

		print(f"Balance Error: {error}")

		max_error = max(error_list) * 100
		min_error = min(error_list) * 100
		print(f"Max Error: {max_error}")
		print(f"Min Error: {min_error}")

		'''approx_map = self.CreateDensityMap(error_map_approx)
		x = list(approx_map['min'].values)
		y = list(approx_map['quantity'].values)
		plt.plot(x, y)

		actual_map = self.CreateDensityMap(error_map_actual)
		x = list(actual_map['min'].values)
		y = list(actual_map['quantity'].values)
		plt.plot(x, y)'''

		#plt.show()

		var = input('>>>')
		
		'''x = list(density_map['min'].values)
		y = list(density_map['quantity'].values)
		plt.plot(x, y)

		
		self.train_data_y.loc[:, 'BTC_0|trend'] = self.BalanceData(list(self.train_data_y['BTC_0|trend']), 
																							self.density_map)

		self.test_data_y.loc[:,'BTC_0|trend'] = self.BalanceData(list(self.test_data_y['BTC_0|trend']), 
																							self.density_map)
		

		density_map = self.CreateDensityMap(self.train_data_y['BTC_0|trend'])

		x = list(density_map['min'].values)
		y = list(density_map['quantity'].values) 
		
		plt.plot(x, y)

		plt.show()

		var = input('>>>')'''

		############################################################
		###Sequence Generator

		'''
		Balancing is essentially flattening the distribution of target values
		(in this case trend values) so that any given float is equally likely to occur in the dataset
		(or at least as even as possible).

		My current method of doing this is categorizing the data based on value ranges into a balance_map
		and fitting a differentiable curve to it. I then get the anti-derivative of that function
		and apply a math equation that warps the values of datapoints so that the distribution is 
		more even. Keep in mind this warping maintains the integrity of data and is reversable to 
		within 1x10^-17 in testing (essentially perfect without floating point roundoff error).

		The importance of this is to prevent the neural model from optimizing to the same
		guess no matter what input is given. Currently, a non-balanced dataset
		causes the model to converge as mentioned previously: I think target data balancing 
		will help mitigate this effect. (has not been tested at the time of writing this)
		'''

		#TRAIN_DATA (MAY HAVE BALANCING)
		self.training_batch = []
		count = 0
		prev_days = deque(maxlen=self.SEQ_LEN)
		trend_nan_count = 0
		for index, row in self.train_data_x.iterrows():
			prev_days.append([n for n in row])

			if len(prev_days) == self.SEQ_LEN:
				y_values = self.train_data_y.loc[index, :]
				isnan_y = np.isnan(y_values)

				if np.isin(True, isnan_y) == False:
					self.training_batch.append([np.array(prev_days), self.train_data_y.loc[index, :]])
				else:
					trend_nan_count += 1

			if count % 50000 == 0 and count != 0:
				print(count)
			count += 1
		print(trend_nan_count)

		random.shuffle(self.training_batch)

		init_time = time.time()

		self.xs = []
		self.ys = []

		for seq, target in self.training_batch:
			self.xs.append(seq)
			self.ys.append(target)

		self.xs = np.array(self.xs)
		self.ys = np.array(self.ys)


		#TEST_DATA (NO BALANCING)
		self.testing_batch = []
		count = 0
		prev_days = deque(maxlen=self.SEQ_LEN)
		for index, row in self.test_data_x.iterrows():
			prev_days.append([n for n in row])

			if len(prev_days) == self.SEQ_LEN:
				isnan_y = np.isnan(self.test_data_y.loc[index, :])
				if np.isin(True, isnan_y) == False:
					self.testing_batch.append([np.array(prev_days), self.test_data_y.loc[index, :]])

			if count % 50000 == 0 and count != 0:
				print(count)
			count += 1

		self.xs_test = []
		self.ys_test = []

		for seq, target in self.testing_batch:
			self.xs_test.append(seq)
			self.ys_test.append(target)

		self.xs_test = np.array(self.xs_test)
		self.ys_test = np.array(self.ys_test)



	def TrainNetwork(self):


		for x in range(0, 1):
			self.model = Sequential([
				LSTM(300,input_shape=[self.SEQ_LEN, len(self.train_data_x.columns)], return_sequences=True),
				Dropout(0.2),
				BatchNormalization(),
				LSTM(300),
				Dropout(0.2),
				BatchNormalization(),
				Dense(len(self.train_data_x.columns), activation='tanh'),
				Dropout(0.2),
				Dense(200, activation='tanh'),
				Dropout(0.2),
				Dense(200, activation='tanh'),
				Dropout(0.2),
				Dense(len(self.train_data_y.columns), activation='tanh')
				])

			opt = tf.keras.optimizers.Adam(lr=0.0001, decay=1e-5)
			self.model.compile(loss='mean_squared_error', optimizer=opt)

			if os.path.isdir('results') == False:
				os.mkdir('results')

			epochs = 5
			for epoch in range(epochs):
				print('----------------------------------------------------')
				print(f"Epoch {epoch}")
				print('----------------------------------------------------')

				if epoch != 0:
					history = self.model.fit(
							self.xs, self.ys,
							epochs=1,
							batch_size=100,
							validation_data=(self.xs_test, self.ys_test))


				#Model testing beyond this point
				init_index = []
				for x in range(0, len(self.xs_test)):
					init_index.append(x)
				results = pd.DataFrame(columns=['inverse', 'actual', 'prediction'], index=init_index)

				predictions = self.model.predict(self.xs_test)
				error_list = []
				error_list_inv = []
				count = 0
				for index, prediction in enumerate(predictions):
					actual_ys = self.ys_test[index]
					inv_index = -index-1
					inv_ys = self.ys_test[inv_index]

					results.at[index, 'actual'] = actual_ys
					results.at[index, 'inverse'] = inv_ys
					results.at[index, 'prediction'] = prediction

					error = abs((actual_ys-prediction)/ actual_ys)
					error_list.append(error)
					
					inv_error = abs((inv_ys-prediction)/inv_ys)
					error_list_inv.append(inv_error)

					count += 1

				total_error = np.sum(np.array(error_list)) / len(np.array(error_list)) * 100
				total_inv_error = np.sum(np.array(error_list_inv))/len(np.array(error_list_inv)) * 100

				print('################')
				print(f"average_error: {total_error}")
				print(f"inverse error: {total_inv_error}")
				print('################')

				print(results)

				#prediction distribution
				balance_map = self.CreateDensityMap(target_array=np.asarray(np.squeeze(predictions)), 
																					map_resolution=500)
				open(f'results/pred_epoch{epoch}.csv', 'w')
				balance_map.to_csv(f'results/pred_epoch{epoch}.csv', index=False)


			#actual distribution
			balance_map = self.CreateDensityMap(target_array=np.asarray(np.squeeze(self.ys_test)), 
																				map_resolution=500)
			open(f'results/actual.csv', 'w')
			balance_map.to_csv(f'results/actual.csv', index=False)