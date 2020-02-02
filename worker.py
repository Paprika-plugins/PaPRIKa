# -*- coding: utf-8 -*-
import os
import numpy
import gdal
import processing
from qgis.core import QgsRasterLayer, QgsPointXY, QgsField
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from PyQt5.QtCore import QObject, pyqtSignal, QVariant

class WorkerCarteP(QObject):

    results = pyqtSignal()
    error = pyqtSignal(Exception)
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)

    def __init__(self, raster_info, doss,
                  layer_zns,
                  layer_sol, field_sol,
                  layer_epikarst, field_epikarst,
                  layer_sinking, field_sinking):
        super().__init__()
        self.raster_info = raster_info
        self.doss = doss
        self.layer_zns = layer_zns
        self.layer_sol = layer_sol
        self.field_sol = field_sol
        self.layer_epikarst = layer_epikarst
        self.field_epikarst = field_epikarst
        self.layer_sinking = layer_sinking
        self.field_sinking = field_sinking

    def run(self):
        try:
            processing.run("gdal:rasterize", {'INPUT': self.layer_sol,
                                              'FIELD': self.field_sol,
                                              'HEIGHT': self.raster_info['resolution_y'],
                                              'WIDTH': self.raster_info['resolution_x'],
                                              'UNITS': 1,
                                              'EXTENT': self.raster_info['extent']['str_extent'],
                                              'OUTPUT': os.path.join(self.doss, 'rSol.tif')})
            processing.run("grass7:r.resample", {'input': self.layer_zns,
                                                 'GRASS_REGION_PARAMETER': self.raster_info['extent']['str_extent'],
                                                 'GRASS_REGION_CELLSIZE_PARAMETER': self.raster_info['resolution_x'],
                                                 'output': os.path.join(self.doss, 'rZNS.tif')})

            if self.layer_epikarst is None:
                pass
            else:
                processing.run("gdal:rasterize", {'INPUT': self.layer_epikarst,
                                                  'FIELD': self.field_epikarst,
                                                  'HEIGHT': self.raster_info['resolution_y'],
                                                  'WIDTH': self.raster_info['resolution_x'],
                                                  'UNITS': 1,
                                                  'EXTENT': self.raster_info['extent']['str_extent'],
                                                  'OUTPUT': os.path.join(self.doss, 'rEpikarst.tif')})

            if self.layer_sinking is None:
                pass
            else:
                processing.run("gdal:rasterize", {'INPUT': self.layer_sinking,
                                                  'FIELD': self.field_sinking,
                                                  'HEIGHT': self.raster_info['resolution_y'],
                                                  'WIDTH': self.raster_info['resolution_x'],
                                                  'UNITS': 1,
                                                  'EXTENT': self.raster_info['extent']['str_extent'],
                                                  'OUTPUT': os.path.join(self.doss, 'rSinking.tif')})

            # Preparation des donnees pour la comparaison des valeurs des rasters sur chaque pixel
            val_i = range(0, self.raster_info['size_x'], 1)
            val_j = range(0, self.raster_info['size_y'], 1)
            if self.layer_epikarst is None:
                pass
            else:
                rEpikarst = QgsRasterLayer(os.path.join(self.doss, 'rEpikarst.tif'), 'rEpikarst')
                pEpikarst = rEpikarst.dataProvider()
            if self.layer_sinking is None:
                pass
            else:
                rSinking = QgsRasterLayer(os.path.join(self.doss, 'rSinking.tif'), 'rSinking')
                pSinking = rSinking.dataProvider()
            rZNS = QgsRasterLayer(os.path.join(self.doss, 'rZNS.tif'), 'rZNS')
            pZNS = rZNS.dataProvider()
            rSol = QgsRasterLayer(os.path.join(self.doss, 'rSol.tif'), 'rSol')
            pSol = rSol.dataProvider()

            # iteration sur les pixels: selection de la valeur la plus faible et ecriture dans l'array
            ValCarteP = numpy.zeros((self.raster_info['size_y'], self.raster_info['size_x']), numpy.int16)
            for j in val_j:
                self.progress.emit(j, len(val_j))
                for i in val_i:
                    valeur = []
                    pos = QgsPointXY(
                        (self.raster_info['extent']['Xmin'] + (i + 1) * self.raster_info['resolution_x']) - self.raster_info[
                            'resolution_x'] / 2,
                        (self.raster_info['extent']['Ymax'] - j * self.raster_info['resolution_y']) - self.raster_info[
                            'resolution_y'] / 2)
                    if self.layer_sol is None:
                        valSol = 6
                    else:
                        valSol, found = pSol.sample(pos, 1)
                        if not found or valSol == 0:
                            valSol = 6
                    if self.layer_zns is None:
                        valZNS = 6
                    else:
                        valZNS, found = pZNS.sample(pos, 1)
                        if not found or valZNS == 0:
                            valZNS = 6
                    if self.layer_epikarst is None:
                        valEpikarst = 6
                    else:
                        valEpikarst, found = pEpikarst.sample(pos, 1)
                        if not found or valEpikarst == 0:
                            valEpikarst = 6
                    if self.layer_sinking is None:
                        valSinking = 6
                    else:
                        valSinking, found = pSinking.sample(pos, 1)
                        if not found or valSinking == 0:
                            valSinking = 6
                    valeur.append(valSol)
                    valeur.append(valZNS)
                    valeur.append(valEpikarst)
                    valeur.append(valSinking)
                    ValCarteP[j, i] = min(valeur)

            # ecriture du raster a partir de l'array
            raster = gdal.GetDriverByName('Gtiff').Create(os.path.join(self.doss, 'P_factor.tif'),
                                                          self.raster_info['size_x'], self.raster_info['size_y'],
                                                          1, gdal.GDT_Byte)
            # proj = osr.SpatialReference()
            # proj.ImportFromWkt(raster_info['projection_wkt'])
            raster.SetProjection(self.raster_info['projection_wkt'])
            raster.SetGeoTransform((self.raster_info['extent']['Xmin'],
                                    float(self.raster_info['resolution_x']),
                                    0.0,
                                    self.raster_info['extent']['Ymax'],
                                    0.0,
                                    float(-self.raster_info['resolution_y']),
                                    ))
            Band = raster.GetRasterBand(1)
            Band.WriteArray(ValCarteP, 0, 0)
            Band.FlushCache()
            Band.SetNoDataValue(6)

            # fermeture des connexions
            rSol = None
            rSinking = None
            rZNS = None
            rEpikarst = None
            raster = None
            self.results.emit()
        except Exception as e:
            self.error.emit(Exception('An error happen when generating the P Factor: %s' % str(e)))
        finally:
            self.finished.emit()


class WorkerCarteR(QObject):

    results = pyqtSignal()
    error = pyqtSignal(Exception)
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)

    def __init__(self, doss, raster_info, layer_lithology, field_lithology, layer_structure):
        super().__init__()
        self.raster_info = raster_info
        self.doss = doss
        self.layer_lithology = layer_lithology
        self.field_lithology = field_lithology
        self.layer_structure = layer_structure

    def run(self):
        try:
            processing.run("gdal:rasterize", {'INPUT': self.layer_lithology,
                                              'FIELD': self.field_lithology,
                                              'HEIGHT': self.raster_info['resolution_y'],
                                              'WIDTH': self.raster_info['resolution_x'],
                                              'UNITS': 1,
                                              'EXTENT': self.raster_info['extent']['str_extent'],
                                              'OUTPUT': os.path.join(self.doss, 'rLithology.tif')})

            if self.layer_structure is None:
                pass
            else:
                self.layer_structure.startEditing()
                self.layer_structure.dataProvider().addAttributes([QgsField('temp', QVariant.Int)])
                self.layer_structure.commitChanges()
                self.layer_structure.startEditing()
                field_structure = self.layer_structure.fields().indexFromName('temp')
                for feat in self.layer_structure.getFeatures():
                    self.layer_structure.changeAttributeValue(feat.id(), field_structure, 4)
                self.layer_structure.commitChanges()
                processing.run("gdal:rasterize", {'INPUT': self.layer_structure,
                                                  'FIELD': 'temp',
                                                  'HEIGHT': self.raster_info['resolution_y'],
                                                  'WIDTH': self.raster_info['resolution_x'],
                                                  'UNITS': 1,
                                                  'EXTENT': self.raster_info['extent']['str_extent'],
                                                  'OUTPUT': os.path.join(self.doss, 'rStructure.tif')})
                self.layer_structure.startEditing()
                self.layer_structure.dataProvider().deleteAttributes([field_structure])
                self.layer_structure.updateFields()
                self.layer_structure.commitChanges()

            # Preparation des donnees pour la comparaison des valeurs des rasters sur chaque pixel
            val_i = range(0, self.raster_info['size_x'], 1)
            val_j = range(0, self.raster_info['size_y'], 1)

            if self.layer_lithology is None:
                pass
            else:
                rLithology = QgsRasterLayer(os.path.join(self.doss, 'rLithology.tif'), 'rLithology')
                pLithology = rLithology.dataProvider()
            if self.layer_structure is None:
                pStructure = None
            else:
                rStructure = QgsRasterLayer(os.path.join(self.doss, 'rStructure.tif'), 'rStructure')
                pStructure = rStructure.dataProvider()

            # iteration sur les pixels
            ValCarteR = numpy.zeros((self.raster_info['size_y'], self.raster_info['size_x']), numpy.int16)
            for j in val_j:
                self.progress.emit(j, len(val_j))
                for i in val_i:
                    pos = QgsPointXY(
                        (self.raster_info['extent']['Xmin'] + (i + 1) * self.raster_info['resolution_x']) - self.raster_info[
                            'resolution_x'] / 2,
                        (self.raster_info['extent']['Ymax'] - j * self.raster_info['resolution_y']) - self.raster_info[
                            'resolution_y'] / 2)
                    if self.layer_lithology is None:
                        valLithology = 6
                    else:
                        valLithology, found = pLithology.sample(pos, 1)
                        if not found or valLithology == 0:
                            valLithology = 6
                    if self.layer_structure is None:
                        valStructure = 0
                    else:
                        valStructure, found = pStructure.sample(pos, 1)
                        if not found or valStructure == 0:
                            valStructure = 0
                        else:
                            valStructure = 4

                    ValCarteR[j, i] = valLithology + valStructure if valLithology + valStructure <= 4 else 4

            # ecriture du raster a partir de l'array
            raster = gdal.GetDriverByName('Gtiff').Create(os.path.join(self.doss, 'R_factor.tif'),
                                                          self.raster_info['size_x'], self.raster_info['size_y'],
                                                          1, gdal.GDT_Byte)

            raster.SetProjection(self.raster_info['projection_wkt'])
            raster.SetGeoTransform((self.raster_info['extent']['Xmin'],
                                    float(self.raster_info['resolution_x']),
                                    0.0,
                                    self.raster_info['extent']['Ymax'],
                                    0.0,
                                    float(-self.raster_info['resolution_y']),
                                    ))
            Band = raster.GetRasterBand(1)
            Band.WriteArray(ValCarteR, 0, 0)
            Band.FlushCache()
            Band.SetNoDataValue(6)

            # fermeture des connexions
            rLithology = None
            rStructure = None
            Raster = None
            self.results.emit()
        except Exception as e:
            self.error.emit(Exception('An error happen when generating the R Factor: %s' % str(e)))
        finally:
            self.finished.emit()

class WorkerCarteI(QObject):

    results = pyqtSignal()
    error = pyqtSignal(Exception)
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)

    def __init__(self, doss, raster_info, dem, reclass_rules_pente, layer_karst_features, field_karst_features):
        super().__init__()
        self.raster_info = raster_info
        self.doss = doss
        self.dem = dem
        self.reclass_rules_pente = reclass_rules_pente
        self.layer_karst_features = layer_karst_features
        self.field_karst_features = field_karst_features

    def run(self):
        try:
            processing.run("gdal:slope", {'INPUT': self.dem,
                                             'BAND': 1,
                                             'SCALE': 1,
                                             'AS_PERCENT': True,
                                             'COMPUTE_EDGES': False,
                                             'ZEVENBERGEN': False,
                                             'OPTIONS': '',
                                             'OUTPUT': os.path.join(self.doss, 'rRawSlope.tif')})

            rRawSlope = QgsRasterLayer(os.path.join(self.doss, 'rRawSlope.tif'), 'rRawSlope')

            # creation du raster Exokarst si besoin
            if self.field_karst_features is None:
                rKarstFeatures = None
            else:
                processing.run("gdal:rasterize", {'INPUT': self.layer_karst_features,
                                                  'FIELD': self.field_karst_features,
                                                  'HEIGHT': self.raster_info['resolution_y'],
                                                  'WIDTH': self.raster_info['resolution_x'],
                                                  'UNITS': 1,
                                                  'EXTENT': self.raster_info['extent']['str_extent'],
                                                  'OUTPUT': os.path.join(self.doss, 'rKarstFeatures.tif')})

                rKarstFeatures = QgsRasterLayer(os.path.join(self.doss, 'rKarstFeatures.tif'), 'rKarstFeatures')

            processing.run("native:reclassifybytable", {'INPUT_RASTER': rRawSlope,
                                                        'RASTER_BAND': 1,
                                                        'TABLE': self.reclass_rules_pente,
                                                        'NO_DATA': -9999,
                                                        'RANGE_BOUNDARIES': 0,
                                                        'NODATA_FOR_MISSING': False,
                                                        'DATA_TYPE':5,
                                                        'OUTPUT': os.path.join(self.doss, 'rSlope.tif')})

            rSlope = QgsRasterLayer(os.path.join(self.doss, 'rSlope.tif'), 'rSlope')

            # preparation des variables pour le croisement
            val_i = range(0, self.raster_info['size_x'], 1)
            val_j = range(0, self.raster_info['size_y'], 1)

            pSlope = rSlope.dataProvider()
            if rKarstFeatures is None:
                pKarstFeatures = None
            else:
                rKarstFeatures = QgsRasterLayer(os.path.join(self.doss, 'rKarstFeatures.tif'), 'rKarstFeatures')
                pKarstFeatures = rKarstFeatures.dataProvider()
            ValCarteI = numpy.zeros((self.raster_info['size_y'], self.raster_info['size_x']), numpy.int16)
            # iteration sur les pixels: selection de la valeur la plus faible et ecriture dans l'array
            for j in val_j:
                self.progress.emit(j, len(val_j))
                for i in val_i:
                    pos = QgsPointXY(
                        (self.raster_info['extent']['Xmin'] + (i + 1) * self.raster_info['resolution_x']) - self.raster_info[
                            'resolution_x'] / 2,
                        (self.raster_info['extent']['Ymax'] - j * self.raster_info['resolution_y']) - self.raster_info[
                            'resolution_y'] / 2)
                    valSlope, found = pSlope.sample(pos, 1)
                    if not found:
                        valSlope = 6
                    if pKarstFeatures is None:
                        valKarstFeatures = 0
                    else:
                        valKarstFeatures, found = pKarstFeatures.sample(pos, 1)
                        if not found:
                            valSlope = 6

                    ValCarteI[j, i] = max([valSlope, valKarstFeatures]) if (valSlope, valKarstFeatures) != (None, None) else 0

            # ecriture du raster a partir de l'array
            raster = gdal.GetDriverByName('Gtiff').Create(str(self.doss) + '/I_factor.tif', self.raster_info['size_x'],
                                                          self.raster_info['size_y'], 1, gdal.GDT_Byte)

            raster.SetProjection(self.raster_info['projection_wkt'])
            raster.SetGeoTransform((self.raster_info['extent']['Xmin'],
                                    float(self.raster_info['resolution_x']),
                                    0.0,
                                    self.raster_info['extent']['Ymax'],
                                    0.0,
                                    float(-self.raster_info['resolution_y']),
                                    ))
            Band = raster.GetRasterBand(1)
            Band.WriteArray(ValCarteI, 0, 0)
            Band.FlushCache()
            Band.SetNoDataValue(6)

            # fermeture des connexions
            rKarstFeatures = None
            rSlope = None
            Raster = None
            self.results.emit()
        except Exception as e:
            self.error.emit(Exception('An error happen when generating the I Factor: %s' % str(e)))
        finally:
            self.finished.emit()


class WorkerCarteKa(QObject):

    results = pyqtSignal()
    error = pyqtSignal(Exception)
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)

    def __init__(self, doss, raster_info, mangin, karst_features):
        super().__init__()
        self.raster_info = raster_info
        self.doss = doss
        self.mangin = mangin
        self.karst_features = karst_features

    def run(self):
        try:
            if self.karst_features is not None:
                self.karst_features.startEditing()
                self.karst_features.dataProvider().addAttributes([QgsField('temp', QVariant.Int)])
                self.karst_features.commitChanges()
                self.karst_features.startEditing()
                for feat in self.karst_features.getFeatures():
                    self.karst_features.changeAttributeValue(feat.id(), self.karst_features.fields().indexFromName('temp'), 4)
                self.karst_features.commitChanges()

                processing.run("gdal:rasterize", {'INPUT': self.karst_features,
                                                  'FIELD': 'temp',
                                                  'HEIGHT': self.raster_info['resolution_y'],
                                                  'WIDTH': self.raster_info['resolution_x'],
                                                  'UNITS': 1,
                                                  'EXTENT': self.raster_info['extent']['str_extent'],
                                                  'OUTPUT': str(self.doss) + '/rKarst_features.tif'})
                self.karst_features.startEditing()
                self.karst_features.dataProvider().deleteAttributes([self.karst_features.fields().indexFromName('temp')])
                self.karst_features.updateFields()
                self.karst_features.commitChanges()

                rKarst_features = QgsRasterLayer(str(self.doss) + '/rKarst_features.tif', 'rKarst_features')
            else:
                rKarst_features = None

            # Croisement des valeurs des rasters sur chaque pixel
            valCarteKa = numpy.zeros((self.raster_info['size_y'], self.raster_info['size_x']), numpy.int16)
            val_i = range(0, self.raster_info['size_x'], 1)
            val_j = range(0, self.raster_info['size_y'], 1)
            if rKarst_features is None:
                pKarst_features = None
            else:
                pKarst_features = rKarst_features.dataProvider()
            for j in val_j:
                self.progress.emit(j, len(val_j))
                for i in val_i:
                    pos = QgsPointXY(
                        (self.raster_info['extent']['Xmin'] + (i + 1) * self.raster_info['resolution_x']) - self.raster_info[
                            'resolution_x'] / 2,
                        (self.raster_info['extent']['Ymax'] - j * self.raster_info['resolution_y']) - self.raster_info[
                            'resolution_y'] / 2)
                    if pKarst_features:
                        valKarst_features, found = pKarst_features.sample(pos, 1)
                        if found and valKarst_features:
                            valCarteKa[j, i] = 4
                        else:
                            valCarteKa[j, i] = self.mangin
                    else:
                        valCarteKa[j, i] = self.mangin

            # ecriture du raster a partir de l'array
            raster = gdal.GetDriverByName('Gtiff').Create(str(self.doss) + '/Ka_factor.tif', self.raster_info['size_x'],
                                                          self.raster_info['size_y'], 1, gdal.GDT_Byte)

            raster.SetProjection(self.raster_info['projection_wkt'])
            raster.SetGeoTransform((self.raster_info['extent']['Xmin'],
                                    float(self.raster_info['resolution_x']),
                                    0.0,
                                    self.raster_info['extent']['Ymax'],
                                    0.0,
                                    float(-self.raster_info['resolution_y']),
                                    ))
            Band = raster.GetRasterBand(1)
            Band.WriteArray(valCarteKa, 0, 0)
            Band.FlushCache()
            Band.SetNoDataValue(0)

            # fermeture des connexions
            rKarst_features = None
            Raster = None
            self.results.emit()
        except Exception as e:
            self.error.emit(Exception('An error happen when generating the Ka Factor: %s' % str(e)))
        finally:
            self.finished.emit()


class WorkerCarteFinale(QObject):

    results = pyqtSignal()
    error = pyqtSignal(Exception)
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)

    def __init__(self, doss, raster_info, pP, pR, pI, pKa, carte_p, carte_r, carte_i, carte_ka):
        super().__init__()
        self.raster_info = raster_info
        self.doss = doss
        self.pP = pP
        self.pI = pI
        self.pR = pR
        self.pKa = pKa
        self.carte_p = carte_p
        self.carte_i = carte_i
        self.carte_ka = carte_ka
        self.carte_r = carte_r

    def run(self):
        try:
            entries = []
            LayI = QgsRasterCalculatorEntry()
            LayI.ref = "LayI@1"
            LayI.raster = self.carte_i
            LayI.bandNumber = 1
            entries.append(LayI)

            LayK = QgsRasterCalculatorEntry()
            LayK.ref = "LayK@1"
            LayK.raster = self.carte_ka
            LayK.bandNumber = 1
            entries.append(LayK)

            LayR = QgsRasterCalculatorEntry()
            LayR.ref = "LayR@1"
            LayR.raster = self.carte_r
            LayR.bandNumber = 1
            entries.append(LayR)

            LayP = QgsRasterCalculatorEntry()
            LayP.ref = "LayP@1"
            LayP.raster = self.carte_p
            LayP.bandNumber = 1
            entries.append(LayP)

            # creation du calcul a realiser
            Formula = "LayI@1*%s+LayK@1*%s+LayR@1*%s+LayP@1*%s" % (self.pI, self.pKa, self.pR, self.pP)
            calc = QgsRasterCalculator(Formula, os.path.join(self.doss, 'Carte_Vg.tif'), 'Gtiff', self.carte_i.extent(), self.carte_i.width(),
                                       self.carte_i.height(), entries)
            res = calc.processCalculation()

            rCarte_Vg = QgsRasterLayer(os.path.join(self.doss, 'Carte_Vg.tif'), 'Carte_Vg')
            rules = [-1, 79, 0, 79, 159, 1, 159, 239, 2, 240, 319, 3, 319, 400, 4]

            processing.run("native:reclassifybytable", {'INPUT_RASTER': rCarte_Vg,
                                                        'RASTER_BAND': 1,
                                                        'TABLE': rules,
                                                        'NO_DATA': -9999,
                                                        'RANGE_BOUNDARIES': 0,
                                                        'NODATA_FOR_MISSING': False,
                                                        'DATA_TYPE': 5,
                                                        'OUTPUT': os.path.join(self.doss, 'Vulnerability_Map.tif')})
            self.progress.emit(1, 1)
            self.results.emit()
        except Exception as e:
            self.error.emit(Exception('An error happen when generating the Final map: %s' % str(e)))
        finally:
            self.finished.emit()



