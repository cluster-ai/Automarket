
////Cluster.Ai - Automarket//// v1.0 - Alpha (Pre-Launch)

This program is meant to interact with cryptocurrency markets in a way that maximizes profits through trading between different crypto-coins (no fiat interaction). Using historical data of the desired currencies, a LSTM neural network takes historical data from a crypto API in order improve its predictive ability as well as track its likelyhood of that prediction to be false. In doing so this model can intelligently intuit trading actions based on that model. 
It is unlikely that an A.I model of any kind feasible to an average programmer could manage to break even, let alone make money. But using a model that can accurately track its likelyhood and magnitude of error, I believe it would at least be able to not lose money(can't lose money if the model doesn't make any trades XD).


//data file purposes//

*_index.json --- tends to hold information used to index other data. For the api it holds api keys and api request limit information. For historical data it tells you what data is available, file_names of the data, data intervals, naming conventions of crypto data files, etc.

handbook.json --- Contains references to what data is available from the coinAPI service such as currencies available, what currencies each exchange offers and proper interval query format for time units (SEC1, MIN6, DAY10, etc).

config.json --- Program initialization parameters and behavior patterns (tracked-exchanges, handbook update frequency, time of last update, api url extensions).

{exchange}/{cryptocoin}_{fiat}.csv --- All the data available locally for the specified exchange for that cryptocoin using values relative to the specified fiat currency (currently only USD).


//API = [coinapi]//

The API class in this program is meant to offer the database a streamlined use of the api with needed error handling, request limit monitoring, request filtering, etc.

NOTE: all data is stored as UTC. The time is then translated to the specified time zone (currently hard coded as HST) when printing to the screen.

At the time of writing this there is no way of getting request limit data from any api request. Instead it must have its own requests using one of the remaining requests.
Because of this I currently have the program track its requests and resets its values (this is an inaccurate bandaid fix that requires reseting) at initialization of CoinAPI object if the last recorded reset date has been at least 24 hours ago.