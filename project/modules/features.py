
#standard libraries
import datetime

#third-party packages
import pandas as pd
import numpy as np

import time

#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
Features.py will be a too filled scrypt for creating features

New features can be added seamlessly as long as they return unique
names in the following format
features_return = new_df

new_df = pd.DataFrame(columns=['feature1', 'feature2'...], 
					  index='time_period_start')
'''

def time_series(historical):
	'''
	Creates following features
		/date/
		- weekday
		- month
		- day
		- year
		/time/
		- hour
		- minute

	Uses following historical data
		- time_period_start
	'''

	#empty df for the new feature data
	features = pd.DataFrame(index=historical['time_period_start'].index)

	#iterates through historical
	for index, row in historical.iterrows():
		#time_period_start value in unix-utc format
		time_start = int(row['time_period_start'])

		#creates new values for each feature 
		#noted in function description
		features.at[index, 'weekday'] = (
			datetime.datetime.utcfromtimestamp(time_start).strftime('%A'))
		features.at[index, 'month'] = int(
			datetime.datetime.utcfromtimestamp(time_start).strftime('%m'))
		features.at[index, 'day'] = int(
			datetime.datetime.utcfromtimestamp(time_start).strftime('%d'))
		features.at[index, 'year'] = int(
			datetime.datetime.utcfromtimestamp(time_start).strftime('%Y'))

		features.at[index, 'hour'] = int(
			datetime.datetime.utcfromtimestamp(time_start).strftime('%H'))
		features.at[index, 'minute'] = int(
			datetime.datetime.utcfromtimestamp(time_start).strftime('%M'))

	return features


def delta(historical):
	'''
	This function takes various historical values of crytpocurrency
	and converters it to change values. 
	ex: data[1] = (data[1] - data[0]) / data[0]

	Creates the following features
		/price/
		- price_average
		- price_low
		- price_high
		/other/
		- volume_traded
		- trades_count

	Uses follwing historical data
		- price_average
		- price_low
		- price_high
		- volume_traded
		- trades_count
	'''

	#empty df for the new feature data
	features = pd.DataFrame(index=historical['time_period_start'].index)

	#delta function: (data[1] - data[0]) / data[0]
	delta = lambda historical, col, prev_index, index : (
		(historical.at[index, col] / historical.at[prev_index, col]) - 1
	)

	#iterates through historical and computes delta
	prev_index = None
	for index, row in historical.iterrows():

		#skips first row
		if index == historical.index[0]:
			prev_index = index
			continue

		#/price/ features
		'''features.at[index, 'price_average'] = delta(historical,
													'price_average',
													prev_index,
													index)'''
		features.at[index, 'price_low'] = delta(historical,
												'price_low',
												prev_index,
												index)
		features.at[index, 'price_high'] = delta(historical,
												 'price_high',
												 prev_index,
												 index)

		#/other/ features
		features.at[index, 'volume_traded'] = delta(historical,
													'volume_traded',
													prev_index,
													index)
		features.at[index, 'trades_count'] = delta(historical,
												   'trades_count',
												   prev_index,
												   index)

		#used for continuity
		features.at[index, 'time_period_start'] = historical.at[index, 'time_period_start']

		#updates prev_index
		prev_index = index

	return features


def smooth(historical, time_increment, width=1):
	'''
	THIS CAN BE USED TO SIMPLIFY DATA FOR LARGER SEQUENCES
	IT ALSO HELPS REMOVE OUTLIERS FROM THE DATA

	This data iterates through DataFrame and averages each
	value with values directly adjacent to it

	Parameters:
		historical     : (pd.DataFrame()) data from one exchange
										  for one coin
		time_increment : (int) time_series increment of data in seconds
		width          : (positive int) number of points on each side
										of value used in smoothing algo

	Creates the following features
		/price/
		- price_average
		- price_low
		- price_high
		/other/
		- volume_traded
		- trades_count

	Uses follwing historical data
		- price_average
		- price_low
		- price_high
		- volume_traded
		- trades_count

	Assumptions:
		- historical.index values are incrementing evenly and continuously
		- historical.index values are increment by "time_increment" seconds
		- historical.isnan values are 0 if False and 1 if True
	'''

	#sets 'time_period_start' as the index of historical
	historical.set_index('time_period_start', drop=False, inplace=True)

	#creates a complete copy for the new data to be saved
	#this prevents changed values from influencing the algorithm
	data = historical.copy()

	#max and min indexes of historical data
	max_hist_index = historical.index.max()
	min_hist_index = historical.index.min()

	#iterates through historical and converts data values
	count = 0
	prev_time = time.time()#tracks duration
	for index, row in historical.iterrows():

		max_index = index + time_increment*width
		min_index = index - time_increment*width

		#if max or min indexes are outside of dataframe index,
		#it sets it to the next closest one
		if max_index >= max_hist_index:
			max_index = max_hist_index
		if min_index <= min_hist_index:
			min_index = min_hist_index

		#columns being smoothed
		columns = ['price_high']

		#array of values that will be used for average
		#in order of index
		vals = historical.loc[min_index:max_index, columns]

		#starts index count at zero for row 1 but
		#still incrementing by time_increment
		vals.index = vals.index - vals.index.min()

		#centers actual value at index 0
		#also sets index increment to 1
		vals.index = ((vals.index - width*time_increment)
					  / time_increment)

		#calculates the multiplier and adds it as a col
		vals['multiplier'] = vals.index
		vals['multiplier'] = width - abs(vals.loc[:, 'multiplier']) + 1

		#drop empty values
		vals.dropna(inplace=True)

		for col in columns:
			#average the vals
			average = (np.sum(vals[col]*vals['multiplier']) 
					   / np.sum(vals['multiplier']))

			#apply new average value
			data.at[index, col] = average

		if count % 10000 == 0:
			current_time = time.time()
			duration = current_time - prev_time
			prev_time = current_time
			print(f"Count: {count} | Duration: {duration}")

		count += 1

	return data