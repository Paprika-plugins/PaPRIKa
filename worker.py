# -*- coding: utf-8 -*-
import os
import numpy
import gdal
import processing
from qgis.core import QgsRasterLayer, QgsPointXY
from PyQt5.QtCore import QObject, pyqtSignal

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
            self.error.emit(Exception('Une erreur est survenue lors de la génération de la carte P : %s' % str(e)))
        finally:
            self.finished.emit()
