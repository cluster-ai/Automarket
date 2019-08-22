

import database.coin_api as coin_api
import database.database as database

import pandas as pd

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


main = Main()