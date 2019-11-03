
import pandas as pd
import numpy as np
from collections import deque

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization

import random

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
		self.TrainNetwork()

	def TrainNetwork(self):
		self.SEQ_LEN = 200

		self.training_data = self.database.QueryTrainingData(prediction_steps=100, 
														exchange_id='KRAKEN', 
														currencies=['BTC'])
		
		datapoints = len(self.training_data['x'].index)
		datapoints_test = len(self.training_data['y'].index)
		if datapoints != datapoints_test:
			raise

		train_datapoints = int(datapoints * 0.95)
		test_datapoints = datapoints - train_datapoints

		#local copy of training_data
		train_data_x = self.training_data['x'].head(train_datapoints)
		train_data_y = self.training_data['y'].head(train_datapoints)
		
		#omitts the most recent 5% of data for use as a true predictions sample
		test_data_x = self.training_data['x'].tail(test_datapoints)
		test_data_y = self.training_data['y'].tail(test_datapoints)

		#TRAIN_DATA
		training_batch = []
		prev_days = deque(maxlen=self.SEQ_LEN)
		for index, row in train_data_x.iterrows():
			prev_days.append([n for n in row])

			if len(prev_days) == self.SEQ_LEN:
				isnan_y = np.isnan(train_data_y.loc[index, :])
				if np.isin(True, isnan_y) == False:
					training_batch.append([np.array(prev_days), train_data_y.loc[index, :]])

			if index % 50000 == 0 and index != 0:
				print(index)

		random.shuffle(training_batch)

		xs = []
		ys = []

		for seq, target in training_batch:
			xs.append(seq)
			ys.append(target)

		xs = np.array(xs)
		ys = np.array(ys)


		#TEST_DATA
		testing_batch = []
		prev_days = deque(maxlen=self.SEQ_LEN)
		for index, row in test_data_x.iterrows():
			prev_days.append([n for n in row])

			if len(prev_days) == self.SEQ_LEN:
				isnan_y = np.isnan(test_data_y.loc[index, :])
				if np.isin(True, isnan_y) == False:
					testing_batch.append([np.array(prev_days), test_data_y.loc[index, :]])

			if index % 50000 == 0 and index != 0:
				print(index)

		random.shuffle(testing_batch)

		xs_test = []
		ys_test = []

		for seq, target in testing_batch:
			xs_test.append(seq)
			ys_test.append(target)

		xs_test = np.array(xs_test)
		ys_test = np.array(ys_test)


		#MODEL

		for x in range(0, 3):
			self.model = Sequential([
				LSTM(500,input_shape=[self.SEQ_LEN, len(train_data_x.columns)], return_sequences=True),
				Dropout(0.2),
				BatchNormalization(),
				LSTM(500),
				Dropout(0.2),
				BatchNormalization(),
				Dense(len(train_data_x.columns), activation='tanh'),
				Dropout(0.2),
				Dense(400, activation='tanh'),
				Dropout(0.2),
				Dense(400, activation='tanh'),
				Dropout(0.2),
				Dense(len(train_data_y.columns), activation='tanh')
				])

			opt = tf.keras.optimizers.Adam(lr=0.00003, decay=1e-5)
			self.model.compile(loss='mean_squared_error', optimizer=opt)

			history = self.model.fit(
						xs, ys,
						epochs=5,
						batch_size=200,
						validation_data=(xs_test, ys_test))

			predictions = self.model.predict(xs_test)
			error_list = []
			count = 0
			for index, prediction in enumerate(predictions):
				#error
				error = abs((ys_test[index]-prediction)/ ys_test[index])
				error_list.append(error)
				#print(f"Prediction: {x[0]} | Actual: {ys_test[index]}")
				#print(f"Difference: {difference}")

				count += 1

			total_error = np.sum(np.array(error_list)) / count * 100
			
			print(f"average_error: {total_error}")
		#average_error = total_error / len(error_list) * 100

		#print(f"\nAverage Error: {average_error}%")

		#accuracy or %error for trend predictions is calculated by dividing the difference of 
		#  prediction against the actual value divided by actual value, absolute value.
		#		   |prediction - actual|
		#  error = |-------------------|
		#		   |      actual       |
