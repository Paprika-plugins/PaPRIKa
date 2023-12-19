# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Paprika
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
import os, sys
BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, QThread
from PyQt5.QtWidgets import QAction,QMessageBox, QFileDialog, QDialog
from PyQt5.QtGui import QIcon, QColor

# Import the code for the DockWidget
from .A_propos import Ui_A_propos
from .paprika_dockwidget import Ui_PaprikaDockWidgetBase
from qgis.gui import *
from qgis.core import *
import webbrowser
import subprocess
from worker import WorkerCarteP, WorkerCarteR, WorkerCarteI, WorkerCarteKa, WorkerCarteFinale


class Paprika:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Paprika_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Paprika')
        self.toolbar = self.iface.addToolBar(u'Paprika')
        self.toolbar.setObjectName(u'Paprika')
        self.pluginIsActive = False
        self.dockwidget = None
        self.raster_info = {}
        self.extent_view = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Paprika', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(BASE_DIR, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr('Paprika Toolbox'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.dockwidget.mMapLayerComboBox_IMPLUVIUM.layerChanged.disconnect(self.update_raster_info)
        if self.extent_view is not None:
            self.iface.mapCanvas().scene().removeItem(self.extent_view)
            self.extent_view = None
        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if self.extent_view is not None:
            self.iface.mapCanvas().scene().removeItem(self.extent_view)
            self.extent_view = None
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&Paprika'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """Run method that loads and starts the plugin"""
        if not self.pluginIsActive:
            self.pluginIsActive = True

            if self.dockwidget is None:
                self.dockwidget = Ui_PaprikaDockWidgetBase()

            self.dockwidget.pushButton_Aide.clicked.connect(self.open_help)
            self.dockwidget.pushButton_methodo.clicked.connect(self.download_methodo)
            self.dockwidget.pushButton_lancerCarteP.clicked.connect(self.carte_p)
            self.dockwidget.pushButton_lancerCarteR.clicked.connect(self.carte_r)
            self.dockwidget.pushButton_lancerCarteI.clicked.connect(self.carte_i)
            self.dockwidget.pushButton_lancerCarteKa.clicked.connect(self.carte_ka)
            self.dockwidget.pushButton_lancerCarteFinale.clicked.connect(self.carte_finale)
            self.dockwidget.toolButton_dossier_travail.clicked.connect(self.open_directory)
            self.dockwidget.lineEdit_dossier_travail.setText(QSettings().value('Paprika_toolbox/current_directory', ''))
            self.dockwidget.pushButton_Apropos.clicked.connect(self.open_a_propos)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
            
            #filtrage et peuplement des ComboBox des layers
            self.dockwidget.mMapLayerComboBox_IMPLUVIUM.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_SOL.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_EPIKARST.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_ROCHE.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_STRUCTURE.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_KARST_FEATURES.setFilters(QgsMapLayerProxyModel.VectorLayer)
            self.dockwidget.mMapLayerComboBox_ZNS.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dockwidget.mMapLayerComboBox_PENTE.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dockwidget.mMapLayerComboBox_CartePF.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dockwidget.mMapLayerComboBox_CarteRF.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dockwidget.mMapLayerComboBox_CarteIF.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dockwidget.mMapLayerComboBox_CarteKaF.setFilters(QgsMapLayerProxyModel.RasterLayer)
            
            # peuplement de la comboBox du critere de Mangin
            self.dockwidget.comboBox_MANGIN.clear()
            self.dockwidget.comboBox_MANGIN.addItems(['1', '2', '3', '4'])
        
            # peuplement des ComboBox des champs et gestion des criteres optionnels
            self.dockwidget.mMapLayerComboBox_IMPLUVIUM.layerChanged.connect(self.update_raster_info)
            self.dockwidget.cb_show_extent.toggled.connect(self.on_show_extent)
                #SOL
            self.dockwidget.mFieldComboBox_SOL.setFilters(QgsFieldProxyModel.Numeric)
            self.dockwidget.mFieldComboBox_SOL.setLayer(self.dockwidget.mMapLayerComboBox_SOL.currentLayer())
            self.dockwidget.mMapLayerComboBox_SOL.layerChanged.connect(self.dockwidget.mFieldComboBox_SOL.setLayer)
                #EPIKARST
            self.dockwidget.mFieldComboBox_EPIKARST.setFilters(QgsFieldProxyModel.Numeric)
            self.dockwidget.mFieldComboBox_EPIKARST.setLayer(self.dockwidget.mMapLayerComboBox_EPIKARST.currentLayer())
            self.dockwidget.mMapLayerComboBox_EPIKARST.layerChanged.connect(self.dockwidget.mFieldComboBox_EPIKARST.setLayer)
                #SINKING STREAM CATCHMENT
            self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setFilters(QgsFieldProxyModel.Numeric)
            self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setLayer(self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.currentLayer())
            self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.layerChanged.connect(self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setLayer)
                #LITHOLOGY
            self.dockwidget.mFieldComboBox_ROCHE.setFilters(QgsFieldProxyModel.Numeric)
            self.dockwidget.mFieldComboBox_ROCHE.setLayer(self.dockwidget.mMapLayerComboBox_ROCHE.currentLayer())
            self.dockwidget.mMapLayerComboBox_ROCHE.layerChanged.connect(self.dockwidget.mFieldComboBox_ROCHE.setLayer)
                #KARST FEATURES I
            self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setFilters(QgsFieldProxyModel.Numeric)
            self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setLayer(self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.currentLayer())
            self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.layerChanged.connect(self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setLayer)
            # mise a jour du total de la ponderation (Final Map)
            self.dockwidget.spinBox_PondP.setValue(int(QSettings().value('Paprika_toolbox/pondP', 25)))
            self.dockwidget.spinBox_PondR.setValue(int(QSettings().value('Paprika_toolbox/pondR', 20)))
            self.dockwidget.spinBox_PondI.setValue(int(QSettings().value('Paprika_toolbox/pondI', 30)))
            self.dockwidget.spinBox_PondKa.setValue(int(QSettings().value('Paprika_toolbox/pondKa', 25)))
            self.dockwidget.spinBox_PondP.valueChanged.connect(self.calcul_somme_pond)
            self.dockwidget.spinBox_PondR.valueChanged.connect(self.calcul_somme_pond)
            self.dockwidget.spinBox_PondI.valueChanged.connect(self.calcul_somme_pond)
            self.dockwidget.spinBox_PondKa.valueChanged.connect(self.calcul_somme_pond)
            self.calcul_somme_pond()
            self.update_raster_info()

    def calcul_somme_pond(self):
        P = self.dockwidget.spinBox_PondP.value()
        R = self.dockwidget.spinBox_PondR.value()
        I = self.dockwidget.spinBox_PondI.value()
        Ka = self.dockwidget.spinBox_PondKa.value()
        new_value = P + R + I + Ka
        self.dockwidget.label_sum_ponderation.setText(str(new_value) + ' %')
        if new_value == 100:
            self.dockwidget.pushButton_lancerCarteFinale.setEnabled(True)
        else:
            self.dockwidget.pushButton_lancerCarteFinale.setEnabled(False)

    def open_directory(self):
        """choose a directory to save the generated files"""
        directory = QFileDialog.getExistingDirectory(self.dockwidget.toolButton_dossier_travail,
                                                     "Choose a directory to work with",
                                                     QgsProject.instance().fileName(),
                                                     QFileDialog.ShowDirsOnly)
        self.dockwidget.lineEdit_dossier_travail.setText(str(QtCore.QDir.toNativeSeparators(directory)))
        QSettings().setValue('Paprika_toolbox/current_directory', str(QtCore.QDir.toNativeSeparators(directory)))
    
    def update_raster_info(self):
        """Get raster extent and resolution from impluvium user choice and save it in the instance for use"""
        self.raster_info['resolution_x'] = self.dockwidget.spb_resolution.value()
        self.raster_info['resolution_y'] = self.dockwidget.spb_resolution.value()
        layer_impluvium = self.dockwidget.mMapLayerComboBox_IMPLUVIUM.currentLayer()
        if layer_impluvium and layer_impluvium.isValid():
            self.raster_info['projection_wkt'] = layer_impluvium.crs().toWkt()
            feature_impluvium = next(layer_impluvium.getFeatures())
            geom = feature_impluvium.geometry().buffer(1000, 5).boundingBox()
            Xmin = geom.xMinimum()
            Ymin = geom.yMinimum()
            Xmax = geom.xMaximum()
            Ymax = geom.yMaximum()
            self.raster_info['extent'] = {}
            self.raster_info['extent']['Xmin'] = Xmin
            self.raster_info['extent']['Ymin'] = Ymin
            self.raster_info['extent']['Xmax'] = Xmax
            self.raster_info['extent']['Ymax'] = Ymax
            self.raster_info['extent']['str_extent'] = ', '.join([str(Xmin), str(Xmax), str(Ymax), str(Ymin)])
            self.raster_info['size_x'] = int(abs(Xmax - Xmin)/self.raster_info['resolution_x'])
            self.raster_info['size_y'] = int(abs(Ymax - Ymin)/self.raster_info['resolution_y'])
            if self.dockwidget.cb_show_extent.isChecked():
                if self.extent_view is not None:
                    self.iface.mapCanvas().scene().removeItem(self.extent_view)
                    self.extent_view = QgsRubberBand(self.iface.mapCanvas())
                    self.extent_view.addGeometry(QgsGeometry.fromRect(QgsRectangle(Xmin, Ymin, Xmax, Ymax)))
                    self.extent_view.setColor(QColor('#A43C27'))
                else:
                    self.extent_view = QgsRubberBand(self.iface.mapCanvas())
                    self.extent_view.addGeometry(QgsGeometry.fromRect(QgsRectangle(Xmin, Ymin, Xmax, Ymax)))
                    self.extent_view.setColor(QColor('#A43C27'))

    def on_show_extent(self):
        if self.dockwidget.cb_show_extent.isChecked():
            if 'extent' in self.raster_info:
                corner = self.raster_info['extent']
                self.extent_view = QgsRubberBand(self.iface.mapCanvas())
                self.extent_view.addGeometry(QgsGeometry.fromRect(QgsRectangle(corner['Xmin'], corner['Ymin'], corner['Xmax'], corner['Ymax'])))
                self.extent_view.setColor(QColor('#A43C27'))
        else:
            if self.extent_view is not None:
                self.iface.mapCanvas().scene().removeItem(self.extent_view)
                self.extent_view = None

    def carte_p(self):
        """test les parametres et lance la generation de la carte P"""
        if self.dockwidget.mFieldComboBox_SOL.currentField() == u'':
            return self.showdialog('The index Field of Soil Protection Layer is not set...', 'Field issue...')
        # controle la validite des occurences du champ index
        value_sol = [feature.attribute(self.dockwidget.mFieldComboBox_SOL.currentField()) for feature in self.dockwidget.mMapLayerComboBox_SOL.currentLayer().getFeatures()]
        if min(value_sol) < 0 or max(value_sol) > 4 or len(value_sol) == 0 :
            return self.showdialog('The index Field of Soil Cover Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')

        if self.dockwidget.checkBox_Epikarst.isChecked():
            # controle que la comboBox du champ Epikarst est bien remplie
            if self.dockwidget.mFieldComboBox_EPIKARST.currentField() == u'':
                return self.showdialog('The index Field of Epikarst Layer is not set...', 'Field issue...')
            # controle la validite des occurences du champ index
            value_epikarst = [feature.attribute(self.dockwidget.mFieldComboBox_EPIKARST.currentField()) for feature in self.dockwidget.mMapLayerComboBox_EPIKARST.currentLayer().getFeatures()]
            if min(value_epikarst) < 0 or max(value_epikarst) > 4 or len(value_epikarst) == 0 :
                return self.showdialog('The index Field of Epikarst Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')

        if self.dockwidget.checkBox_Sinking.isChecked():
            # controle que la comboBox du champ Sinking Stream Catchment est bien remplie
            if self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.currentField() == u'':
                return self.showdialog('The index Field of Sinking Stream Catchment Layer is not set...', 'Field issue...')
            # controle la validite des occurences des champs index
            value_sinking = [feature.attribute(self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.currentField()) for feature in self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.currentLayer().getFeatures()]
            if min(value_sinking) < 0 or max(value_sinking) > 4 or len(value_sinking) == 0 :
                return self.showdialog('The index''s field of Sinking catchment Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')
                
        sol = self.dockwidget.mMapLayerComboBox_SOL.currentLayer()
        field_sol = self.dockwidget.mFieldComboBox_SOL.currentField()
            #EPIKARST
        if self.dockwidget.checkBox_Epikarst.isChecked():
            epikarst = self.dockwidget.mMapLayerComboBox_EPIKARST.currentLayer()
            field_epikarst = self.dockwidget.mFieldComboBox_EPIKARST.currentField()
        else :
            epikarst = None
            field_epikarst = None
            
            #SINKING CATCHMENT
        if self.dockwidget.checkBox_Sinking.isChecked():
            sinking = self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.currentLayer()
            field_sinking = self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.currentField()
        else : 
            sinking = None
            field_sinking = None
        #lance la generation de la carte P
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == "P factor": 
                QgsProject.instance().removeMapLayers( [lyr.id()])

        self.carte_p_worker = WorkerCarteP(self.raster_info,
                            self.dockwidget.lineEdit_dossier_travail.text(),
                            self.dockwidget.mMapLayerComboBox_ZNS.currentLayer(),
                            sol,
                            field_sol,
                            epikarst,
                            field_epikarst,
                            sinking,
                            field_sinking)
        self.carte_p_thread = QThread()
        self.carte_p_worker.results.connect(self.on_carte_p_results)
        self.carte_p_worker.progress.connect(self.on_progress)
        self.carte_p_worker.error.connect(self.on_error)
        self.carte_p_worker.finished.connect(self.on_carte_p_finished)

        self.carte_p_worker.moveToThread(self.carte_p_thread)
        self.carte_p_thread.started.connect(self.carte_p_worker.run)
        self.carte_p_thread.start()

    def on_carte_p_results(self):
        #genere le style et charge le tif dans QGIS avec un message
        lay_carteP = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/P_factor.tif','P factor')
        self.set_raster_style(lay_carteP)
        QgsProject.instance().addMapLayer(lay_carteP)
        self.showdialog('P factor map created wih success!', 'Well done!')

    def on_carte_p_finished(self):
        self.carte_p_thread.quit()
        self.carte_p_thread.wait()
        self.carte_p_worker = None
        self.carte_p_thread = None

    def carte_r(self):
        """teste les parametres et lance la generation de la carte R"""
        if self.dockwidget.mFieldComboBox_ROCHE.currentField() == u'':
                return self.showdialog('The index Field of Lithology Layer is not set...', 'Field issue...')
        value_lithology = [feature.attribute(self.dockwidget.mFieldComboBox_ROCHE.currentField()) for feature in self.dockwidget.mMapLayerComboBox_ROCHE.currentLayer().getFeatures()]
        if min(value_lithology) < 0 or max(value_lithology) > 4 or len(value_lithology) == 0 :
            return self.showdialog('The index Field of Lithology Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')

        lithology = self.dockwidget.mMapLayerComboBox_ROCHE.currentLayer()
        field_lithology = self.dockwidget.mFieldComboBox_ROCHE.currentField()
        if self.dockwidget.checkBox_STRUCTURE.isChecked():
            structure = self.dockwidget.mMapLayerComboBox_STRUCTURE.currentLayer()
        else:
            structure = None

        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == "R factor": 
                QgsProject.instance().removeMapLayers( [lyr.id()] )

        self.carte_r_worker = WorkerCarteR(self.dockwidget.lineEdit_dossier_travail.text(),
                                           self.raster_info,
                                           lithology,
                                           field_lithology,
                                           structure)
        self.carte_r_thread = QThread()
        self.carte_r_worker.results.connect(self.on_carte_r_results)
        self.carte_r_worker.progress.connect(self.on_progress)
        self.carte_r_worker.error.connect(self.on_error)
        self.carte_r_worker.finished.connect(self.on_carte_r_finished)

        self.carte_r_worker.moveToThread(self.carte_r_thread)
        self.carte_r_thread.started.connect(self.carte_r_worker.run)
        self.carte_r_thread.start()

    def on_carte_r_results(self):
        lay_carteR = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text()) + '/R_factor.tif',
                                    'R factor')
        self.set_raster_style(lay_carteR)
        QgsProject.instance().addMapLayer(lay_carteR)
        self.showdialog('R factor map created wih success!', 'Well done!')

    def on_carte_r_finished(self):
        self.carte_r_thread.quit()
        self.carte_r_thread.wait()
        self.carte_r_worker = None
        self.carte_r_thread = None
  
    def carte_i(self):
        """teste les parametres et lance la generation de la carte I"""
        if self.dockwidget.checkBox_OBJETS_EXOKARSTIQUES.isChecked():
            if self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.currentField() == '':
                return self.showdialog('The index Field of Karst features Layer is not set...', 'Field issue...')

            value_objets_exokarstiques = [feature.attribute(self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.currentField()) for feature in self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.currentLayer().getFeatures()]
            if min(value_objets_exokarstiques) < 0 or max(value_objets_exokarstiques) > 4 :
                return self.showdialog('The index Field of Karst features Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')

        rules = self.generate_reclass_rules_slope(self.dockwidget.spinBox_first_threshold.value(),self.dockwidget.spinBox_second_threshold.value(),self.dockwidget.spinBox_third_threshold.value())
        pente = self.dockwidget.mMapLayerComboBox_PENTE.currentLayer()

        if self.dockwidget.checkBox_OBJETS_EXOKARSTIQUES.isChecked():
            exokarst = self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.currentLayer()
            field_exokarst = self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.currentField()
        else:
            exokarst = None
            field_exokarst = None

        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == "I Factor": 
                QgsProject.instance().removeMapLayers( [lyr.id()] )

        self.carte_i_worker = WorkerCarteI(self.dockwidget.lineEdit_dossier_travail.text(),
                                self.raster_info,
                                pente,
                                rules,
                                exokarst,
                                field_exokarst)
        self.carte_i_thread = QThread()
        self.carte_i_worker.results.connect(self.on_carte_i_results)
        self.carte_i_worker.progress.connect(self.on_progress)
        self.carte_i_worker.error.connect(self.on_error)
        self.carte_i_worker.finished.connect(self.on_carte_i_finished)

        self.carte_i_worker.moveToThread(self.carte_i_thread)
        self.carte_i_thread.started.connect(self.carte_i_worker.run)
        self.carte_i_thread.start()

    def on_carte_i_results(self):
        lay_carteI = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/I_factor.tif', 'I factor')

        self.set_raster_style(lay_carteI)
        QgsProject.instance().addMapLayer(lay_carteI)
        self.showdialog('I factor map created wih success!', 'Well done!')

    def on_carte_i_finished(self):
        self.carte_i_thread.quit()
        self.carte_i_thread.wait()
        self.carte_i_worker = None
        self.carte_i_thread = None

    def carte_ka(self):
        """teste les parametres et lance la generation de la carte Ka"""
        if self.dockwidget.checkBox_KARST_FEATURES.isChecked():
            karst_features = self.dockwidget.mMapLayerComboBox_KARST_FEATURES.currentLayer()
            
        else:
            karst_features = None
                
        #genere le tif
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == "Ka factor": 
                QgsProject.instance().removeMapLayers([lyr.id()])

        self.carte_ka_worker = WorkerCarteKa(self.dockwidget.lineEdit_dossier_travail.text(),
                                self.raster_info,
                                int(self.dockwidget.comboBox_MANGIN.currentText()),
                                karst_features)

        self.carte_ka_thread = QThread()
        self.carte_ka_worker.results.connect(self.on_carte_ka_results)
        self.carte_ka_worker.progress.connect(self.on_progress)
        self.carte_ka_worker.error.connect(self.on_error)
        self.carte_ka_worker.finished.connect(self.on_carte_ka_finished)

        self.carte_ka_worker.moveToThread(self.carte_ka_thread)
        self.carte_ka_thread.started.connect(self.carte_ka_worker.run)
        self.carte_ka_thread.start()

    def on_carte_ka_results(self):
        lay_carteKa = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/Ka_factor.tif','Ka factor')
        self.set_raster_style(lay_carteKa)
        QgsProject.instance().addMapLayer(lay_carteKa)
        self.showdialog('Ka factor map created wih success!', 'Well done!')

    def on_carte_ka_finished(self):
        self.carte_ka_thread.quit()
        self.carte_ka_thread.wait()
        self.carte_ka_worker = None
        self.carte_ka_thread = None
    
    def carte_finale(self):
        pP=self.dockwidget.spinBox_PondP.value()
        pR=self.dockwidget.spinBox_PondR.value()
        pI=self.dockwidget.spinBox_PondI.value()
        pKa=self.dockwidget.spinBox_PondKa.value()
        QSettings().setValue('Paprika_toolbox/pondP', pP)
        QSettings().setValue('Paprika_toolbox/pondR', pR)
        QSettings().setValue('Paprika_toolbox/pondI', pI)
        QSettings().setValue('Paprika_toolbox/pondKa', pKa)

        if pI + pKa + pP + pR != 100:
            return self.showdialog('weight sum must be egal at 100%!', 'invalid weight...')
            
        #supprime la couche si elle est deja chargee et genere le tif
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.name() == "Vulnerability Map": 
                QgsProject.instance().removeMapLayers( [lyr.id()] )

        self.carte_finale_worker = WorkerCarteFinale(self.dockwidget.lineEdit_dossier_travail.text(),
                                        self.raster_info,
                                        self.dockwidget.spinBox_PondP.value(),
                                        self.dockwidget.spinBox_PondR.value(),
                                        self.dockwidget.spinBox_PondI.value(),
                                        self.dockwidget.spinBox_PondKa.value(),
                                        self.dockwidget.mMapLayerComboBox_CartePF.currentLayer(),
                                        self.dockwidget.mMapLayerComboBox_CarteRF.currentLayer(),
                                        self.dockwidget.mMapLayerComboBox_CarteIF.currentLayer(),
                                        self.dockwidget.mMapLayerComboBox_CarteKaF.currentLayer())

        self.carte_finale_thread = QThread()
        self.carte_finale_worker.results.connect(self.on_carte_finale_results)
        self.carte_finale_worker.progress.connect(self.on_progress)
        self.carte_finale_worker.error.connect(self.on_error)
        self.carte_finale_worker.finished.connect(self.on_carte_finale_finished)

        self.carte_finale_worker.moveToThread(self.carte_finale_thread)
        self.carte_finale_thread.started.connect(self.carte_finale_worker.run)
        self.carte_finale_thread.start()

    def on_carte_finale_results(self):
        lay_carteFinale = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/Vulnerability_Map.tif','Vulnerability Map')
        self.set_raster_style(lay_carteFinale)
        QgsProject.instance().addMapLayer(lay_carteFinale)
        return self.showdialog('Final map created wih success!', 'Well done!')

    def on_carte_finale_finished(self):
        self.carte_finale_thread.quit()
        self.carte_finale_thread.wait()

    def on_error(self, e):
        """If something wrong happen in the thread, show what..."""
        self.showdialog(str(e), 'Oups!')

    def on_progress(self, value, tot):
        """Update the progress bar from thread"""
        self.dockwidget.progress.setMaximum(100)
        self.dockwidget.progress.setValue((value*100/tot) + 1)
    
    def showdialog (self, text, title):
        """Just a wrapper to show message popup to user"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def set_raster_style(self, raster_layer):
        """Set the style for output"""
        s = QgsRasterShader()
        c = QgsColorRampShader()
        c.setColorRampType(QgsColorRampShader.Exact)
        i = []
        i.append(QgsColorRampShader.ColorRampItem(0, QColor('#FFFFFF'), '0'))
        i.append(QgsColorRampShader.ColorRampItem(1, QColor('#0040FF'), '1'))
        i.append(QgsColorRampShader.ColorRampItem(2, QColor('#A8D990'), '2'))
        i.append(QgsColorRampShader.ColorRampItem(3, QColor('#F6F085'), '3'))
        i.append(QgsColorRampShader.ColorRampItem(4, QColor('#E6A55B'), '4'))
        i.append(QgsColorRampShader.ColorRampItem(5, QColor('#A43C27'), '5'))
        c.setColorRampItemList(i)
        s.setRasterShaderFunction(c)
        ps = QgsSingleBandPseudoColorRenderer(raster_layer.dataProvider(), 1, s)
        raster_layer.setRenderer(ps)
    
    def open_a_propos(self):
        """Open About dialog"""
        a_propos = Ui_A_propos()
        a_propos.exec()
    
    def download_methodo(self):
        """Open webbrowser on official methodology page"""
        webbrowser.open_new('http://infoterre.brgm.fr/rapports/RP-57527-FR.pdf')
        webbrowser.open_new_tab('http://link.springer.com/article/10.1007/s10040-010-0688-8')
    
    def open_help(self):
        """Open pdf docs. Platform dependent"""
        if os.name == 'nt':
            os.startfile(os.path.dirname(os.path.abspath(__file__))+'/doc/Paprika_Toolbox_User_guide.pdf')
        elif os.name == 'posix':
            subprocess.call(["xdg-open", os.path.dirname(os.path.abspath(__file__))+'/doc/Paprika_Toolbox_User_guide.pdf'])
    
    def generate_reclass_rules_slope(self,first,second,third):
        """Generate the list that contains rules for slope reclassify"""
        return [-1, first, 4, first, second, 3, second, third, 2, third, 99999999, 1]
