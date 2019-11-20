
import pandas as pd
import numpy as np
from collections import deque

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization

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

		self.data_cap = self.GenerateSequences(cap_multiplier=.5)

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
		if value < balance_map[estimated_index]['min']:
			estimated_index -= 1
		elif value >= balance_map[estimated_index]['max'] and value != max_value:
			estimated_index += 1

		#this verifies the value is actually in the correct category
		if value < balance_map[estimated_index]['min']:
			print(f"est_index: {estimated_index} | value: {value}")
			print(balance_map[estimated_index])
			raise
		elif value >= balance_map[estimated_index]['max'] and value != max_value:
			raise

		return estimated_index


	def GenerateSequences(self, map_resolution=1000, cap_multiplier=1):
		#The data trend values are not evenly distributed across all its relative values
		#EX:
		#	Even distribution: [-1,3,0,2,-2,-3,1] (equal numbers of each between -3 and 3)
		#	un-even distribution: [-1,2,-1,-1,3,2] (unequal/missing numbers between -3 and 3)
		#Since the model is more likely to favor or even exclusively choose one specific number 
		#for all predictions if the data is unevenly distributed. We must omitt values of certain 
		#categories to balance the data.
		#The following evenly cuts the normalization feature_range (-1 to 1) into balance_res pieces

		'''ONLY WORKS WITH ONE CURRENCY (and has to be BTC)'''
		max_trend = self.training_data['y']['BTC_0|trend'].max()
		min_trend = self.training_data['y']['BTC_0|trend'].min()

		increment = abs(max_trend - min_trend) / map_resolution
		#balance map is a dictionary of the trend distribution
		#the keys are its value range and the value is number of self.datapoints in that category
		#EX: 
		#[
		#	{
		#		"min": -1, 
		#		"max": -0.9,
		#		"quantity": 45
		#	},
		#	...
		#]
		balance_map = []
		#balance map initializer
		prev_value = min_trend
		for x in range(map_resolution):
			new_min = prev_value
			if x+1 == map_resolution:
				print('FLAG')
				new_max = max_trend
			else:
				new_max = prev_value + increment

			#values are >= min but < max. only the last index can be equal to max
			new_value = {"min": new_min, "max": new_max, "quantity": 0}
			balance_map.append(new_value)

			prev_value = new_max

		tracking_map = copy.deepcopy(balance_map)
		self.init_map = copy.deepcopy(tracking_map)

		isnan = 0
		#index quantity of data for each category
		for value in self.train_data_y['BTC_0|trend']:

			if np.isnan(value) == True:
				isnan += 1
				continue

			map_index = self.EstimateMapIndex(value, 
												balance_map=balance_map, 
												map_resolution=map_resolution, 
												min_value=min_trend,
												max_value=max_trend)

			balance_map[map_index]['quantity'] += 1

		qty_sum = 0
		for item in balance_map:
			qty_sum += item['quantity']

		average = qty_sum/len(balance_map)
		data_cap = int(average * cap_multiplier)

		qty_total = 0
		for item in balance_map:
			qty = item['quantity']
			if qty > data_cap:
				qty = data_cap
			qty_total += qty
			print(item)

			percent_left = qty_total/(self.train_datapoints-isnan)

		print('data_cap:', data_cap, "||", "percent_left:", percent_left*100)


		############################################################
		###Sequence Generator

		#TRAIN_DATA
		self.training_batch = []
		count = 0
		prev_days = deque(maxlen=self.SEQ_LEN)
		trend_nan_count = 0
		print(len(self.train_data_x) * percent_left)
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
			map_index = self.EstimateMapIndex(target[0],
												balance_map=balance_map,
												map_resolution=map_resolution,
												min_value=min_trend,
												max_value=max_trend)

			if tracking_map[map_index]['quantity'] < data_cap:
				self.xs.append(seq)
				self.ys.append(target)
				tracking_map[map_index]['quantity'] += 1

		self.xs = np.array(self.xs)
		self.ys = np.array(self.ys)

		print("Balance Duration:", time.time() - init_time)


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

		return data_cap



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

			opt = tf.keras.optimizers.Adam(lr=0.0001, decay=1e-4)
			self.model.compile(loss='mean_squared_error', optimizer=opt)
			
			epochs = 3
			for x in range(epochs):
				print('EPOCH:', x+1, "/", epochs)

				###TEMPORARY
				max_trend = self.training_data['y']['BTC_0|trend'].max()
				min_trend = self.training_data['y']['BTC_0|trend'].min()

				random.shuffle(self.training_batch)

				init_time = time.time()

				self.xs = []
				self.ys = []


				tracking_map = copy.deepcopy(self.init_map)
				for seq, target in self.training_batch:
					map_index = self.EstimateMapIndex(target[0],
														balance_map=tracking_map,
														map_resolution=1000,
														min_value=min_trend,
														max_value=max_trend)

					if tracking_map[map_index]['quantity'] < self.data_cap:
						self.xs.append(seq)
						self.ys.append(target)
						tracking_map[map_index]['quantity'] += 1

				self.xs = np.array(self.xs)
				self.ys = np.array(self.ys)

				###

				history = self.model.fit(
						self.xs, self.ys,
						epochs=1,
						batch_size=5,
						validation_data=(self.xs_test, self.ys_test))

				print('four')

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
		