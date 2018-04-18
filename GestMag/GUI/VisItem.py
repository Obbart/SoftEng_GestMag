# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'VisItem.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Item(object):
    def setupUi(self, Item):
        Item.setObjectName("Item")
        Item.resize(104, 46)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Item)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lbl_stat = QtWidgets.QLabel(Item)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_stat.sizePolicy().hasHeightForWidth())
        self.lbl_stat.setSizePolicy(sizePolicy)
        self.lbl_stat.setWordWrap(True)
        self.lbl_stat.setObjectName("lbl_stat")
        self.horizontalLayout.addWidget(self.lbl_stat)
        self.btn_prop = QtWidgets.QPushButton(Item)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_prop.sizePolicy().hasHeightForWidth())
        self.btn_prop.setSizePolicy(sizePolicy)
        self.btn_prop.setObjectName("btn_prop")
        self.horizontalLayout.addWidget(self.btn_prop)

        self.retranslateUi(Item)
        QtCore.QMetaObject.connectSlotsByName(Item)

    def retranslateUi(self, Item):
        _translate = QtCore.QCoreApplication.translate
        Item.setWindowTitle(_translate("Item", "Form"))
        self.lbl_stat.setText(_translate("Item", "Item"))
        self.btn_prop.setText(_translate("Item", "P"))

