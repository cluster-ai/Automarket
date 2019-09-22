
from pandas_datareader import data
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import urllib.request, json 
import os
import numpy as np
import tensorflow as tf # This code has been tested with TensorFlow 1.6
from sklearn.preprocessing import MinMaxScaler

import database.database as database

database = database.Database()

df = database.LoadTrainingData('KRAKEN_SPOT_BTC_USD.csv')

plt.figure(figsize = (18,9))
plt.plot(range(df.shape[0]),(df['price_low']+df['price_high'])/2.0)
plt.xticks(range(0,df.shape[0],500),df['time_period_start'].loc[::500],rotation=45)
plt.xlabel('Date',fontsize=18)
plt.ylabel('Mid Price',fontsize=18)
plt.show()

high_prices = df.loc[:, 'price_high'].values #.values is the same as .as_matrix
low_prices = df.loc[:, 'price_low'].values
mid_prices = (high_prices+low_prices)/2

init_index = 140000
train_index_end = init_index+11000
test_index_end = train_index_end+1000
#data
train_data = mid_prices[init_index:train_index_end]
test_data = mid_prices[train_index_end:test_index_end]
