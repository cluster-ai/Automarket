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
        MainWindow.resize(1065, 711)
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
        self.hist_scroll = QtWidgets.QScrollArea(self.historical_tab)
        self.hist_scroll.setGeometry(QtCore.QRect(40, 70, 301, 451))
        self.hist_scroll.setWidgetResizable(True)
        self.hist_scroll.setObjectName("hist_scroll")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 299, 449))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.hist_scroll.setWidget(self.scrollAreaWidgetContents)
        self.hist_label = QtWidgets.QLabel(self.historical_tab)
        self.hist_label.setGeometry(QtCore.QRect(20, 20, 331, 31))
        self.hist_label.setAlignment(QtCore.Qt.AlignCenter)
        self.hist_label.setObjectName("hist_label")
        self.hist_update_btn = QtWidgets.QPushButton(self.historical_tab)
        self.hist_update_btn.setGeometry(QtCore.QRect(90, 550, 191, 31))
        self.hist_update_btn.setObjectName("hist_update_btn")
        self.tab_widget.addTab(self.historical_tab, "")
        self.feature_tab = QtWidgets.QWidget()
        self.feature_tab.setObjectName("feature_tab")
        self.feat_scroll = QtWidgets.QScrollArea(self.feature_tab)
        self.feat_scroll.setGeometry(QtCore.QRect(40, 130, 301, 391))
        self.feat_scroll.setWidgetResizable(True)
        self.feat_scroll.setObjectName("feat_scroll")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 299, 389))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.feat_scroll.setWidget(self.scrollAreaWidgetContents_2)
        self.feat_label = QtWidgets.QLabel(self.feature_tab)
        self.feat_label.setGeometry(QtCore.QRect(20, 20, 331, 31))
        self.feat_label.setAlignment(QtCore.Qt.AlignCenter)
        self.feat_label.setObjectName("feat_label")
        self.feat_update_btn = QtWidgets.QPushButton(self.feature_tab)
        self.feat_update_btn.setGeometry(QtCore.QRect(90, 550, 191, 31))
        self.feat_update_btn.setObjectName("feat_update_btn")
        self.create_feat_btn = QtWidgets.QPushButton(self.feature_tab)
        self.create_feat_btn.setGeometry(QtCore.QRect(90, 70, 191, 31))
        self.create_feat_btn.setObjectName("create_feat_btn")
        self.tab_widget.addTab(self.feature_tab, "")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(-1, 129, 681, 521))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.graph_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.graph_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_layout.setObjectName("graph_layout")
        self.interval_widget = QtWidgets.QWidget(self.centralwidget)
        self.interval_widget.setGeometry(QtCore.QRect(340, 0, 341, 131))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.interval_widget.setFont(font)
        self.interval_widget.setObjectName("interval_widget")
        self.time_label = QtWidgets.QLabel(self.interval_widget)
        self.time_label.setGeometry(QtCore.QRect(20, 0, 101, 51))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.time_label.setFont(font)
        self.time_label.setObjectName("time_label")
        self.start_time = QtWidgets.QDateTimeEdit(self.interval_widget)
        self.start_time.setGeometry(QtCore.QRect(120, 10, 201, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.start_time.setFont(font)
        self.start_time.setObjectName("start_time")
        self.day_btn = QtWidgets.QPushButton(self.interval_widget)
        self.day_btn.setGeometry(QtCore.QRect(30, 50, 81, 31))
        self.day_btn.setObjectName("day_btn")
        self.week_btn = QtWidgets.QPushButton(self.interval_widget)
        self.week_btn.setGeometry(QtCore.QRect(130, 50, 81, 31))
        self.week_btn.setObjectName("week_btn")
        self.month_btn = QtWidgets.QPushButton(self.interval_widget)
        self.month_btn.setGeometry(QtCore.QRect(230, 50, 81, 31))
        self.month_btn.setObjectName("month_btn")
        self.interval_label = QtWidgets.QLabel(self.interval_widget)
        self.interval_label.setGeometry(QtCore.QRect(20, 90, 301, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.interval_label.setFont(font)
        self.interval_label.setAlignment(QtCore.Qt.AlignCenter)
        self.interval_label.setObjectName("interval_label")
        self.index_id_widget = QtWidgets.QWidget(self.centralwidget)
        self.index_id_widget.setGeometry(QtCore.QRect(0, 0, 341, 131))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.index_id_widget.setFont(font)
        self.index_id_widget.setObjectName("index_id_widget")
        self.index_id_box = QtWidgets.QComboBox(self.index_id_widget)
        self.index_id_box.setGeometry(QtCore.QRect(50, 40, 251, 31))
        self.index_id_box.setCurrentText("")
        self.index_id_box.setObjectName("index_id_box")
        self.index_id_btn = QtWidgets.QPushButton(self.index_id_widget)
        self.index_id_btn.setGeometry(QtCore.QRect(110, 80, 121, 31))
        self.index_id_btn.setObjectName("index_id_btn")
        self.index_id_label = QtWidgets.QLabel(self.index_id_widget)
        self.index_id_label.setGeometry(QtCore.QRect(80, 0, 191, 41))
        self.index_id_label.setObjectName("index_id_label")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1065, 26))
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
        self.hist_label.setText(_translate("MainWindow", "No Item Selected"))
        self.hist_update_btn.setText(_translate("MainWindow", "Update Graph"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.historical_tab), _translate("MainWindow", "Historical Data"))
        self.feat_label.setText(_translate("MainWindow", "No Item Selected"))
        self.feat_update_btn.setText(_translate("MainWindow", "Update Graph"))
        self.create_feat_btn.setText(_translate("MainWindow", "Create Feature"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.feature_tab), _translate("MainWindow", "Feature Data"))
        self.time_label.setText(_translate("MainWindow", "Start Time:"))
        self.day_btn.setText(_translate("MainWindow", "1 Day"))
        self.week_btn.setText(_translate("MainWindow", "1 Week"))
        self.month_btn.setText(_translate("MainWindow", "1 Month"))
        self.interval_label.setText(_translate("MainWindow", "Current Interval: 1 Day"))
        self.index_id_btn.setText(_translate("MainWindow", "Submit"))
        self.index_id_label.setText(_translate("MainWindow", "Exchange, Coin, Period:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
