# -*- coding: utf-8 -*-
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
        self.add_image()

    def add_image(self):
        self.lbl_img_EMMAH.setPixmap(QPixmap(os.path.join(BASE_DIR, 'resources', 'emmah.gif')).scaledToWidth(100))
        self.lbl_img_SNO.setPixmap(QPixmap(os.path.join(BASE_DIR, 'resources', 'LogoSNOKarst.PNG')).scaledToWidth(100))
        self.lbl_img_PACA.setPixmap(QPixmap(os.path.join(BASE_DIR, 'resources', 'logo_PACA.jpg')).scaledToWidth(100))
        self.lbl_img_SMBS.setPixmap(QPixmap(os.path.join(BASE_DIR, 'resources', 'logo_SMBS.jpg')).scaledToWidth(100))
        self.lbl_img_CARTYL.setPixmap(QPixmap(os.path.join(BASE_DIR, 'resources', 'logo_light.png')).scaledToWidth(300))
