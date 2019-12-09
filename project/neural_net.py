
import pandas as pd
import numpy as np
from collections import deque

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization

import matplotlib.pyplot as plt

from scipy.stats import norm
from scipy.optimize import curve_fit

import database.preprocessor as preprocessor

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
		self.preprocessor = preprocessor.Preprocessor()

		self.overall_min = 0
		self.overall_max = 1
		self.balance_range = abs(self.overall_min - self.overall_max)

		self.SEQ_LEN = 200
		self.training_data, self.filename = self.database.QueryTrainingData(prediction_steps=100, 
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


	def EstimateMapIndex(self, value, balance_map=pd.DataFrame(), min_value=0, 
															max_value=0, index_map={}, map_resolution=0):
		#rel_value is the value parameter translated along the "x-axis" so that min_value == 0
		#EX: value_range == [-1, 1]   so...   rel_value_range == [0, 2]
		#EX: value == 0               so...   rel_value == value - min_value == 1
		value_range = abs(max_value - min_value)
		rel_value = value - min_value

		estimated_index = math.floor(rel_value / value_range * map_resolution)
		og_index = estimated_index

		#prevents index overflow
		if estimated_index >= map_resolution-1:
			estimated_index = map_resolution-1
		if estimated_index < 0:
			estimated_index = 0

		if index_map != {}:
			estimated_index = index_map[estimated_index]

		#since estimated_index can be off by one,
		#  this shifts the value to appropriate category if needed
		if value < balance_map.at[estimated_index, 'min']:
			estimated_index -= 1
		elif value >= balance_map.at[estimated_index, 'max'] and estimated_index != len(balance_map.index)-1:
			estimated_index += 1

		#this verifies the value is actually in the correct category
		if value < balance_map.at[estimated_index, 'min'] and estimated_index > 0:
			print(f"est_index: {estimated_index} | value: {value}")
			print(balance_map.loc[estimated_index, :])
			raise
		elif value >= balance_map.at[estimated_index, 'max'] and estimated_index != len(balance_map.index)-1:
			max_index = len(balance_map.index) - 1
			print(f"estimated_index: {estimated_index}, max_index: {max_index}, map_res: {map_resolution}")
			raise

		return estimated_index


	def CreateDensityMap(self, target_array=[], map_resolution=1000, non_zero_values=False, return_index_map=False):
		#only works on a single dimension of data

		abs_max = 1   #max(target_array)
		abs_min = 0  #min(target_array)

		increment = abs(abs_max - abs_min) / map_resolution

		balance_map = pd.DataFrame(columns=['max', 'min', 'area', 'quantity'], 
																index=range(map_resolution))
		for col in balance_map.columns:
			balance_map[col].values[:] = 0

		prev_max = abs_min
		for index, row in balance_map.iterrows():
			new_min = prev_max
			if index+1 == map_resolution:
				new_max = abs_max
			else:
				new_max = prev_max + increment

			#values are >= min but < max. only the last index can be equal to max
			balance_map.at[index, 'max'] = new_max
			balance_map.at[index, 'min'] = new_min

			prev_max = new_max

		isnan = 0
		#index quantity of data for each category
		for index, value in enumerate(target_array):

			if np.isnan(value) == True:
				isnan += 1
				continue

			index = self.EstimateMapIndex(value, balance_map=balance_map, 
														min_value=abs_min, 
														max_value=abs_max,
														map_resolution=map_resolution)

			balance_map.at[index, 'quantity'] += 1

		min_quantity = balance_map['quantity'].min()
		max_quantity = balance_map['quantity'].max()
		print(f'min_quantity: {min_quantity}, max_quantity: {max_quantity}')
		print('percentage graphed:', (abs(min_quantity - max_quantity) / max_quantity * 100))

		#This prevents values being zero so that any value in the domain can be represented.
		#index map is used to keep track of what each index now maps to since its being changed
		'''
		index map format:
		{estimated_index:actual_index(+/- 1), ...}
		example:
		{1:1, 2:1, 3:3, 4:4, 5:4}
		'''
		index_map = {}
		if non_zero_values == True:
			last_valid_index = np.nan
			latest_zero_points = []
			for index, row in balance_map.iterrows():
				index_map.update({index: index})#may be changed if current index quantity is zero

				if row['quantity'] <= 0:
					balance_map.at[index, 'quantity'] = np.nan
					latest_zero_points.append(index)
					continue
				elif np.isnan(last_valid_index) == False:
					#wrap up the last valid index (max value needs to be set)
					balance_map.at[last_valid_index, 'max'] = balance_map.at[index, 'min']

					for zero_index in latest_zero_points:
						index_map[zero_index] = last_valid_index
					latest_zero_points = []

					last_valid_index = index
					continue
				elif np.isnan(last_valid_index) == True:
					last_valid_index = index
					continue

		balance_map.dropna(inplace=True)
		balance_map.reset_index(inplace=True)

		#this converts index map values within new index range
		for key, item in index_map.items():
			new_index = balance_map.index[balance_map['index'] == item][0]
			index_map[key] = new_index

		values = balance_map['quantity'].values
		scaled_data = self.preprocessor.FeatureScale(values, feature_range=[0, 100])
		balance_map['quantity'] = scaled_data

		self.total_area = 0
		prev_y = 0
		prev_x = self.overall_min
		for index, row in balance_map.iterrows():
			x_diff = abs(prev_x - row['min'])
			#this gets the area under curve from 0 to min of each point.
			low_y = min([prev_y, row['quantity']])
			high_y = max([prev_y, row['quantity']])
			y_diff = abs(low_y - high_y)
			self.total_area += (y_diff*x_diff/2 + low_y*x_diff)

			balance_map.at[index, 'area'] = self.total_area

			prev_y = row['quantity']
			prev_x = row['min']
		x_diff = abs(balance_map['min'].iloc[-1]-balance_map['max'].iloc[-1])
		y_diff = abs(balance_map['quantity'].iloc[-1] - 0)
		self.total_area = self.total_area + y_diff*x_diff/2

		if return_index_map == True:
			return balance_map, index_map

		return balance_map


	def BalanceData(self, data, density_map, map_resolution=0, index_map={}, return_indexes=False):
		init_time = time.time()

		x_diff = abs(density_map['min'].iloc[-1] - density_map['max'].iloc[-1])
		y_diff = abs(density_map['quantity'].iloc[-1] - 0)
		total_area = density_map['area'].iloc[-1] + y_diff*x_diff/2

		new_data = []
		map_indexes = []
		for index, trend_x in enumerate(data):
			if np.isnan(trend_x):
				new_data.append(np.nan)
				map_indexes.append(np.nan)
				continue

			map_index = self.EstimateMapIndex(trend_x, balance_map=density_map,
															min_value=self.overall_min,
															max_value=self.overall_max,
															index_map=index_map,
															map_resolution=map_resolution)

			approx_area = density_map.at[map_index, 'area']

			#x and y are the current points values. x2 and y2 are the next datapoints values
			x = density_map.at[map_index, 'min']
			x2 = density_map.at[map_index, 'max']

			y = density_map.at[map_index, 'quantity']
			y2 = 0
			if map_index != len(density_map.index) - 1:
				y2 = density_map.at[map_index+1, 'quantity']
	
			m = (y - y2) / (x - x2)
			b = y - m*x

			#excess_area is the area between the actual point and the max of its category
			#here I use the antiderivative of a linear equation to get area between
			#	trend_x and min of current map_index (anti-deriv = m/2*(x^2)+bx)
			trend_y = m*trend_x + b
			area_offset = abs(trend_x-x)*min([y, trend_y]) + abs(trend_x - x)*abs(y - trend_y)/2
			rel_total_area = abs(x-x2)*min([y, y2]) + abs(x - x2)*abs(y - y2)/2

			area = approx_area + area_offset

			new_trend = (area / total_area) * self.balance_range + self.overall_min

			new_data.append(new_trend)
			map_indexes.append(map_index)

			if index % 50000 == 0 and index != 0:
				print(index)

		duration = time.time() - init_time
		#print(f"Balance Duration: {duration}")

		if return_indexes == True:
			return new_data, map_indexes

		return new_data


	def UnbalanceData(self, data, density_map, index_map={}, map_resolution=0, map_indexes=[]):
		init_time = time.time()

		x_diff = abs(density_map['min'].iloc[-1] - density_map['max'].iloc[-1])
		y_diff = abs(density_map['quantity'].iloc[-1] - 0)
		total_area = density_map['area'].iloc[-1] + y_diff*x_diff/2

		new_data = []
		for index, trend_x in enumerate(data):
			if np.isnan(trend_x):
				new_data.append(np.nan) 
				continue

			area = (abs(trend_x - self.overall_min) / self.balance_range) * total_area

			#finds map index
			map_index = int((len(density_map.index)-1) / 2)
			if map_indexes != []:
				map_index = map_indexes[index]

			while True:
				if map_index != len(density_map.index)-1:
					if area >= density_map.at[map_index+1, 'area']:
						map_index += 1
					elif area < density_map.at[map_index, 'area'] and map_index != 0:
						map_index -= 1
					else:
						break
				elif map_index == len(density_map.index)-1:
					if area < density_map.at[map_index, 'area']:
						map_index -= 1
					else:
						break
				else:
					break

			x = density_map.at[map_index, 'min']
			x2 = density_map.at[map_index, 'max']

			y = density_map.at[map_index, 'quantity']
			y2 = 0
			if map_index != len(density_map.index) - 1:
				y2 = density_map.at[map_index+1, 'quantity']

			approx_area = density_map.at[map_index, 'area']

			rel_area = area - approx_area
			

			m = (y - y2) / (x - x2)
			b = y - m*x

			ref_area = (m/2 * x**2 + b*x) + rel_area

			a = m/2
			b = b
			c = -ref_area

			x_plus = x
			x_minus = x
			if m != 0:
				sqrt_val = b**2 - 4*a*c
				if sqrt_val < 0 and abs(sqrt_val) < 0.0000001:
					sqrt_val = 0
				elif sqrt_val < 0 and abs(sqrt_val) > 0.0000001:
					pass
				x_plus = (-b + math.sqrt(sqrt_val)) / (2*a)
				x_minus = (-b - math.sqrt(sqrt_val)) / (2*a)


			plus_error = 1000
			if x_plus >= self.overall_min and x_plus <= self.overall_max:
				plus_error = self.BalanceData([x_plus], density_map, map_resolution=map_resolution, 
																					index_map=index_map)[0]
				if trend_x == 0:
					plus_error = abs(plus_error)
				else:
					plus_error = abs((plus_error - trend_x) / trend_x)

			minus_error = 1000
			if x_minus >= self.overall_min and x_minus <= self.overall_max:
				minus_error = self.BalanceData([x_minus], density_map, map_resolution=map_resolution, 
																					index_map=index_map)[0]
				if trend_x == 0:
					minus_error = abs(minus_error)
				else:
					minus_error = abs((minus_error - trend_x) / trend_x)

			new_trend = x
			if minus_error < plus_error:
				new_trend = x_minus
			else:
				new_trend = x_plus

			if m == 0 and b != 0:
				new_trend = ref_area / b

			new_data.append(new_trend)

			if index % 10000 == 0 and index != 0:
				print(index)

		duration = time.time() - init_time
		print(f"Unbalance Duration: {duration}")

		return new_data


	def GenerateSequences(self):

		self.map_res = 1000 #45000 currently seems to generate the lowest error
		self.density_map, self.index_map = self.CreateDensityMap(list(self.train_data_y['BTC_0|trend'].values), 
																				map_resolution=self.map_res,
																				non_zero_values=True,
																				return_index_map=True)


		'''self.TestBalanceError()

		var = input('>>>')'''

		####################################################
		####Data Balancer

		#data, density_map, map_resolution=0, index_map={}, return_indexes=False

		og_data = self.train_data_y.loc[:, 'BTC_0|trend'].values

		self.train_data_y.loc[:, 'BTC_0|trend'], indexes = self.BalanceData(
														np.ndarray.tolist(self.train_data_y['BTC_0|trend'].values),
																self.density_map,
																map_resolution=self.map_res,
																index_map=self.index_map,
																return_indexes=True)


		self.train_data_y.loc[:, 'BTC_0|trend'] = self.UnbalanceData(
														np.ndarray.tolist(self.train_data_y['BTC_0|trend'].values),
																self.density_map,
																map_resolution=self.map_res,
																index_map=self.index_map,
																map_indexes=indexes)

		
		new_data = self.train_data_y.loc[:, 'BTC_0|trend'].values

		error = abs(np.divide(np.subtract(new_data, og_data), og_data))
		error = np.sum(error) / len(new_data) * 100
		print(f'error: {error}')

		#train_map = self.CreateDensityMap(list(self.train_data_y['BTC_0|trend'].values), map_resolution=1000)

		'''x = list(train_map['min'].values)
		y = list(train_map['quantity'].values)

		plt.plot(x, y)
		plt.show()'''

		var = input('>>>')

		############################################################
		###Sequence Generator

		'''
		Balancing is essentially flattening the distribution of target values
		(in this case trend values) so that any given float is equally likely to occur in the dataset
		(or at least as even as possible).

		The importance of this is to prevent the neural model from optimizing to the same
		guess no matter what input is given. Currently, a non-balanced dataset
		causes the model to converge as mentioned previously.
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

			epochs = 3
			for epoch in range(epochs):
				print('----------------------------------------------------')
				print(f"Epoch {epoch}")
				print('----------------------------------------------------')

				if epoch != 0:
					history = self.model.fit(
							self.xs, self.ys,
							epochs=1,
							batch_size=200,
							validation_data=(self.xs_test, self.ys_test))


				#Model testing beyond this point
				init_index = []
				for x in range(0, len(self.xs_test)):
					init_index.append(x)
				results = pd.DataFrame(columns=['inverse', 'actual', 'prediction'], index=init_index)

				predictions = np.asarray(np.squeeze(self.model.predict(self.xs_test)))
				#the model predicts in the "balanced format"
				predictions = self.UnbalanceData(predictions, self.density_map, map_index=self.map_index, 
																						map_resolution=self.map_res)
				#self.ys_test = self.BalanceData(np.asarray(np.squeeze(self.ys_test)), self.density_map, )
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

					error = abs((actual_ys-prediction)/ self.balance_range)
					error_list.append(error)
					
					inv_error = abs((inv_ys-prediction)/ self.balance_range)
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
				balance_map = self.CreateDensityMap(target_array=predictions, map_resolution=500)
				open(f'results/pred_epoch{epoch}.csv', 'w')
				balance_map.to_csv(f'results/pred_epoch{epoch}.csv', index=False)


			#actual distribution
			balance_map = self.CreateDensityMap(target_array=np.asarray(np.squeeze(self.ys_test)), 
																				map_resolution=500)
			open(f'results/actual.csv', 'w')
			balance_map.to_csv(f'results/actual.csv', index=False)


	def TestBalanceError(self):
		map_data = list(self.train_data_y['BTC_0|trend'].values)
		test_data = list(self.test_data_y['BTC_0|trend'].values)
		map_res = 100
		density_m, self.index_m = self.CreateDensityMap(map_data, map_resolution=map_res, 
															non_zero_values=True, return_index_map=True)

		#####################################################################

		remapped_data, remapped_indexes = self.BalanceData(test_data, 
									density_m, map_resolution=map_res, index_map=self.index_m, return_indexes=True)

		remapped_data = self.UnbalanceData(remapped_data, density_m, index_map=index_map, map_resolution=map_res)

		unbalanced_map = self.CreateDensityMap(remapped_data, map_resolution=1000)

		x = list(unbalanced_map['min'].values)
		y = list(unbalanced_map['quantity'].values)
		plt.plot(x, y)

		'''x = list(density_m['min'].values)
		y = list(density_m['quantity'].values)
		plt.plot(x, y)'''

		error_list = []
		error_map_approx = []
		error_map_actual = []
		scaled_zero = self.database.training_index[self.filename]['target_columns']['BTC_0|trend']['scaled_zero']
		for index, value in enumerate(remapped_data):
			if np.isnan(value):
				continue
			init_train_index = self.test_data_y.index[0]
			train_value = self.test_data_y.at[index+init_train_index, 'BTC_0|trend']

			#offset data so that scaled_zero is not zero
			#value = value - scaled_zero
			#train_value = train_value - scaled_zero
			error = abs((value - train_value) / self.balance_range * 100)

			#the added overall min gets the minimum value to zero so the error is not
			#	being calculated for points across zero. This prevents the error from 
			#	drastically inflating on points around zero.

			if error >= 0:
				#print(f"og_val: {train_value}, new_val: {value}")
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

		plt.show()

		var = input('>>>')