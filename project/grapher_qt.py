# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'grapher.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1072, 712)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_widget.setGeometry(QtCore.QRect(680, 0, 381, 651))
        self.tab_widget.setMinimumSize(QtCore.QSize(381, 0))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.tab_widget.setFont(font)
        self.tab_widget.setIconSize(QtCore.QSize(20, 20))
        self.tab_widget.setObjectName("tab_widget")
        self.historical_tab = QtWidgets.QWidget()
        self.historical_tab.setObjectName("historical_tab")
        self.index_id_box = QtWidgets.QComboBox(self.historical_tab)
        self.index_id_box.setGeometry(QtCore.QRect(60, 60, 251, 31))
        self.index_id_box.setCurrentText("")
        self.index_id_box.setObjectName("index_id_box")
        self.hist_box_label = QtWidgets.QLabel(self.historical_tab)
        self.hist_box_label.setGeometry(QtCore.QRect(80, 10, 221, 41))
        self.hist_box_label.setObjectName("hist_box_label")
        self.hist_submit_btn = QtWidgets.QPushButton(self.historical_tab)
        self.hist_submit_btn.setGeometry(QtCore.QRect(120, 110, 131, 28))
        self.hist_submit_btn.setObjectName("hist_submit_btn")
        self.hist_scroll_label = QtWidgets.QLabel(self.historical_tab)
        self.hist_scroll_label.setGeometry(QtCore.QRect(10, 179, 351, 31))
        self.hist_scroll_label.setAlignment(QtCore.Qt.AlignCenter)
        self.hist_scroll_label.setObjectName("hist_scroll_label")
        self.hist_scroll = QtWidgets.QScrollArea(self.historical_tab)
        self.hist_scroll.setGeometry(QtCore.QRect(40, 230, 301, 311))
        self.hist_scroll.setWidgetResizable(True)
        self.hist_scroll.setObjectName("hist_scroll")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 299, 309))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.hist_scroll.setWidget(self.scrollAreaWidgetContents)
        self.hist_update_btn = QtWidgets.QPushButton(self.historical_tab)
        self.hist_update_btn.setGeometry(QtCore.QRect(92, 560, 191, 31))
        self.hist_update_btn.setObjectName("hist_update_btn")
        self.tab_widget.addTab(self.historical_tab, "")
        self.feature_tab = QtWidgets.QWidget()
        self.feature_tab.setObjectName("feature_tab")
        self.tab_widget.addTab(self.feature_tab, "")
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
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(-1, 129, 681, 521))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.graph_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.graph_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_layout.setObjectName("graph_layout")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1072, 26))
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


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
