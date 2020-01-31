
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

	Uses folloing df historical columns
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