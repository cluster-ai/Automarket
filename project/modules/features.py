
#standard libraries
import datetime

#third-party packages
import pandas as pd
import numpy as np

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


def smooth(historical, time_increment):
	'''
	
	THIS CAN BE USED TO SIMPLIFY DATA FOR LARGER SEQUENCES
	IT ALSO HELPS REMOVE OUTLIERS FROM THE DATA

	This data iterates through DataFrame and averages each
	value with values directly adjacent to it

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

	#iterates through historical and converters data values
	for index, row in historical.iterrows():

		prev_index = index - time_increment
		next_index = index + time_increment

		#verifies adjacent indexes exist
		if (prev_index not in historical.index or 
				next_index not in historical.index):
			data.loc[index, :] = np.nan
			continue

		#iterates through columns
		for col in historical.columns:
			#verifies col is one that will be converted
			if col in ['price_high', 'price_low',
					   'volume_traded', 'trades_count']:

				#loads values
				prev_val = historical.at[prev_index, col]
				next_val = historical.at[next_index, col]
				val = row[col]

				#creates new val and saves it to data
				new_val = (prev_val + next_val + val) / 3
				data.at[index, col] = new_val

	return data