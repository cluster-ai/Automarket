
import pandas as pd
import numpy as np
from collections import deque

import tensorflow as tf
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
		self.SEQ_LEN = 250

		self.training_data = self.database.LoadTrainingData('KRAKEN_SPOT_BTC_USD.csv')
		print(self.training_data.columns)
		x = input('>>>')

		self.training_data = self.training_data.drop(columns=['time_period_end',
															  'time_period_start',
															  'price_close',
															  'price_open',
															  'trades_count',
															  'volume_traded'])

		print(self.training_data.head())

		#this sets up the data into batches
		training_batch = []
		prev_days = deque(maxlen=self.SEQ_LEN)
		count = 0
		for i in self.training_data.values:
			prev_days.append([n for n in i[:-1]])

			if len(prev_days) == self.SEQ_LEN:
				#print("Thing:", [np.array(prev_days), i[-1]])
				training_batch.append([np.array(prev_days), i[-1]])

			if count != 0 and count % 10000 == 0:
				print(count)

			count += 1


		random.shuffle(training_batch)

		xs = []
		ys = []

		for seq, target in training_batch:
			xs.append(seq)
			ys.append(target)

		xs = np.array(xs)
		ys = np.array(ys)


		self.model = tf.keras.Sequential([
			LSTM(100, input_shape=[self.SEQ_LEN, 2], return_sequences=True),
			Dropout(0.2),
			BatchNormalization(),
			LSTM(100, input_shape=[self.SEQ_LEN, 2], return_sequences=True),
			Dropout(0.2),
			BatchNormalization(),
			Dense(200, activation='tanh'),
			Dense(100, activation='tanh'),
			Dense(1, activation='tanh')
			])

		opt = tf.keras.optimizers.Adam(lr=0.002, decay=1e-5)
		self.model.compile(loss='mean_squared_error', optimizer=opt)

		history = self.model.fit(
					xs, ys,
					epochs=5,
					batch_size=100)