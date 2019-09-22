
import pandas as pd
import numpy as np
from collections import deque

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, CuDNNLSTM, LSTM, BatchNormalization

import random

##############################

## GPU MEMORY ALLOCATION CONFIG
from keras import backend as k
config = tf.ConfigProto()

config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction = 0.5#can only use up to 50% GPU-ram

k.tensorflow_backend.set_session(tf.Session(config=config))

###############################

import database.coin_api as coin_api
import database.database as database

'''
Don't normalize the market data for LSTM, make the data a relative percentage.
Percentage change when compared to data x time-steps ago (start with x = 1) so that
value at x is value at x / x-1
ex: 
[1,2,1,3,1,4] Becomes... [n/a,2,0.5,3,0.333,4]

To handle missing datapoints, use data from larger period_id to fill in the gaps of
more specific data sequences.
ex:
period_id = 1
1MIN = [n/a, n/a, 3, 3]
2MIN = [6,        6]
so...
1MIN = [3, 3, 3, 3]
'''

class Main():
	def __init__(self):
		self.database = database.Database()
		self.SEQ_LEN = 20
		'''
		self.training_data = self.database.LoadTrainingData('KRAKEN_SPOT_BTC_USD.csv')
		self.training_data = self.training_data.drop(columns=['time_close',
															  'time_open',
															  'time_period_end',
															  'time_period_start',
															  'trades_count',
															  'volume_traded'])
		
		index_range = []
		for x in range(2000, 312799):
			index_range.append(x)

		self.training_data = self.training_data.drop(index_range)
		'''
		'''

		self.training_data = pd.DataFrame(columns=['factor1', 'factor2', 'product'])

		for x in range(0, 12000):
			factor1 = random.uniform(-1, 1)
			factor2 = random.uniform(-1, 1)

			product = factor1 * factor2

			if x > 0:
				product = product * (self.training_data.at[x-1, 'product'] + .5)

			if abs(product) > 1:
				print(f"overflow: {product}")

			self.training_data.at[x, 'factor1'] = factor1
			self.training_data.at[x, 'factor2'] = factor2
			self.training_data.at[x, 'product'] = product

		#this sets up the data into batches
		training_batch = []
		prev_days = deque(maxlen=self.SEQ_LEN)
		for i in self.training_data.values:
			prev_days.append([n for n in i[:-1]])

			if len(prev_days) == self.SEQ_LEN:
				#print("Thing:", [np.array(prev_days), i[-1]])
				training_batch.append([np.array(prev_days), i[-1]])

		random.shuffle(training_batch)

		xs = []
		ys = []

		for seq, target in training_batch:
			xs.append(seq)
			ys.append(target)

		xs = np.array(xs)


		self.model = Sequential([
			CuDNNLSTM(units=200, input_shape=[self.SEQ_LEN, 2], return_sequences=True),
			Dropout(0.2),
			BatchNormalization(),
			CuDNNLSTM(units=200, input_shape=[self.SEQ_LEN, 2]),
			Dropout(0.2),
			BatchNormalization(),
			Dense(units=100, activation='tanh'),
			Dense(units=1, activation='tanh')
			])

		self.TrainNetwork()

	def TrainNetwork(self):
		test_batch = []
		prev_days = deque(maxlen=self.SEQ_LEN)
		for i in self.training_data.values:
			prev_days.append([n for n in i[:-1]])

			if len(prev_days) == self.SEQ_LEN:
				#print("Thing:", [np.array(prev_days), i[-1]])
				test_batch.append([np.array(prev_days), i[-1]])

		random.shuffle(test_batch)

		xs_test = []
		ys_test = []

		for seq, target in test_batch:
			xs_test.append(seq)
			ys_test.append(target)

		xs_test = np.array(xs_test)

		opt = tf.keras.optimizers.SGD(lr=0.01, decay=0.1, momentum=0.1, nesterov=False)
		self.model.compile(loss='mean_squared_error', optimizer=opt)

		history = self.model.fit(
					xs_test, ys_test,
					epochs=5,
					batch_size=50)
		'''


main = Main()