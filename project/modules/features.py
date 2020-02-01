
#standard libraries
import datetime

#third-party packages
import pandas as pd

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
		features.at[index, 'price_average'] = delta(historical,
													'price_average',
													prev_index,
													index)
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
		#updates prev_index
		prev_index = index

	return features