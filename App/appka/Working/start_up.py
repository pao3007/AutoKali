# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'start_up.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Setup(object):
    def setupUi(self, Setup):
        Setup.setObjectName("Setup")
        Setup.resize(592, 311)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(127, 127, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 170, 170))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 85, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(227, 227, 227))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(160, 160, 160))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(160, 160, 160))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(105, 105, 105))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(245, 245, 245))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(127, 127, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(127, 127, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 170, 170))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(127, 127, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(127, 127, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 120, 215))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(245, 245, 245))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.PlaceholderText, brush)
        Setup.setPalette(palette)
        self.centralwidget = QtWidgets.QWidget(Setup)
        self.centralwidget.setObjectName("centralwidget")
        self.start_app = QtWidgets.QPushButton(self.centralwidget)
        self.start_app.setGeometry(QtCore.QRect(230, 226, 141, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.start_app.setFont(font)
        self.start_app.setObjectName("start_app")
        self.sens_type_label = QtWidgets.QLabel(self.centralwidget)
        self.sens_type_label.setGeometry(QtCore.QRect(60, 60, 231, 41))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.sens_type_label.setFont(font)
        self.sens_type_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.sens_type_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.sens_type_label.setObjectName("sens_type_label")
        self.sens_type_comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.sens_type_comboBox.setGeometry(QtCore.QRect(310, 70, 171, 24))
        self.sens_type_comboBox.setObjectName("sens_type_comboBox")
        self.open_settings_btn = QtWidgets.QPushButton(self.centralwidget)
        self.open_settings_btn.setGeometry(QtCore.QRect(50, 225, 111, 41))
        self.open_settings_btn.setObjectName("open_settings_btn")
        self.app_label = QtWidgets.QLabel(self.centralwidget)
        self.app_label.setGeometry(QtCore.QRect(0, 0, 601, 41))
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.app_label.setFont(font)
        self.app_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.app_label.setAlignment(QtCore.Qt.AlignCenter)
        self.app_label.setObjectName("app_label")
        self.status_opt_label = QtWidgets.QLabel(self.centralwidget)
        self.status_opt_label.setGeometry(QtCore.QRect(310, 146, 281, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.status_opt_label.setFont(font)
        self.status_opt_label.setObjectName("status_opt_label")
        self.status_label = QtWidgets.QLabel(self.centralwidget)
        self.status_label.setGeometry(QtCore.QRect(140, 171, 151, 21))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.status_label.setFont(font)
        self.status_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.status_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.status_label.setObjectName("status_label")
        self.status_ref_label = QtWidgets.QLabel(self.centralwidget)
        self.status_ref_label.setGeometry(QtCore.QRect(310, 166, 281, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.status_ref_label.setFont(font)
        self.status_ref_label.setObjectName("status_ref_label")
        self.null_detect_label = QtWidgets.QLabel(self.centralwidget)
        self.null_detect_label.setGeometry(QtCore.QRect(0, 270, 16, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.null_detect_label.setFont(font)
        self.null_detect_label.setAlignment(QtCore.Qt.AlignCenter)
        self.null_detect_label.setObjectName("null_detect_label")
        self.opt_channel_label = QtWidgets.QLabel(self.centralwidget)
        self.opt_channel_label.setGeometry(QtCore.QRect(60, 90, 231, 41))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.opt_channel_label.setFont(font)
        self.opt_channel_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.opt_channel_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.opt_channel_label.setObjectName("opt_channel_label")
        self.opt_config_combobox = QtWidgets.QComboBox(self.centralwidget)
        self.opt_config_combobox.setGeometry(QtCore.QRect(310, 100, 171, 24))
        self.opt_config_combobox.setObjectName("opt_config_combobox")
        self.status_gen_label = QtWidgets.QLabel(self.centralwidget)
        self.status_gen_label.setGeometry(QtCore.QRect(310, 186, 281, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.status_gen_label.setFont(font)
        self.status_gen_label.setObjectName("status_gen_label")
        self.logo_label = QtWidgets.QLabel(self.centralwidget)
        self.logo_label.setGeometry(QtCore.QRect(80, 156, 61, 51))
        self.logo_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.logo_label.setObjectName("logo_label")
        self.combobox_sel_operator = QtWidgets.QComboBox(self.centralwidget)
        self.combobox_sel_operator.setGeometry(QtCore.QRect(390, 241, 151, 24))
        self.combobox_sel_operator.setObjectName("combobox_sel_operator")
        self.combobox_sel_operator.addItem("")
        self.btn_add_operator = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_operator.setGeometry(QtCore.QRect(520, 240, 24, 26))
        self.btn_add_operator.setObjectName("btn_add_operator")
        self.just_box_1 = QtWidgets.QTextBrowser(self.centralwidget)
        self.just_box_1.setGeometry(QtCore.QRect(50, 60, 491, 71))
        self.just_box_1.setMouseTracking(False)
        self.just_box_1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.just_box_1.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        self.just_box_1.setObjectName("just_box_1")
        self.just_box_1.raise_()
        self.start_app.raise_()
        self.sens_type_label.raise_()
        self.sens_type_comboBox.raise_()
        self.open_settings_btn.raise_()
        self.app_label.raise_()
        self.status_opt_label.raise_()
        self.status_label.raise_()
        self.status_ref_label.raise_()
        self.null_detect_label.raise_()
        self.opt_channel_label.raise_()
        self.opt_config_combobox.raise_()
        self.status_gen_label.raise_()
        self.logo_label.raise_()
        self.combobox_sel_operator.raise_()
        self.btn_add_operator.raise_()
        Setup.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Setup)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 592, 21))
        self.menubar.setObjectName("menubar")
        Setup.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Setup)
        self.statusbar.setObjectName("statusbar")
        Setup.setStatusBar(self.statusbar)

        self.retranslateUi(Setup)
        QtCore.QMetaObject.connectSlotsByName(Setup)

    def retranslateUi(self, Setup):
        _translate = QtCore.QCoreApplication.translate
        Setup.setWindowTitle(_translate("Setup", "MainWindow"))
        self.start_app.setText(_translate("Setup", "START"))
        self.sens_type_label.setText(_translate("Setup", "Optical sensor type"))
        self.open_settings_btn.setText(_translate("Setup", "SETTINGS"))
        self.app_label.setText(_translate("Setup", "Appname"))
        self.status_opt_label.setText(_translate("Setup", "Optical device"))
        self.status_label.setText(_translate("Setup", "STATUS :"))
        self.status_ref_label.setText(_translate("Setup", "Reference device"))
        self.null_detect_label.setText(_translate("Setup", "Please setup \n"
"parameters!"))
        self.opt_channel_label.setText(_translate("Setup", "Select config"))
        self.status_gen_label.setText(_translate("Setup", "Function generator"))
        self.logo_label.setText(_translate("Setup", "LOGO"))
        self.combobox_sel_operator.setItemText(0, _translate("Setup", "Select operator"))
        self.btn_add_operator.setText(_translate("Setup", "+"))