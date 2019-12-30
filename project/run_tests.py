

import unittest


##########################################################################
#MODULES

import qa.test_preproc as test_preproc
print(
'\n//////////////////////////////////////////////////////////////////////')
print('Testing: preproc')
suite = unittest.TestLoader().loadTestsFromModule(test_preproc)
unittest.TextTestRunner().run(suite)


import qa.test_coinapi as test_coinapi
print(
'\n//////////////////////////////////////////////////////////////////////')
print('Testing: coinapi')
suite = unittest.TestLoader().loadTestsFromModule(test_coinapi)
unittest.TextTestRunner().run(suite)


##########################################################################
#