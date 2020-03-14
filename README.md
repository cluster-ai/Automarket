# Automarket
Automarket is a multi-purpose data visualization tool to find predictable patterns within data

## Automarket Alpha-v1.0 Design Overview
### 3/9/20

### Developers: Jason Godmere


### Code Style: PEP 8


### Project Overview:
Automarket is a tool for creating a financial model of cryptocurrency markets using historical data from numerous exchanges. The end goal is to provide the user with a workbench to create and visualize custom features for use in financial modeling/analysis.

### Context: 
This program can be broken up into 5 distinct parts: interface, market data api requests, custom feature creation, data vizualization, and data storage. The purpose of this document is to provide a clearunderstanding of each part and elaborate on how they interact from a high-level.

### Outline:
The end goal of this application is to remove as many barriers aspossible from the process of creating cryptocurrency data features.

* Graphical User Interface (window.py):
	* Acts as the skeleton of the app.
	* scale the widgets in the window to whatever size is needed by the user. 
	* maintains a resolution ratio range and minimum window size for each axis
	* tooling for system notifications and loading bars

* Market Data Interface (coinapi.py):
	* Gather market data by exchange, currency and period (time_interval)
	* Track particular user-defined exchanges to declutter UI
	* Track all the available currencies that are common across alltracked exchanges
	* Monitor and record request errors and display relevent requestdata to the user (remaining, reset, limit)
	* provide an api set-up feature to add api keys and what you want each key to be used for (backfilling and exchange/currency tracking)

* Custom Feature Creation (feature.py):
	* Provide a core set of feature functions
	* split features into two types: numerical and categorical. Featuresdesigned for one may not work for another.
	* User creates a feature "frame" that is used as an instructionmanual for generating that feature data
	* Stack features based on feature type
	* May need a hybrid datatype for things with a category and number

* Data Visualization (diagram.py):
	* Matplotlib ustilizing Line Graph, Histogram, Pie Chart, Box andWhiskers diagrams for categorical and numerical data.
	* Track what diagram each historical and feature data type canbe plotted on. 
	* dynamic interval setter for diplaying more or less data and forvarious positions along the timeline
	* an option to normalize/scale data as seen on diagram in orderto compare data at different units/scales
	* Many feature functions break down at the end of a dataset. Allow user to view that edge from any interval in real time
	* real time scrolling of data for timeline graphs.
	* implement legend, x and y axis labels as well as grid markers, preferably with style so it is easier to read and less ugly

* Data Storage (database.py):
	* CRUD (Create, Read, Update, Delete) manager for all data beingstored long term
	* Utilize json files for indexing csv and other data storage task.