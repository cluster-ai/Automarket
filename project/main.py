
if __name__ == "__main__":
	import database.database as database
	import neural_net

	'''
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
			self.neural_net = neural_net.NeuralNet(self.database)


	main = Main()