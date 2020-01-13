# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PaprikaDockWidget
                                 A QGIS plugin
 perform the Paprika Method with QGIS
                             -------------------
        begin                : 2017-01-09
        git sha              : $Format:%H$
        copyright            : (C) 2017 by SIG
        email                : ylecomte@sig.eu.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'paprika_dockwidget_base.ui'))


class Ui_PaprikaDockWidgetBase(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(Ui_PaprikaDockWidgetBase, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.connectUi()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def connectUi(self):
        self.checkBox_Sinking.stateChanged.connect(self.desactive_widget_Sinking)
        self.checkBox_STRUCTURE.stateChanged.connect(self.desactive_widget_structure)
        self.checkBox_OBJETS_EXOKARSTIQUES.stateChanged.connect(self.desactive_widget_objets_exokarstiques)
        self.checkBox_KARST_FEATURES.stateChanged.connect(self.desactive_widget_karst_features)
        self.checkBox_Epikarst.stateChanged.connect(self.desactive_widget_Epikarst)

    def desactive_widget_Epikarst(self):
        if self.checkBox_Epikarst.isChecked():
            self.mMapLayerComboBox_EPIKARST.setEnabled(True)
            self.mFieldComboBox_EPIKARST.setEnabled(True)
            self.label_EPIKARST.setStyleSheet('color: black')
            self.label_index_EPIKARST.setStyleSheet('color: black')
        else:
            self.mMapLayerComboBox_EPIKARST.setDisabled(True)
            self.mFieldComboBox_EPIKARST.setDisabled(True)
            self.label_EPIKARST.setStyleSheet('color: grey')
            self.label_index_EPIKARST.setStyleSheet('color: grey')

    def desactive_widget_Sinking(self):
        if self.checkBox_Sinking.isChecked():
            self.mMapLayerComboBox_SINKING_CATCHMENT.setEnabled(True)
            self.mFieldComboBox_SINKING_CATCHMENT.setEnabled(True)
            self.label_SINKING.setStyleSheet('color: black')
            self.label_index_SINKING.setStyleSheet('color: black')
        else:
            self.mMapLayerComboBox_SINKING_CATCHMENT.setDisabled(True)
            self.mFieldComboBox_SINKING_CATCHMENT.setDisabled(True)
            self.label_SINKING.setStyleSheet('color: grey')
            self.label_index_SINKING.setStyleSheet('color: grey')

    def desactive_widget_structure(self):
        if self.checkBox_STRUCTURE.isChecked():
            self.mMapLayerComboBox_STRUCTURE.setEnabled(True)
            self.label_STRUCTURE.setStyleSheet('color: black')
        else:
            self.mMapLayerComboBox_STRUCTURE.setDisabled(True)
            self.label_STRUCTURE.setStyleSheet('color: grey')

    def desactive_widget_objets_exokarstiques(self):
        if self.checkBox_OBJETS_EXOKARSTIQUES.isChecked():
            self.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.setEnabled(True)
            self.mFieldComboBox_OBJETS_EXOKARSTIQUES.setEnabled(True)
            self.label_OBJETS_EXOKARSTIQUES.setStyleSheet('color: black')
            self.label_index_OBJETS_EXOKARSTIQUES.setStyleSheet('color: black')
            self.label_text_I.setStyleSheet('color: black')
        else:
            self.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.setDisabled(True)
            self.mFieldComboBox_OBJETS_EXOKARSTIQUES.setDisabled(True)
            self.label_OBJETS_EXOKARSTIQUES.setStyleSheet('color: grey')
            self.label_index_OBJETS_EXOKARSTIQUES.setStyleSheet('color: grey')
            self.label_text_I.setStyleSheet('color: grey')

    def desactive_widget_karst_features(self):
        if self.checkBox_KARST_FEATURES.isChecked():
            self.mMapLayerComboBox_KARST_FEATURES.setEnabled(True)
            self.label_KARST_FEATURES.setStyleSheet('color: black')
        else:
            self.mMapLayerComboBox_KARST_FEATURES.setDisabled(True)
            self.label_KARST_FEATURES.setStyleSheet('color: grey')
