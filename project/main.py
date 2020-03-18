

if __name__ == "__main__":
	from define import *
	init()


	#tests
	from modules.features import Feature

	feature = Feature('KRAKEN_BTC_5MIN')

	feature.add_layer('smooth', width=1)

	feature.add_layer('delta')

	print(feature.layers)
	print(feature.output_type)