import processing
from qgis.core import *
from osgeo import gdal, ogr, osr
import numpy
from shutil import copyfile
import os

def genere_carteI(doss, raster_info, dem, reclass_rules_pente,exokarst,field_exokarst):
    #creation du raster Pente
    processing.run("gdalogr:slope", {'INPUT': '',
                                     'OUTPUT': ''})

    #creation du raster Exokarst si besoin
    if field_exokarst is None:
        rExokarst = None
    else:
        processing.run("gdal:rasterize",{'INPUT': '',
                                         'OUTPUT': ''})

    processing.run("grass7:r.reclass", {'INPUT': '',
                                        'OUTPUT': ''})

    #preparation des variables pour le croisement
    val_i = range(0, extension1.RasterXSize, 1)
    val_j = range(0, extension1.RasterYSize, 1)
    pSlope = rSlope.dataProvider()
    if rExokarst is None:
        pExokarst = None
    else:
        pExokarst = rExokarst.dataProvider()
    ValCarteI= numpy.zeros((extension1.RasterYSize, extension1.RasterXSize), numpy.int16)
    #iteration sur les pixels: selection de la valeur la plus faible et ecriture dans l'array
    for j in val_j:
        for i in val_i:
            pos = QgsPoint((ExtentInfo[0] + (i+1) * int(ExtentInfo[1])) - int(ExtentInfo[1])/2, (ExtentInfo[3] - j * int(ExtentInfo[1])) - int(ExtentInfo[1])/2)
            valSlope = pSlope.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
            if pExokarst is None:
                valExokarst = 0
            else:
                valExokarst = pExokarst.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]

            ValCarteI[j,i] = max([valSlope, valExokarst]) if (valSlope,valExokarst) != (None,None) else 0

    #ecriture du raster a partir de l'array
    Raster = gdal.GetDriverByName('Gtiff').Create(str(doss)+'/I_factor.tif', extension1.RasterXSize, extension1.RasterYSize, 1, gdal.GDT_Byte)
    proj = osr.SpatialReference()
    proj.ImportFromWkt(Syst_coord)
    Raster.SetProjection(proj.ExportToWkt())
    Raster.SetGeoTransform(ExtentInfo)
    Band = Raster.GetRasterBand(1)
    Band.WriteArray(ValCarteI, 0, 0)
    Band.FlushCache()
    Band.SetNoDataValue(0)

    #fermeture des connexions
    rExokarst = None
    rSlope = None
    Raster = None
