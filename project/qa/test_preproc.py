
#module being tested
import modules.preproc as preproc

import unittest
import numpy as np


class TestDproc(unittest.TestCase):

	def test_unix_and_date_time_conversion(self):
		#Tests preproc.date_to_unix() and preproc.unix_to_date()
		test_vals = {
			'case1': {
				'unix': 10000,
				'date': '1970-01-01T02:46:40.0000000Z'
			},
			'case2': {
				'unix': 10000.1000000,
				'date': '1970-01-01T02:46:40.1000000Z'
			},
			'case3': {
				'unix': 10000.9999999,
				'date': '1970-01-01T02:46:40.9999999Z'
			},
			'case4': {
				'unix': 0.1000000,
				'date': '1970-01-01T00:00:00.1000000Z'
			},
			'case5': {
				'unix': 0.9999999,
				'date': '1970-01-01T00:00:00.9999999Z'
			}
		}

		for case, vals in test_vals.items():
			unix = vals['unix']
			date = vals['date']
			self.assertEqual(preproc.unix_to_date(unix), date)
			self.assertEqual(preproc.date_to_unix(date), unix)


	def test_add_average_price(self):
		pass


	def test_scale(self):
		'''
		NOTE: the parameter 'custom_range' is untested
		'''
		#these represent min max
		value_ranges = {
			'case1': [0, 10],
			'case1': [0, 10.1],
			'case3': [-10, 0],
			'case3': [-10.1, 0],
			'case5': [-10, 10],
			'case5': [-10.1, 10.1]
		}
		#runs through value_ranges to make initial test array
		for case, val in value_ranges.items():
			test_array = np.random.uniform(low=val[0], high=val[1], size=(50,))
			#creates a list of 50 items with specified min max
			#set np array to list
			max_val = np.amax(test_array)
			min_val = np.amin(test_array)

			#runs through value_ranges again to test different new_range values
			for case, val in value_ranges.items():

				#scales test_array to val range
				scaled_array = preproc.scale(test_array, new_range=[val[0], val[1]])
				scaled_max = np.amax(scaled_array)
				scaled_min = np.amin(scaled_array)
				#verifies scaled min max matches new_range
				self.assertEqual(scaled_min, val[0])
				self.assertEqual(scaled_max, val[1])
				
				#scales scaled_data to original min max val range of test_array
				unscaled_array = preproc.scale(scaled_array, new_range=[min_val, max_val])
				#verifies unscaled_array matches test_array up to 15 decimals
				#to make room for float point error
				np.testing.assert_array_almost_equal(unscaled_array, test_array, decimal=14)
				#self.assertTrue((unscaled_array == test_array).all())


if __name__ == '__main__':
    unittest.main()