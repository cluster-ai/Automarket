
#PyQt (GUI Framework)
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox


import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

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
		self.historical_cols = []
		self.graph_data = pd.DataFrame()#each column is another plot
		self.start_time = None
		self.end_time = None
		self.default_interval = 100 #100 datapoints

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
		self.hist_submit_btn.setGeometry(QtCore.QRect(120, 130, 131, 28))
		self.hist_submit_btn.setObjectName("hist_submit_btn")
		self.hist_submit_btn.clicked.connect(lambda: self.clicked_hist_submit())
		#hist scroll widgets
		self.hist_scroll_label = QtWidgets.QLabel(self.historical_tab)
		self.hist_scroll_label.setGeometry(QtCore.QRect(10, 179, 351, 31))
		self.hist_scroll_label.setAlignment(QtCore.Qt.AlignCenter)
		self.hist_scroll_label.setObjectName("hist_scroll_label")
		self.hist_scroll_area = QtWidgets.QScrollArea(self.historical_tab)
		self.hist_scroll_area.setGeometry(QtCore.QRect(40, 230, 301, 311))
		self.hist_scroll_area.setWidgetResizable(True)
		self.hist_scroll_area.setObjectName("hist_scroll_area")
		self.hist_scroll_widget = QtWidgets.QWidget()
		self.hist_scroll_widget.setGeometry(QtCore.QRect(0, 0, 299, 309))
		self.hist_scroll_widget.setObjectName("hist_scroll_widget")
		self.hist_scroll_area.setWidget(self.hist_scroll_widget)
		self.hist_scroll_layout = QtWidgets.QVBoxLayout()
		self.hist_scroll_widget.setLayout(self.hist_scroll_layout)

		self.tab_widget.addTab(self.historical_tab, "")

		#update graph btn
		self.hist_update_btn = QtWidgets.QPushButton(self.historical_tab)
		self.hist_update_btn.setGeometry(QtCore.QRect(92, 560, 191, 31))
		self.hist_update_btn.setObjectName("hist_update_btn")
		self.hist_update_btn.clicked.connect(self.update_graph)
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
		self.start_time_box = QtWidgets.QDateTimeEdit(self.interval_widget)
		self.start_time_box.setGeometry(QtCore.QRect(110, 10, 201, 31))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.start_time_box.setFont(font)
		self.start_time_box.setObjectName("start_time_box")
		self.end_time_box = QtWidgets.QDateTimeEdit(self.interval_widget)
		self.end_time_box.setGeometry(QtCore.QRect(110, 50, 201, 31))
		font = QtGui.QFont()
		font.setPointSize(10)
		self.end_time_box.setFont(font)
		self.end_time_box.setObjectName("end_time_box")
		self.interval_btn = QtWidgets.QPushButton(self.interval_widget)
		self.interval_btn.setGeometry(QtCore.QRect(50, 90, 221, 31))
		self.interval_btn.setObjectName("interval_btn")
		self.interval_btn.clicked.connect(self.update_graph)
		#graph widget
		self.graph_widget = QtWidgets.QWidget(self.centralwidget)
		self.graph_widget.setGeometry(QtCore.QRect(-1, 129, 681, 521))
		self.graph_widget.setObjectName("graph_widget")
		self.graph_layout = QtWidgets.QVBoxLayout(self.graph_widget)
		self.graph_layout.setContentsMargins(0, 0, 0, 0)
		self.graph_layout.setObjectName("graph_layout")

		self.figure = MatplotlibFigure()
		self.graph_layout.addWidget(self.figure)
		self.graph_widget.setLayout(self.graph_layout)

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

		#resets historical col list
		self.historical_cols = []

		#clear layout
		for i in reversed(range(self.hist_scroll_layout.count())): 
			self.hist_scroll_layout.itemAt(i).widget().setParent(None)

		#hist scroll buttons (shows data columns
		#available for chosen hist data)
		for col in self.historical_data.columns:
			btn = QtWidgets.QPushButton()
			btn.setCheckable(True)
			btn.setText(col)
			#btn.clicked.connect()
			self.hist_scroll_layout.addWidget(btn)


	def update_graph(self):
		#find interval of data
		'''
		data_end = self.graph_data.index.max()
		data_start = self.graph_data.index.min()
		'''

		self.start_time = 1568690100
		self.end_time = self.start_time + 300*100

		'''
		#keep graph interval in range of data
		if self.start_time > self.end_time:
			self.start_time = self.end_time
		#start time
		if self.start_time < data_start:
			self.start_time = data_start
		elif self.start_time > data_end:
			self.start_time = data_end
		#end time
		if self.end_time < data_start:
			self.end_time = data_start
		elif self.end_time > data_end:
			self.end_time = data_end
		'''

		#finds which hist_box column buttons are selected
		widgets = (self.hist_scroll_layout.itemAt(i).widget() 
					for i in range(self.hist_scroll_layout.count()))

		selected_columns = []
		for widget in widgets:
			if isinstance(widget, QtWidgets.QPushButton):
				if widget.isChecked() == True:
					selected_columns.append(widget.text())

		#adds selected columns to graph data
		self.graph_data = self.historical_data.loc[self.start_time:self.end_time, selected_columns]
		
		self.figure.plot(self.graph_data)


class MatplotlibFigure(QtWidgets.QWidget):

	# constructor
	def __init__(self):
		super().__init__()
		#self.layout = QBoxLayout()
		self.figure = matplotlib.figure.Figure()
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)

	def plot(self, data):
		self.figure.clf()
		ax = self.figure.add_subplot(111)
		for col in data.columns:
			ax.plot(data.loc[:, col])
		self.canvas.draw_idle()


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