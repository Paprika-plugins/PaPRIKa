import processing
from qgis.core import *
from osgeo import gdal, ogr, osr
import numpy
from shutil import copyfile
import os

def genere_carteI(doss, extension, dem, reclass_rules_pente,exokarst,field_exokarst):
    #creation du raster Pente
    processing.runalg("gdalogr:slope",dem,1,False,False,True,1,str(doss)+'/rPente.tif')
    rPente = QgsRasterLayer(str(doss)+'/rPente.tif', "rPente")
    print rPente.isValid()
    #creation du raster Exokarst si besoin
    if field_exokarst is None:
        rExokarst = None
    else:
        copyfile(str(doss)+'/Extension.tif',str(doss)+'/rExokarst.tif')
        processing.runalg("gdalogr:rasterize_over", exokarst, field_exokarst, str(doss)+'/rExokarst.tif')
        rExokarst = QgsRasterLayer(str(doss)+'/rExokarst.tif', "rExokarst")

    #recuperation des bornes XY de la zone
    extension1 = gdal.Open(extension.source())
    ExtentInfo = extension1.GetGeoTransform()
    Xmin = str(ExtentInfo[0])
    Ymin = str(ExtentInfo[3])
    Xmax = str(ExtentInfo[0] + ExtentInfo[1] * extension1.RasterXSize)
    Ymax = str(ExtentInfo[3] + ExtentInfo[5] * extension1.RasterYSize)
    Extent =(Xmin, Xmax, Ymax, Ymin)
    StrExtent = ','.join(Extent)
    print(StrExtent)

    #reclassement de la pente
    if QGis.QGIS_VERSION_INT > 21800:
        processing.runalg("grass7:r.reclass", rPente, reclass_rules_pente,"", StrExtent, ExtentInfo[1], str(doss)+'/Slope.tif')
    else :
        processing.runalg("grass7:r.reclass", rPente, reclass_rules_pente, StrExtent, ExtentInfo[1], str(doss)+'/Slope.tif')

    rSlope = QgsRasterLayer(str(doss)+'/Slope.tif', "rSlope")
    print 'ok'
    rPente = None
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

    #recuperation du systeme de coordonnees
    source = gdal.Open(extension.source())
    Syst_coord = source.GetProjection()

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
    print 'Done!'
    
    #fermeture des connexions
    rExokarst = None
    rSlope = None
    Raster = None
