
#PyQt (GUI Framework)
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

import random

#standard libraries
from itertools import count

#third-party packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#local modules
from define import *
import modules.preproc as preproc
import modules.features as features


#79 character absolute limit
###############################################################################

#72 character recommended limit
########################################################################

'''
NOTE: TO CREATE A GRAPH, USE ONLY THE "graph" FUCNTION
	  DO NOT CREATE INSTANCE OF GRAPHER (its unnecessary)

The "Graph" class will be used as a continuously updating 
representation of data. The built in features of this class
will be for data stored in the database, any other data must 
be loaded into it via argument.

For version 1 (if time permits), this module would benefit from
being nested in a UI allowing the user to change graph data/options
without having to reopen it manually. (use PyQt UI framework)

For Dynamic Scrolling List of Buttons:
- a container widget that you put in the QScrollArea,
- a QHBoxLayout on that widget.
- add your new buttons to that horizontal layout.
'''

class Ui_MainWindow(object):
	def setupUi(self, MainWindow):
		MainWindow.setObjectName("MainWindow")
		MainWindow.resize(1070, 710)
		self.centralwidget = QtWidgets.QWidget(MainWindow)
		self.centralwidget.setObjectName("centralwidget")

		#initializes graph data variables
		self.historical_data = pd.DataFrame()

		###TAB WIDGET###
		self.tab_widget = QtWidgets.QTabWidget(self.centralwidget)
		self.tab_widget.setGeometry(QtCore.QRect(680, 0, 381, 651))
		self.tab_widget.setMinimumSize(QtCore.QSize(381, 0))
		font = QtGui.QFont()
		font.setPointSize(12)
		self.tab_widget.setFont(font)
		self.tab_widget.setIconSize(QtCore.QSize(20, 20))
		self.tab_widget.setObjectName("tab_widget")
		#historical tab
		self.historical_tab = QtWidgets.QWidget()
		self.historical_tab.setObjectName("historical_tab")
		#hist combo box
		self.hist_box = QtWidgets.QComboBox(self.historical_tab)
		self.hist_box.setGeometry(QtCore.QRect(60, 60, 251, 31))
		self.hist_box.setCurrentText("")
		self.hist_box.setObjectName("hist_box")
		hist_list = list(Database.historical_index.keys())
		self.hist_box_val = str(self.hist_box.currentText())

		self.hist_box.addItems(hist_list)#populates combobox
		self.hist_box_label = QtWidgets.QLabel(self.historical_tab)
		self.hist_box_label.setGeometry(QtCore.QRect(80, 10, 221, 41))
		self.hist_box_label.setObjectName("hist_box_label")
		self.hist_submit_btn = QtWidgets.QPushButton(self.historical_tab)
		self.hist_submit_btn.setGeometry(QtCore.QRect(120, 110, 131, 28))
		self.hist_submit_btn.setObjectName("hist_submit_btn")
		self.hist_submit_btn.clicked.connect(lambda: self.clicked_hist_submit())
		#hist scroll widgets
		self.hist_scroll_label = QtWidgets.QLabel(self.historical_tab)
		self.hist_scroll_label.setGeometry(QtCore.QRect(10, 179, 351, 31))
		self.hist_scroll_label.setAlignment(QtCore.Qt.AlignCenter)
		self.hist_scroll_label.setObjectName("hist_scroll_label")
		self.hist_scroll_area = QtWidgets.QScrollArea(self.historical_tab)
		self.hist_scroll_area.setGeometry(QtCore.QRect(40, 230, 301, 231))
		self.hist_scroll_area.setWidgetResizable(True)
		self.hist_scroll_area.setObjectName("hist_scroll_area")
		self.hist_scroll_widget = QtWidgets.QWidget()
		self.hist_scroll_widget.setGeometry(QtCore.QRect(0, 0, 299, 229))
		self.hist_scroll_widget.setObjectName("hist_scroll_widget")
		self.hist_scroll_area.setWidget(self.hist_scroll_widget)
		self.hist_scroll_layout = QtWidgets.QVBoxLayout()

		self.tab_widget.addTab(self.historical_tab, "")

		#update graph btn
		self.hist_update_btn = QtWidgets.QPushButton(self.historical_tab)
		self.hist_update_btn.setGeometry(QtCore.QRect(92, 480, 191, 31))
		self.hist_update_btn.setObjectName("hist_update_btn")
		#feature tab
		self.feature_tab = QtWidgets.QWidget()
		self.feature_tab.setObjectName("feature_tab")
		self.tab_widget.addTab(self.feature_tab, "")

		###static widget###
		self.static_widget = QtWidgets.QWidget(self.centralwidget)
		self.static_widget.setGeometry(QtCore.QRect(0, 0, 681, 131))
		self.static_widget.setObjectName("static_widget")
		self.interval_widget = QtWidgets.QWidget(self.static_widget)
		self.interval_widget.setGeometry(QtCore.QRect(360, 0, 321, 131))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.interval_widget.setFont(font)
		self.interval_widget.setObjectName("interval_widget")
		self.interval_label1 = QtWidgets.QLabel(self.interval_widget)
		self.interval_label1.setGeometry(QtCore.QRect(10, 0, 101, 51))
		font = QtGui.QFont()
		font.setPointSize(11)
		self.interval_label1.setFont(font)
		self.interval_label1.setObjectName("interval_label1")
		self.interval_label2 = QtWidgets.QLabel(self.interval_widget)
		self.interval_label2.setGeometry(QtCore.QRect(20, 40, 91, 51))
		font = QtGui.QFont()
		font.setPointSize(11)
		self.interval_label2.setFont(font)
		self.interval_label2.setObjectName("interval_label2")
		self.start_time = QtWidgets.QDateTimeEdit(self.interval_widget)
		self.start_time.setGeometry(QtCore.QRect(110, 10, 201, 31))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.start_time.setFont(font)
		self.start_time.setObjectName("start_time")
		self.end_time = QtWidgets.QDateTimeEdit(self.interval_widget)
		self.end_time.setGeometry(QtCore.QRect(110, 50, 201, 31))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.end_time.setFont(font)
		self.end_time.setObjectName("end_time")
		self.interval_btn = QtWidgets.QPushButton(self.interval_widget)
		self.interval_btn.setGeometry(QtCore.QRect(50, 90, 221, 31))
		self.interval_btn.setObjectName("interval_btn")
		self.graph_widget = QtWidgets.QWidget(self.centralwidget)
		self.graph_widget.setGeometry(QtCore.QRect(0, 130, 681, 521))
		self.graph_widget.setObjectName("graph_widget")
		MainWindow.setCentralWidget(self.centralwidget)
		self.menubar = QtWidgets.QMenuBar(MainWindow)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 1070, 26))
		self.menubar.setObjectName("menubar")
		MainWindow.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(MainWindow)
		self.statusbar.setObjectName("statusbar")
		MainWindow.setStatusBar(self.statusbar)

		self.retranslateUi(MainWindow)
		self.tab_widget.setCurrentIndex(0)
		QtCore.QMetaObject.connectSlotsByName(MainWindow)

	def retranslateUi(self, MainWindow):
		_translate = QtCore.QCoreApplication.translate
		MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
		self.hist_box_label.setText(_translate("MainWindow", "Exchange, Coin, Period:"))
		self.hist_submit_btn.setText(_translate("MainWindow", "Submit"))
		self.hist_scroll_label.setText(_translate("MainWindow", "No Item Selected"))
		self.hist_update_btn.setText(_translate("MainWindow", "Update Graph"))
		self.tab_widget.setTabText(self.tab_widget.indexOf(self.historical_tab), _translate("MainWindow", "Historical Data"))
		self.tab_widget.setTabText(self.tab_widget.indexOf(self.feature_tab), _translate("MainWindow", "Feature Data"))
		self.interval_label1.setText(_translate("MainWindow", "Start Time:"))
		self.interval_label2.setText(_translate("MainWindow", "End Time:"))
		self.interval_btn.setText(_translate("MainWindow", "Update Graph"))


	def clicked_hist_submit(self):
		#find what the latest hist box value is (index_id of hist)
		self.hist_box_val = str(self.hist_box.currentText())

		#update scroll box label
		self.hist_scroll_label.setText(f"Historical: {self.hist_box_val}")

		#loads historical data into memory using hist_box index_id
		self.historical_data = Database.historical(self.hist_box_val)

		#clear layout
		self.hist_scroll_layout = QtWidgets.QVBoxLayout()

		#hist scroll buttons (shows data columns
		#available for chosen hist data)
		for col in self.historical_data.columns:
			btn = QtWidgets.QPushButton()
			btn.setText(col)
			self.hist_scroll_layout.addWidget(btn)

		self.hist_scroll_widget.setLayout(self.hist_scroll_layout)


def window():
	app = QtWidgets.QApplication(sys.argv)
	MainWindow = QtWidgets.QMainWindow()
	ui = Ui_MainWindow()
	ui.setupUi(MainWindow)
	MainWindow.show()
	sys.exit(app.exec_())



'''
from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class App(QMainWindow):

	def __init__(self):
		super().__init__()
		self.left = 10
		self.top = 10
		self.title = 'PyQt5 matplotlib example - pythonspot.com'
		self.width = 640
		self.height = 400
		self.initUI()

	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		m = PlotCanvas(self, width=5, height=4)
		m.move(0,0)

		button = QPushButton('PyQt5 button', self)
		button.setToolTip('This s an example button')
		button.move(500,0)
		button.resize(140,100)

		self.show()


class PlotCanvas(FigureCanvas):

	def __init__(self, parent=None, width=6, height=5, dpi=100):
		self.datapoints = 100 #datapoints
		self.raw = Database.historical('KRAKEN_BTC_5MIN')

		fig = Figure(figsize=(width, height), dpi=dpi)
		self.axes = fig.add_subplot(111)

		FigureCanvas.__init__(self, fig)
		self.setParent(parent)

		FigureCanvas.setSizePolicy(self,
			QSizePolicy.Expanding,
			QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

		self.plot()



	def plot(self):
		end_time = 1537789800
		start_time = end_time - (300 * self.datapoints)

		#self.index += 1
		ax = self.figure.add_subplot(111)

		display_raw = self.raw.loc[start_time:end_time, 'price_high']

		ax.plot(display_raw)
		ax.set_title('PyQt Matplotlib Example')
		self.draw()


def start():
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())
'''