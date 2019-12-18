

#standard libraries
import math
import time
import datetime

import numpy as np


def print_progress_bar(iteration, total, prefix = '', suffix = ''):
	#these varibales used to be parameters but there is no need to have them change
	length = 49
	fill = '/'
	printEnd = "\r"
	decimals = 1

	'''
	Call in a loop to create terminal progress bar
	Parameters:
		iteration   - Required  : current iteration (Int)
		total       - Required  : total iterations (Int)
		prefix      - Optional  : prefix string (Str)
		suffix      - Optional  : suffix string (Str)
		decimals    - Optional  : positive number of decimals in percent complete (Int)
		length      - Optional  : character length of bar (Int)
		fill        - Optional  : bar fill character (Str)
		printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
	'''
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
	# Print New Line on Complete
	if iteration == total: 
		print()


def thread_monitor(progress, compute_total, thread_total):
	'''
	Parameters:
		progress       : number of computed items from each thread (shared dict)
		compute_total  : total number of items to be computed (int)
	'''
	prog_count = 0
	threads = 1
	while prog_count < compute_total:
		prog_part = progress['part']
		print_progress_bar(prog_count, compute_total, 
						   suffix=f' | {prog_part}, threads: {threads}/{thread_total}')
		
		for key, val in progress.items()
			if key == 'threads':
				threads = len(val) + 1 #plus 1 for monitoring thread
			elif key == 'count':
				prog_count = sum(val.values())

