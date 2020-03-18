
import pandas as pd
import numpy as np
from collections import deque

import tensorflow as tf
from tensorflow.keras.optimizers import RMSprop
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

		self.outputs = 2
		self.output_map = pd.DataFrame(columns=['min', 'max', 'quantity'])

		self.y_data_columns = []
		for x in range(self.outputs):
			self.y_data_columns.append(x)

		self.SEQ_LEN = 100
		self.training_data, self.filename = self.database.QueryTrainingData(prediction_steps=20, 
																exchange_id='KRAKEN', 
																currencies=['BTC'])

		self.target_min = min(np.ndarray.tolist(np.squeeze(self.training_data['y'].values)))
		self.target_max = max(np.ndarray.tolist(np.squeeze(self.training_data['y'].values)))
		self.balance_range = abs(self.target_min - self.target_max)


		self.datapoints = len(self.training_data['x'].index)
		if self.datapoints != len(self.training_data['y'].index):
			raise

		self.train_datapoints = int(self.datapoints * 0.95)
		self.test_datapoints = self.datapoints - self.train_datapoints

		#instance copy of train data (oldest 95% of self.training_data)
		'''
		self.train_data_x = self.training_data['x'].head(self.train_datapoints)
		train_index = range(self.train_data_x.index[0], self.train_data_x.index[0]+self.train_datapoints)
		self.train_data_y = pd.DataFrame(columns=self.y_data_columns, index=train_index)
		self.train_target = self.training_data['y'].head(self.train_datapoints)
		'''
		self.train_data_x = self.training_data['x'].head(self.datapoints)
		#self.train_data_x.drop(columns=['time_period_start'], inplace=True)
		train_index = range(self.train_data_x.index[0], self.train_data_x.index[0]+self.datapoints)
		self.train_data_y = pd.DataFrame(columns=self.y_data_columns, index=train_index)
		self.train_target = self.training_data['y'].head(self.datapoints)
		
		#instance copy of test data (newest 95% of self.training_data)
		self.test_data_x = self.training_data['x'].tail(self.test_datapoints)
		#self.test_data_x.drop(columns=['time_period_start'], inplace=True)
		test_index = range(self.test_data_x.index[0], self.test_data_x.index[0]+self.test_datapoints)
		self.test_data_y = pd.DataFrame(columns=self.y_data_columns, index=test_index)
		self.test_target = self.training_data['y'].tail(self.test_datapoints)

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
		if value < balance_map.at[estimated_index, 'min'] and estimated_index != 0:
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

		#quantity feature scale
		values = balance_map['quantity'].values
		scaled_data = self.preprocessor.FeatureScale(values, feature_range=[0, 100])
		balance_map['quantity'] = scaled_data

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
					if index == 0:
						balance_map.at[index, 'quantity'] = 0
						last_valid_index = index
					else:
						balance_map.at[index, 'quantity'] = np.nan
						latest_zero_points.append(index)
				elif row['quantity'] > 0 and np.isnan(last_valid_index) == True:
					last_valid_index = index
					continue
				elif row['quantity'] > 0 and np.isnan(last_valid_index) == False:
					#wrap up the last valid index (max value needs to be set)
					balance_map.at[last_valid_index, 'max'] = balance_map.at[index, 'min']

					for zero_index in latest_zero_points:
						index_map[zero_index] = last_valid_index
					latest_zero_points = []

					last_valid_index = index
					continue

		balance_map.dropna(inplace=True)
		balance_map.reset_index(inplace=True)

		#this converts index map values within new index range
		for key, item in index_map.items():
			new_index = balance_map.index[balance_map['index'] == item][0]
			index_map[key] = new_index

		self.total_area = 0
		prev_y = 0
		prev_x = self.target_min
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
															min_value=self.target_min,
															max_value=self.target_max,
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

			new_trend = (area / total_area) * self.balance_range + self.target_min

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

			area = (abs(trend_x - self.target_min) / self.balance_range) * total_area

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
			if x_plus >= self.target_min and x_plus <= self.target_max:
				plus_error = self.BalanceData([x_plus], density_map, map_resolution=map_resolution, 
																					index_map=index_map)[0]
				if trend_x == 0:
					plus_error = abs(plus_error)
				else:
					plus_error = abs((plus_error - trend_x) / trend_x)

			minus_error = 1000
			if x_minus >= self.target_min and x_minus <= self.target_max:
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

			if index % 1000 == 0 and index != 0:
				print(index)

		duration = time.time() - init_time
		print(f"Unbalance Duration: {duration}")

		return new_data


	def GenerateSequences(self):

		self.map_res = 5000
		print(self.map_res)
		#if the datapoint count is two years worth (210240), self.map_res == 2000
		self.density_map, self.index_map = self.CreateDensityMap(list(self.train_target['BTC_0|trend'].values), 
																				map_resolution=self.map_res,
																				non_zero_values=True,
																				return_index_map=True)


		#Inititalizes output map with equal spacing
		increment = self.balance_range / self.outputs
		prev_max = self.target_min
		for index in range(self.outputs):
			new_max = prev_max + increment
			if index+1 == self.outputs:
				self.output_map.at[index, 'min'] = prev_max
				self.output_map.at[index, 'max'] = self.target_max
			else:
				self.output_map.at[index, 'min'] = prev_max
				self.output_map.at[index, 'max'] = new_max
			prev_max = new_max

		self.output_map.fillna(0, inplace=True)

		#uses the unbalance function so that each category has an equal number of datapoints (roughly)
		output_min = np.ndarray.tolist(np.squeeze(self.output_map.loc[:, 'min'].values))
		output_max = np.ndarray.tolist(np.squeeze(self.output_map.loc[:, 'max'].values))
		self.output_map.loc[:, 'min'] = self.UnbalanceData(output_min, self.density_map, 
											map_resolution=self.map_res, index_map=self.index_map)
		self.output_map.loc[:, 'max'] = self.UnbalanceData(output_max, self.density_map, 
											map_resolution=self.map_res, index_map=self.index_map)


		#iterates through the data and creates a matching train_data_y values
		#	based on datas category
		self.train_data_y.fillna(0, inplace=True)
		init_target_index = self.train_target.index[0]
		for target_index, row in self.train_target.iterrows():
			map_index = np.nan
			value = row['BTC_0|trend']
			if np.isnan(value):
				self.train_data_y.loc[target_index, :] = np.nan
				continue
			for output_index, category in self.output_map.iterrows():
				if value < category['max'] and output_index == 0:
					map_index = output_index
				elif value < category['max'] and value >= category['min']:
					map_index = output_index
				elif value >= category['max'] and output_index == self.outputs-1:
					map_index = output_index

			self.train_data_y.at[target_index, map_index] = 1
			if (target_index-init_target_index) % 20000 == 0:
				print(target_index - init_target_index)

		#finds how many datapoints fall under each category
		total_qty = self.datapoints
		for col in self.train_data_y.columns:
			qty = np.sum((self.train_data_y[col].dropna()).values)
			self.output_map.at[col, 'quantity'] = qty
			percent = qty / total_qty * 100
			print(f"Quantity: {qty} | Percent: {percent}%")

		print(self.output_map)



		#SAME THING BUT FOR TEST DATA

		#iterates through the data and creates a matching train_data_y values
		#	based on datas category
		self.test_data_y.fillna(0, inplace=True)
		init_target_index = self.test_target.index[0]
		for target_index, row in self.test_target.iterrows():
			map_index = np.nan
			value = row['BTC_0|trend']
			if np.isnan(value):
				self.test_data_y.loc[target_index, :] = np.nan
				continue
			for output_index, category in self.output_map.iterrows():
				if value < category['max'] and output_index == 0:
					map_index = output_index
				elif value < category['max'] and value >= category['min']:
					map_index = output_index
				elif value >= category['max'] and output_index == self.outputs-1:
					map_index = output_index

			self.test_data_y.at[target_index, map_index] = 1
			if (target_index) % 20000 == 0:
				print(target_index - init_target_index)

		print(self.output_map)


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

		#TRAIN_DATA
		self.training_batch = []
		count = 0
		prev_days = deque(maxlen=self.SEQ_LEN)
		trend_nan_count = 0
		for index, row in self.train_data_x.iterrows():
			prev_days.append([n for n in row])

			if len(prev_days) == self.SEQ_LEN:
				y_values = self.train_data_y.loc[index, :].values
				isnan_y = np.isnan(y_values)
				isnan_x = np.isnan(prev_days)

				if np.isin(True, isnan_y) == False and np.isin(True, isnan_x) == False:
					self.training_batch.append([np.array(prev_days), self.train_data_y.loc[index, :].values])
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


		#TEST_DATA
		self.testing_batch = []
		count = 0
		prev_days = deque(maxlen=self.SEQ_LEN)
		for index, row in self.test_data_x.iterrows():
			prev_days.append([n for n in row])

			if len(prev_days) == self.SEQ_LEN:
				isnan_y = np.isnan(self.test_data_y.loc[index, :].values)
				if np.isin(True, isnan_y) == False:
					self.testing_batch.append([np.array(prev_days), self.test_data_y.loc[index, :].values])

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

		print(self.xs_test)
		print('=======================================')
		print(self.xs)
		var = input('>>>')



	def TrainNetwork(self):

		for x in range(0, 1):
			self.model = Sequential([
				LSTM(500,input_shape=[self.SEQ_LEN, len(self.train_data_x.columns)], return_sequences=True),
				Dropout(0.2),
				BatchNormalization(),
				LSTM(500, return_sequences=True),
				Dropout(0.2),
				BatchNormalization(),
				Dense(400, activation='sigmoid'),
				Dropout(0.2),
				Dense(400, activation='sigmoid'),
				Dropout(0.2),
				Dense(self.outputs, activation='softmax')
				])

			opt = tf.keras.optimizers.Adam(lr=0.005, decay=1e-5)
			self.model.compile(loss='mse', optimizer=opt, metrics=['accuracy'])

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

				'''if epoch == 0:
					continue'''

				predictions = self.model.predict(self.xs_test)
				error_list = []
				error_list_inv = []
				value_pred = []
				count = 0
				for index, prediction_raw in enumerate(predictions):
					actual_ys = np.ndarray.tolist(self.ys_test[index])
					inv_index = -index-1
					inv_ys = np.ndarray.tolist(self.ys_test[inv_index])

					actual_max = max(actual_ys)
					actual_ys = [ i for i,v in enumerate(actual_ys) if v==actual_max ][0]

					inv_max = max(inv_ys)
					inv_ys = [ i for i,v in enumerate(inv_ys) if v==inv_max ][0]

					prediction = np.ndarray.tolist(prediction_raw)
					prediction_max = max(prediction)
					prediction = [ i for i,v in enumerate(prediction) if v==prediction_max ][0]

					value_pred.append(prediction)

					results.at[index, 'actual'] = actual_ys
					results.at[index, 'inverse'] = inv_ys
					results.at[index, 'prediction'] = prediction

					if prediction == actual_ys:
						error_list.append(0)
					elif prediction != actual_ys:
						error_list.append(100)

					if prediction == inv_ys:
						error_list_inv.append(0)
					elif prediction != inv_ys:
						error_list_inv.append(100)

					count += 1

				print("Predictions for 0:", value_pred.count(0))
				print("Predictions for 1:", value_pred.count(1))

				total_error = np.sum(np.array(error_list)) / len(np.array(error_list))
				total_inv_error = np.sum(np.array(error_list_inv))/len(np.array(error_list_inv))

				print('################')
				print(f"average_error: {total_error}")
				print(f"inverse error: {total_inv_error}")
				print('################')

				'''for index, row in results.iterrows():
					print(row.values)'''

				#prediction distribution
				'''balance_map = self.CreateDensityMap(target_array=bal_predictions, map_resolution=500)
				open(f'results/pred_epoch{epoch}.csv', 'w')
				balance_map.to_csv(f'results/pred_epoch{epoch}.csv', index=False)

			#actual distribution
			bal_ys_test = np.asarray(np.squeeze(self.ys_test))
			bal_ys_test = self.BalanceData(bal_ys_test, self.density_map, map_resolution=self.map_res, 
																					index_map=self.index_map)
			balance_map = self.CreateDensityMap(target_array=bal_ys_test, map_resolution=500)
			open(f'results/actual.csv', 'w')
			balance_map.to_csv(f'results/actual.csv', index=False)'''


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
			init_train_index = self.test_target.index[0]
			train_value = self.test_target.at[index+init_train_index, 'BTC_0|trend']

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