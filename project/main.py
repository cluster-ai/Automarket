
if __name__ == "__main__":
	import database.database as database
	import neural_net


	class Main():
		def __init__(self):
			self.database = database.Database()
			self.neural_net = neural_net.NeuralNet(self.database)


	main = Main()