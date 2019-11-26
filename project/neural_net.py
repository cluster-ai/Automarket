
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


import time

import random

import copy

import math

##############################

## GPU MEMORY ALLOCATION CONFIG
from keras import backend as k
config = tf.compat.v1.ConfigProto()

config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction = 0.95#can only use up to 50% GPU-ram

tf.compat.v1.Session(config=config)

###############################

import database.coin_api as coin_api
import database.database as database

'''
To handle missing datapoints, use data from larger period_id to fill in the gaps of
more specific data sequences.
ex:
period_id = 1
1MIN = [n/a, n/a, 3, 3]
2MIN = [6,        6]
so...
1MIN = [3, 3, 3, 3]
'''

class NeuralNet():
	def __init__(self, database):
		self.database = database

		self.SEQ_LEN = 200
		self.training_data = self.database.QueryTrainingData(prediction_steps=100, 
														exchange_id='KRAKEN', 
														currencies=['BTC'])

		self.datapoints = len(self.training_data['x'].index)
		datapoints_test = len(self.training_data['y'].index)
		if self.datapoints != datapoints_test:
			raise

		self.train_datapoints = int(self.datapoints * 0.95)
		self.test_datapoints = self.datapoints - self.train_datapoints

		#local copy of training_data
		self.train_data_x = self.training_data['x'].head(self.train_datapoints)
		self.train_data_y = self.training_data['y'].head(self.train_datapoints)
		
		#omitts the most recent 5% of data for use as a true predictions sample
		self.test_data_x = self.training_data['x'].tail(self.test_datapoints)
		self.test_data_y = self.training_data['y'].tail(self.test_datapoints)

		self.GenerateSequences()

		self.TrainNetwork()


	def EstimateMapIndex(self, value, balance_map=[], map_resolution=0, min_value=0, max_value=0):
		#rel_value is value set to a range starting at zero
		value_range = abs(max_value - min_value)
		rel_value = value - min_value
		estimated_index = math.floor(rel_value / value_range * map_resolution)

		if estimated_index >= map_resolution:
			estimated_index = map_resolution - 1
		if estimated_index < 0:
			estimated_index = 0

		#since estimated_index can be off by one, the following statement is needed
		if value < balance_map.at[estimated_index, 'min']:
			estimated_index -= 1
		elif value >= balance_map.at[estimated_index, 'max'] and value != max_value:
			estimated_index += 1

		#this verifies the value is actually in the correct category
		if value < balance_map.at[estimated_index, 'min']:
			print(f"est_index: {estimated_index} | value: {value}")
			print(balance_map[estimated_index])
			raise
		elif value >= balance_map.at[estimated_index, 'max'] and value != max_value:
			raise

		return estimated_index


	def MapDensity(self, target_array=[], map_resolution=100):
		'''ONLY WORKS WITH ONE CURRENCY (and has to be BTC)'''
		max_val = max(target_array)
		min_val = min(target_array)

		increment = abs(max_val - min_val) / map_resolution

		balance_map = pd.DataFrame(columns=['max', 'min', 'quantity'], index=range(map_resolution))
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

			index = self.EstimateMapIndex(value, 
										balance_map=balance_map, 
										map_resolution=map_resolution, 
										min_value=min_val,
										max_value=max_val)

			balance_map.at[index, 'quantity'] += 1

		values = balance_map['quantity'].values
		values = values.reshape((len(balance_map['quantity']), 1))
		scaler = MinMaxScaler(feature_range=(0,10000))
		#print(col, '| Min: %f, Max: %f' % (scaler.data_min_, scaler.data_max_))
		normalized = np.squeeze(scaler.fit_transform(values))
		balance_map['quantity'] = normalized

		return balance_map


	def Func(self, x, a, b):
		return np.exp(np.multiply(np.power(np.add(x, 25), a), b))


	def GenerateSequences(self):

		balance_map = self.MapDensity(self.train_data_y['BTC_0|trend'], map_resolution=100)

		############################################################
		###Grapher

		x = []
		y = []

		count = 0
		for index, row in balance_map.iterrows():
			x_val = abs(row['max'] - row['min'])/2 + row['min']
			x.append(x_val)
			y.append(row['quantity'])

		self.midpoint =  x[y.index(max(y))]
		
		x = []
		y = []
		for index, row in balance_map.iterrows():
			x_val = abs(row['max'] - row['min'])/2 + row['min']
			if x_val <= self.midpoint and row['quantity'] >= 0:
				x.append(x_val)
				y.append(row['quantity'])

		params, params_covariance = curve_fit(self.Func, x, y)
		print(f'parameters: {params}')

		error = abs(np.subtract(y, self.Func(x, params[0], params[1]))) / y
		error = np.sum(error) / len(x) * 100

		print(f'Percent Error: {error}')

		plt.plot(x, y)

		data_x = np.linspace(x[0], x[-1], 100)
		data = self.Func(data_x, params[0], params[1])
		plt.plot(data_x, data)

		plt.show()

		var = input('>>>')


		############################################################
		###Sequence Generator

		#TRAIN_DATA
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


		for x in range(0, 3):
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

			opt = tf.keras.optimizers.Adam(lr=0.001, decay=1e-4)
			self.model.compile(loss='mean_squared_error', optimizer=opt)

			history = self.model.fit(
					self.xs, self.ys,
					epochs=4,
					batch_size=50,
					validation_data=(self.xs_test, self.ys_test))


			#print(testing_batch)
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

			open('0_epoch.csv', 'w')
			results.to_csv('0_epoch.csv')
			var = input('>>>')

		#average_error = total_error / len(error_list) * 100


		#print(f"\nAverage Error: {average_error}%")

		#accuracy or %error for trend predictions is calculated by dividing the difference of 
		#  prediction against the actual value divided by actual value, absolute value.
		#		   |prediction - actual|
		#  error = |-------------------|
		#		   |      actual       |
		