
import database.coin_api as coin_api
import database.database as database

from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler

import pandas as pd

import time


data = database.Database()

df = data.LoadHistoricalData('KRAKEN', 'SPOT_LTC_USD.csv')

count = 0
prev_time = time.time()
start_time = time.time()
new_df = df
new_row = pd.DataFrame(columns=df.columns)

for index, row in df.iterrows():
	for col in df.columns:

		if 'time' in col:#if true, needs to be changed to unix time
			new_df.at[index, col] = data.SetDateToUnix(row[col])
	count += 1
	if count == 1000:
		current_time = time.time()
		delay = current_time - prev_time
		print(f"index: {index} || delay: {delay}")
		count = 0
		prev_time = current_time

total_time = time.time() - start_time
print(f"total duration: {total_time}")
print(new_df.head())

'''
class Main():
	def __init__():
		self.database = database.Database()

	def PreprocessData(self, )
'''