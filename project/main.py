from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM, CuDNNLSTM, BatchNormalization
from tensorflow.keras.callbacks import TensorBoard, ModelCheckpoint

import database.database as data

'''
This program might need to have a fibonacci type of framework in which
the program references its previous data to predict the next x datapoints
USE AN RNN (Recurrent Neural Network) 
'''

class Model:
	def __init__(self, data):
		self.data = data.Datbase()
		self.n_cols = self.data.train_x.shape[1]
		self.graph = Sequential([
			CuDNNLSTM(128, input_shape=(train_x.shape[1:]), return_sequences=True)
			Dropout(0.2)
			BatchNormalization()

			CuDNNLSTM(128, input_shape=(train_x.shape[1:]), return_sequences=True)
			Dropout(0.2)
			BatchNormalization()

			CuDNNLSTM(128, input_shape=(train_x.shape[1:]))
			Dropout(0.2)
			BatchNormalization()

			Dense(32, activation='relu')
			Dropout(0.2)

			Dense(2, activation='softmax')])












#EXAMPLE =====================================================================================
#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
#EXAMPLE =====================================================================================


import pandas as pd
import numpy as np
from sklearn import preprocessing
from collections import deque
import matplotlib.pyplot as plt

import tensorflow as tf

import os
import random
import time

#this import is for converting string numbers with commas to float
import locale
from locale import atof
##############################

## GPU MEMORY ALLOCATION CONFIG
'''from keras import backend as k
config = tf.ConfigProto()

config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction = 0.5#can only use up to 50% GPU-ram

k.tensorflow_backend.set_session(tf.Session(config=config))'''
###############################


##changes text-based date format to unix
import datetime
def SetDateToUnix(date):#input date string
		utc = datetime.datetime.strptime(date, '%b %d, %Y')
		return int(utc.timestamp())



SEQ_LEN = 60
FUTURE_PERIOD_PREDICT = 3
EPOCHS = 50
BATCH_SIZE = 64
NAME = f"{SEQ_LEN}-SEQ-{FUTURE_PERIOD_PREDICT}-PRED-{int(time.time())}"

#all used currency dataframe
main_df = pd.DataFrame()

#these are all in reference to USD
used_coins = ["etherium"]
#the current version DOES NOT support multiple coins.
# it can only preprocess, train, and predict one coin at a time.



def classify(current, future):
	if float(future) > float(current):
		return 1
	else:
		return 0

def preprocess_df(df):
	for col in df.columns:
		if col.find('target') == -1:
			df[col] = pd.to_numeric(df[col])
			df[col] = df[col].pct_change()# %change relative to the first value in each sequence
			df.dropna(inplace=True)
			df[col] = preprocessing.scale(df[col].values)#normalize

	df.dropna(inplace=True)

	coin_target = 0
	for coin in used_coins:
		#determine the split ratio between each coins target values
		for col in df.columns:
			if col == f"{coin}_target":
				coin_target = 0
				for value in df[col]:
					if value == 1:
						coin_target += 1
				#print(col + ": ", coin_target, " : ", (coin_target / 1332))



	sequential_data = []
	prev_days = deque(maxlen=SEQ_LEN)

	for i in df.values:
		prev_days.append([n for n in i[:-1]])

		if len(prev_days) == SEQ_LEN:
			sequential_data.append([np.array(prev_days), i[-1]])
			#print([np.array(prev_days), i])

	random.shuffle(sequential_data)

	buys = []
	sells = []

	for seq, target in sequential_data:
		#print(seq, " : ", target)
		if target == 0:
			sells.append([seq, target])
		elif target == 1:
			buys.append([seq, target])

	random.shuffle(buys)
	random.shuffle(sells)

	lower = min(len(buys), len(sells))

	buys = buys[:lower]
	sells = sells[:lower]

	sequential_data = buys+sells
	random.shuffle(sequential_data)

	X = []
	y = []

	for seq, target in sequential_data:
		X.append(seq)
		y.append(target)

	return np.array(X), y


for coin in used_coins:
	#set each filename of used coins
	dataset = f"data/{coin}.csv"
	#load the dataset of each coin specified above
	df = pd.read_csv(dataset)

	#set date string to unix timestamp
	for index, date in enumerate(df.iloc[:, 0]):
		df['Date'][index] = SetDateToUnix(date)

	df.rename(columns={"Open": f"{coin}_open", 
					   "High": f"{coin}_high",
					   "Low": f"{coin}_low", 
					   "Volume": f"{coin}_volume",
					   "Market Cap": f"{coin}_market cap"}, inplace=True)

	df.set_index("Date", inplace=True)

	df = df.replace({',': ''}, regex=True)#gets rid of number commas

	#the new dataframe only has the following columns
	df = df[[f"{coin}_open", 
			 f"{coin}_volume"]]

	#future value of that crypto coin at the next period
	df[f"{coin}_future"] = df[f"{coin}_open"].shift(-FUTURE_PERIOD_PREDICT)
	df.dropna(inplace=True)#omit not a number (NaN) rows
	df[f"{coin}_target"] = list(map(classify, df[f"{coin}_open"], df[f"{coin}_future"]))
	df.dropna(inplace=True)#omit not a number (NaN) rows
	df = df.drop(f"{coin}_future", 1)#not needed after target is made
	
	if len(main_df) == 0:
		main_df = df
	else:
		main_df = main_df.join(df)

main_df = main_df.iloc[::-1]#reverse array orientation so newest data is at the end

times = sorted(main_df.index.values)

#omitts the most recent 5% of data for use as a true predictions sample
last_5pct = times[-int(0.10*len(times))]

#validation is for predicting, main_df is the training data
validation_main_df = main_df[(main_df.index >= last_5pct)]
main_df = main_df[(main_df.index < last_5pct)]
#print(main_df)

#preprocess_df(main_df)
train_x, train_y = preprocess_df(main_df)
validation_x, validation_y = preprocess_df(validation_main_df)

print(f"train data: {len(train_x)} validation: {len(validation_x)}")
print(f"Dont buys: {train_y.count(0)}, buys: {train_y.count(1)}")
print(f"VALIDATION Dont buys: {validation_y.count(0)}, buys: {validation_y.count(1)}")

model = Sequential()
model.add(CuDNNLSTM(128, input_shape=(train_x.shape[1:]), return_sequences=True))
model.add(Dropout(0.2))
model.add(BatchNormalization())

model.add(CuDNNLSTM(128, input_shape=(train_x.shape[1:]), return_sequences=True))
model.add(Dropout(0.2))
model.add(BatchNormalization())

model.add(CuDNNLSTM(128, input_shape=(train_x.shape[1:])))
model.add(Dropout(0.2))
model.add(BatchNormalization())

model.add(Dense(32, activation='relu'))
model.add(Dropout(0.2))

model.add(Dense(2, activation='softmax'))

opt = tf.keras.optimizers.Adam(lr=0.001, decay=1e-6)

model.compile(loss='sparse_categorical_crossentropy',
			  optimizer=opt,
			  metrics=['accuracy'])

'''tensorboard = TensorBoard(log_dir=f"logs/{NAME}")

filepath = "RNN_Final-{epoch:02d}-{val_acc:.3f}"
checkpoint = ModelCheckpoint("models/{}.model".format(filepath, 
													  monitor='val_acc', 
													  verbose=1,
													  save_best_only=True,
													  mode='max'))'''

history = model.fit(
	train_x, train_y,
	epochs=EPOCHS,
	batch_size=BATCH_SIZE,
	validation_data=(validation_x, validation_y))
	#callbacks=[tensorboard, checkpoint])