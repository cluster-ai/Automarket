
#global

from modules.database import Database
from modules.coinapi import Coinapi

def init():
	Database.__init__()
	Coinapi.__init__()