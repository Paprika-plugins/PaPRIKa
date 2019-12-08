# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'A_propos.ui'
#
# Created: Thu Jun 08 12:01:48 2017
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

import os

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

BASE_DIR = os.path.dirname(__file__)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    BASE_DIR, 'A_propos.ui'))

class Ui_A_propos(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(Ui_A_propos, self).__init__(parent)
        self.setupUi(self)
