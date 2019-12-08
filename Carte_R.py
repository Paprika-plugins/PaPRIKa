from qgis.core import *
import processing
from PyQt5.QtCore import QVariant
from osgeo import gdal, ogr, osr
import numpy
from shutil import copyfile
import os

def genere_carteR (doss, raster_info, layer_lithology, field_lithology, layer_structure):

    processing.run("gdal:rasterize", {'INPUT': layer_lithology,
                                      'FIELD': field_lithology,
                                      'HEIGHT': raster_info['resolution_y'],
                                      'WIDTH': raster_info['resolution_x'],
                                      'UNITS': 1,
                                      'EXTENT': raster_info['extent']['str_extent'],
                                      'OUTPUT': os.path.join(doss, 'rLithology.tif')})

    if layer_structure is None:
        pass
    else:
        layer_structure.startEditing()
        layer_structure.dataProvider().addAttributes([QgsField('temp',  QVariant.Int)])
        layer_structure.commitChanges()
        layer_structure.startEditing()
        field_structure = layer_structure.fields().indexFromName('temp')
        for feat in layer_structure.getFeatures():
            layer_structure.changeAttributeValue(feat.id(), field_structure, 4)
        layer_structure.commitChanges()
        processing.run("gdal:rasterize", {'INPUT': layer_structure,
                                          'FIELD': 'temp',
                                          'HEIGHT': raster_info['resolution_y'],
                                          'WIDTH': raster_info['resolution_x'],
                                          'UNITS': 1,
                                          'EXTENT': raster_info['extent']['str_extent'],
                                          'OUTPUT': os.path.join(doss, 'rStructure.tif')})
        layer_structure.startEditing()
        layer_structure.dataProvider().deleteAttributes([field_structure])
        layer_structure.updateFields()
        layer_structure.commitChanges()
    
    #Preparation des donnees pour la comparaison des valeurs des rasters sur chaque pixel
    val_i = range(0, raster_info['size_x'], 1)
    val_j = range(0, raster_info['size_y'], 1)
    
    if layer_lithology is None:
        pass
    else:
        rLithology = QgsRasterLayer(os.path.join(doss, 'rLithology.tif'), 'rLithology')
        pLithology = rLithology.dataProvider()
    if layer_structure is None:
        pStructure = None
    else:
        rStructure = QgsRasterLayer(os.path.join(doss, 'rStructure.tif'), 'rStructure')
        pStructure = rStructure.dataProvider()
        
    #iteration sur les pixels
    ValCarteR = numpy.zeros((raster_info['size_y'], raster_info['size_x']), numpy.int16)
    for j in val_j:
        for i in val_i:
            pos = QgsPointXY((raster_info['extent']['Xmin'] + (i+1) * raster_info['resolution_x']) - raster_info['resolution_x']/2,
                           (raster_info['extent']['Ymax'] - j * raster_info['resolution_y']) - raster_info['resolution_y']/2)
            if layer_lithology is None:
                valLithology = 6
            else:
                valLithology, found = pLithology.sample(pos, 1)
                if not found or valLithology == 0:
                    valLithology = 6
            if layer_structure is None:
                valStructure = 0
            else:
                valStructure, found = pStructure.sample(pos, 1)
                if not found or valStructure == 0:
                    valStructure = 0
                else:
                    valStructure = 4
                    
            ValCarteR[j,i] = valLithology + valStructure if valLithology + valStructure <= 4 else 4

    #ecriture du raster a partir de l'array
    raster = gdal.GetDriverByName('Gtiff').Create(os.path.join(doss, 'R_factor.tif'),
                                                  raster_info['size_x'], raster_info['size_y'],
                                                  1, gdal.GDT_Byte)
    proj = osr.SpatialReference()
    proj.ImportFromWkt(raster_info['projection_wkt'])
    raster.SetProjection(proj.ExportToWkt())
    raster.SetGeoTransform((raster_info['extent']['Xmin'],
                            float(raster_info['resolution_x']),
                            0.0,
                            raster_info['extent']['Ymax'],
                            0.0,
                            float(-raster_info['resolution_y']),
                            ))
    Band = raster.GetRasterBand(1)
    Band.WriteArray(ValCarteR, 0, 0)
    Band.FlushCache()
    Band.SetNoDataValue(6)
    
    #fermeture des connexions
    rLithology = None
    rStructure = None
    Raster = None
