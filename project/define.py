
#global

from modules.database import Database
from modules.historical import Historical
from modules.features import Features


def init():
	Database.__init__()
	Historical.__init__()
	Features.__init__()


def index_id(exchange_id, coin_id, period_id):
	'''
	generates an index_id based on arguments

	Parameters:
		exchange_id    : (str) name of exchange in bold: 'KRAKEN'
		coin_id        : (str) crytpocurrency id: 'BTC'
		period_id      : (str) time increment of data in coinapi
							   period_id format
	'''
	#verifies each of the given arguments
	Historical.verify_exchange(exchange_id)
	Historical.verify_period(period_id)
	Historical.verify_coin(coin_id)

	return f'{exchange_id}_{coin_id}_{period_id}'