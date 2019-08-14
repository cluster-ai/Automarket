
////Cluster.Ai - Automarket//// v1.0 - Alpha (Pre-Launch)

This program is meant to interact with cryptocurrency markets in a way that maximizes profits through trading between different crypto-coins (no fiat interaction). Using historical data of the desired currencies, a LSTM neural network takes historical data from a crypto API in order improve its predictive ability as well as track its likelyhood of that prediction to be false. In doing so this model can intelligently intuit trading actions based on that model. 
It is unlikely that an A.I model of any kind feasible to an average programmer could manage to break even, let alone make money. But using a model that can accurately track its likelyhood and magnitude of error, I believe it would at least be able to not lose money (can't lose money if the model doesn't make any trades XD).


//Automarket Business Model - profit fees (revenue)//

Looking at the leading competitor in AI trading software, I noticed their revenue is gained exclusively from a monthly fee of a minimum $150 for the starter pack. This may work for well for larger scale operations but is very high risk for smaller asset customers. For example, their advertised best algorithm at any given time is ~18% gains per month. This is clearly handpicked out of their pool of algorithms and an average gain rate is likely lower; for the sake of argument, lets leave it at face value. At that growth rate (~18% per/month) you could only expect to break even at an initial total asset pool of $906.26 (if you are lucky this will break even on AI trader). 

While it is true that if the customer were to eat the trading subscription fee of $150 dollars out of pocket instead of pulling it from crypto, it would eventually make money. but in my experience a very large portion of the population are not comfortable with AI and would be averse to the subscription fee that costs more than 3 internet lines for something they are not sure will work. Not to mention the fact that they are almost garanteed to bleed money for 24 months until they finally break even with an initial asset pool of $100. The model I want to base the program on is a 15% fee on profit from transactions and a minimum starting pool of ~$50 (depending on exchange). This does mean a reduced growth rate but is still an easy decision when compared to the 28 months of losing money on AI trader (with initial asset pool of $50).

Now that I have established that $906.26 is roughly the "break even point" for AI trader using their best performing algorithm (assuming it never dips below an unlikely 18% every month) which is a profit margin of 0% vs my algorithms 15.3% (since the actual profit is 85% of 18% for fee). The point at which ai trader will make the same money as my algorithm is for the customer to have a whopping $6040 in total trade assets, at which point their profit is an equivalent 85% growth rate to my program.

Fact of the matter is that there is a entry gap for people to get value from the money they have dumped into the market. Most people are dissatisfied in the market and I believe a low risk value engine that only takes a small portion of profit as payment for the service is very attractive. This business model gives the customer a much higher confidence in our service. Even if the algorithm is far worse than AI Trader, the profit margin is still positive beneath a total asset pool of $1000 vs the negative profit AI Trader will have with the same assets and growth rate. The higher growth rates below $6040 and the much lower risk nature of my program provides a service to the majority of people looking to trade their assets since not many are willing to put in more than $6040 in an AI trading algorithm assuming they even have that high of an asset pool at all.


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