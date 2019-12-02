from qgis.core import *
import processing
from osgeo import gdal, ogr, osr
import numpy
from shutil import copyfile
import os
    

def genere_carteP(raster_info, doss,
                  layer_zns,
                  layer_sol, field_sol,
                  layer_epikarst, field_epikarst,
                  layer_sinking, field_sinking):
    """algorithme de generation de la Carte P"""

    processing.run("gdal:rasterize", {'INPUT': layer_sol,
                                      'FIELD': field_sol,
                                      'HEIGHT': raster_info['resolution_y'],
                                      'WIDTH': raster_info['resolution_x'],
                                      'UNITS': 1,
                                      'EXTENT': raster_info['extent']['str_extent'],
                                      'OUTPUT': os.path.join(doss,'rSol.tif')})
    processing.run("grass7:r.resample", {'input': layer_zns,
                                         'GRASS_REGION_PARAMETER': raster_info['extent']['str_extent'],
                                         'GRASS_REGION_CELLSIZE_PARAMETER': raster_info['resolution_x'],
                                         'output': os.path.join(doss, 'rZNS.tif')})

    if layer_epikarst is None:
        pass
    else:
        processing.run("gdal:rasterize", {'INPUT': layer_epikarst,
                                          'FIELD': field_epikarst,
                                          'HEIGHT': raster_info['resolution_y'],
                                          'WIDTH': raster_info['resolution_x'],
                                          'UNITS': 1,
                                          'EXTENT': raster_info['extent']['str_extent'],
                                          'OUTPUT': os.path.join(doss, 'rEpikarst.tif')})
    
    if layer_sinking is None :
        pass
    else:
        processing.run("gdal:rasterize", {'INPUT': layer_sinking,
                                          'FIELD': field_sinking,
                                          'HEIGHT': raster_info['resolution_y'],
                                          'WIDTH': raster_info['resolution_x'],
                                          'UNITS': 1,
                                          'EXTENT': raster_info['extent']['str_extent'],
                                          'OUTPUT': os.path.join(doss, 'rSinking.tif')})

    #Preparation des donnees pour la comparaison des valeurs des rasters sur chaque pixel
    val_i = range(0, raster_info['size_x'], 1)
    val_j = range(0, raster_info['size_y'], 1)
    if layer_epikarst is None:
        pass
    else:
        rEpikarst = QgsRasterLayer(os.path.join(doss, 'rEpikarst.tif'), 'rEpikarst')
        pEpikarst = rEpikarst.dataProvider()
    if layer_sinking is None:
        pass
    else:
        rSinking = QgsRasterLayer(os.path.join(doss, 'rSinking.tif'), 'rSinking')
        pSinking = rSinking.dataProvider()
    rZNS = QgsRasterLayer(os.path.join(doss, 'rZNS.tif'), 'rZNS')
    pZNS = rZNS.dataProvider()
    rSol = QgsRasterLayer(os.path.join(doss, 'rSol.tif'), 'rSol')
    pSol = rSol.dataProvider()


    #iteration sur les pixels: selection de la valeur la plus faible et ecriture dans l'array
    ValCarteP = numpy.zeros((raster_info['size_y'], raster_info['size_x']), numpy.int16)
    for j in val_j:
        for i in val_i:
            valeur = []
            pos = QgsPointXY((raster_info['extent']['Xmin'] + (i+1) * raster_info['resolution_x']) - raster_info['resolution_x']/2,
                             (raster_info['extent']['Ymax'] - j * raster_info['resolution_y']) - raster_info['resolution_y']/2)
            if layer_sol is None:
                valSol = 6
            else:
                valSol, found = pSol.sample(pos, 1)
                if not found or valSol == 0:
                    valSol = 6
            if layer_zns is None:
                valZNS = 6
            else:
                valZNS, found = pZNS.sample(pos, 1)
                if not found or valZNS == 0:
                    valZNS = 6
            if layer_epikarst is None:
                valEpikarst = 6
            else:
                valEpikarst, found = pEpikarst.sample(pos, 1)
                if not found or valEpikarst == 0:
                    valEpikarst = 6
            if layer_sinking is None:
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

    #ecriture du raster a partir de l'array
    raster = gdal.GetDriverByName('Gtiff').Create(os.path.join(doss,'P_factor.tif'),
                                                  raster_info['size_x'], raster_info['size_y'],
                                                  1, gdal.GDT_Byte)
    # proj = osr.SpatialReference()
    # proj.ImportFromWkt(raster_info['projection_wkt'])
    raster.SetProjection(raster_info['projection_wkt'])
    raster.SetGeoTransform((raster_info['extent']['Xmin'],
                            float(raster_info['resolution_x']),
                            0.0,
                            raster_info['extent']['Ymax'],
                            0.0,
                            float(-raster_info['resolution_y']),
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

