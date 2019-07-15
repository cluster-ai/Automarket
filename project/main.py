from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers

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
		self.graph = tf.keras.Sequential([
			layers.Dense(units=250, activation='relu', input_shape=[self.n_cols]),
			layers.Dense(units=250, activation='relu'),
			layers.Dense(units=250, activation='relu'),
			layers.Dense(units=2, activation='softmax')])

