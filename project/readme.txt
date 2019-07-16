
////Cluster.Ai - Automarket//// v1.0 - Alpha (Pre-Launch)

This program is meant to interact with cryptocurrency markets in a way that maximizes profits through trading between different crypto-coins (no fiat interaction). Using historical data of the desired currencies, a LSTM neural network takes historical data from a crypto API in order improve its predictive ability as well as track its likelyhood of that prediction to be false. In doing so this model can intelligently intuit trading actions based on that model. 
It is unlikely that an A.I model of any kind feasible to an average programmer could manage to break even, let alone make money. But using a model that can accurately track its likelyhood and magnitude of error, I believe it would at least be able to not lose money(can't lose money if the model doesn't make any trades XD).


//API = [coinapi]//

The API class in this program is meant to offer the database a standardized use of data in a format most suited for it. In this way, the API class is a middle-man that translates all data requests from the database and puts it into terms the API can understand and vise versa.

Relevant API data available:
MetaData:
 - coin/exchange naming conventions
 - coin types (fiat or crypto)
 - available exchanges and their web-addresses
 - coin/exchange query symbols
OHLCV Bar Data:
 - Interval of following data
 - Time of first and last transaction (open & close) on given exchange
 - Price at open-high-low-close of interval.
 - Volume traded during interval (not sure if its in coins or fiat)
 - Number of trades during interval (int)

API
 - 