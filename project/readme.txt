
////Cluster.Ai - Automarket//// v1.0 - Alpha (Pre-Launch)

This program is meant to interact with cryptocurrency markets in a way that maximizes profits through trading between different crypto-coins (no fiat interaction). Using historical data of the desired currencies, a LSTM neural network takes historical data from a crypto API in order improve its predictive ability as well as track its likelyhood of that prediction to be false. In doing so this model can intelligently intuit trading actions based on that model. 
It is unlikely that an A.I model of any kind feasible to an average programmer could manage to break even, let alone make money. But using a model that can accurately track its likelyhood and magnitude of error, I believe it would at least be able to not lose money (can't lose money if the model doesn't make any trades XD).


//Automarket Business Model - profit fees (revenue)//

/overview/
Looking at the leading competitor in AI trading software, I noticed their revenue is gained exclusively from a monthly fee of $150 (if you buy a year it is $50). This may work for well for larger scale operations but is a very high risk for smaller asset customers and a long-term committment. AI Trader's best advertised algorithm at any given time is ~18% gains per month. This is clearly handpicked out of their pool of algorithms and an average gain rate is likely less than half (on average); for the sake of argument, lets leave it at face value. At that growth rate (~18% per/month) you could only expect to break even at an initial total asset pool of $906.26 (again, this is very generous and is likely higher). 

While it is true that if the customer were to eat the trading subscription fee of $150 dollars out of pocket instead of pulling it from crypto, it would eventually make money. but in my experience a very large portion of the population are not comfortable with AI and would be averse to the subscription fee that costs more than 3 internet lines for something they are not sure will work. Not to mention the fact that they are almost garanteed to bleed money for 24 months until they finally break even with an initial asset pool of $100. The model I want to base the program on is a 15% fee on profit from transactions and a minimum starting pool of ~$50 (depending on exchange). This does mean a reduced growth rate but is still an easy decision when compared to the 28 months of losing money on AI trader (with initial asset pool of $50).

Now that I have established that $906.26 is roughly the "break even point" for AI trader using their best performing algorithm (assuming it never dips below an unlikely 18% every month) which is a profit margin of 0% vs my algorithms 15.3% (customer gains on my algorithm are 85% of 18%, since fee is 15% of profit). In order for an AI trader client to make an equivalent amount as my program after the first month is for the customer assets to be a whopping $6040.

Fact of the matter is that there is an entry gap for people to get value from the money they have dumped into the market. Most people are dissatisfied in the market and I believe a low risk value engine that only takes a small portion of profit as payment for the service is very attractive. This business model gives the customer a much higher confidence in our service, even if the algorithm is far worse than AI Trader. The profit margin is still positive beneath a total asset pool of $1000 vs the negative profit AI Trader will have with the same assets and growth rate. The higher growth rates below $6040 and the much lower risk nature of my program provides a service to the majority of people. As not many are willing to put in anything clost to $6040 in an AI trading algorithm assuming they have that much money in the first place.

/Algorithm performance targets/
Taking a portion of profit on trades makes having an optimized and powerfull trading algorithm of utmost importance (profit is directly correlated to performance). In light of this, I do not want to launch this algorithm without at least an average 1.07% return per month because that is roughly the point a client would double their assets in one year. However, if there is a large enough "vaccuum" of business to be had in this niche and I am confident of at least 100 customers in growth a year in paying customers; I will certainly consider settling for a growth rate of less than 1.07%.


//Neural Network Architecture//

/concept/
To generate intelligent trading, this model will use a combination of two network types: LSTM (Long short-term memory) and convolutional. The former being the primary market data predictor which will approximate future values of the market for each exchange and cryptocurrency being tracked. The convolutional network (responsible for optimizing trades), will be given information from the LSTM portion as well as the clients asset pool, trading fees, etc (This will be a one and done model to train as the data patterns do not change: very correlative).
Eventually I may want to incorporate an LSTM network in place of or parallel to the convolutional net previously defined. This would be to add a time series dimensionality that one would not otherwise get from a convolutional net. When considering the most optimized possible trading system, the most obvious trait (other than perfect knowledge of future market values) is the ability to trade across long periods of time since a market asset may continue to increase over several time steps. An LSTM trader may provide this functionality (at least to a more useful degree than strictly a convolutional net)
To continue with only a convolutional net (and simultaneously staying above the minimum growth margins outlined in the business model portion of this document) it needs to have an input for each next point the LSTM predicts times the number of cryptocurrencies being tracked. Each currency will have a pre-defined system of outputs from the network that control what assets are moving and where.

NOTE: I am not so sure throwing fee data into the mix for this convolutional net will work as intended but I suppose we can try it out and see what happens. Also consider the fact that LSTM data is more reliable (generally) the fewer time-steps worth of predictions it has made. For example, a prediction one time-step in the future is generally more accurate than a prediction 200 time-steps in the future.


//data file purposes//

*_index.json --- tends to hold information used to index other data. For the api it holds api keys and api request limit information. For historical data it tells you what data is available; file_names of the data, data intervals, naming conventions of crypto data files, etc.

handbook.json --- Contains references to what data is available from the coinAPI service such as currencies available, what currencies each exchange offers and the proper interval query format for time units (SEC1, MIN6, DAY10, etc).

config.json --- Program initialization parameters and behavior patterns (tracked-exchanges, handbook update frequency, time of last update, api url extensions).

{exchange}/{cryptocoin}_{fiat}.csv --- All the data available locally for the specified exchange for that cryptocoin using values relative to the specified fiat currency (currently only USD).


//API = [coinapi]//

The API class in this program is meant to offer the database a streamlined use of the api with needed error handling, request limit monitoring, request filtering, etc.

NOTE: all timestamps are stored as UTC. The time is then translated to the specified time zone (currently hard coded as HST) when printing to the screen.