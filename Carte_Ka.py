import processing
from qgis.core import *
from PyQt5.QtCore import QVariant
from shutil import copyfile
import numpy
from osgeo import gdal, ogr, osr

def genere_carteKa(Mangin, karst_features, extension, doss):
    if karst_features is not None:
        #Rasterisation et ouverture de la couche karst features
        copyfile(str(doss)+'/Extension.tif',str(doss)+'/rKarst_features.tif')
        #Prepare karst_features datas
        karst_features.startEditing()
        karst_features.dataProvider().addAttributes([QgsField("temp",  QVariant.Int)])
        karst_features.commitChanges()
        karst_features.startEditing()
        for feat in karst_features.getFeatures():
            karst_features.changeAttributeValue(feat.id(),karst_features.fieldNameIndex('temp'), 4)
        karst_features.commitChanges()
        #process rasterization and delete temp fields
        processing.runalg("gdalogr:rasterize_over", karst_features, 'temp', str(doss)+'/rKarst_features.tif')
        karst_features.startEditing()
        karst_features.dataProvider().deleteAttributes([karst_features.fieldNameIndex('temp')])
        karst_features.updateFields()
        karst_features.commitChanges()

        rKarst_features = QgsRasterLayer(str(doss)+'/rKarst_features.tif','rKarst_features')
    else:
        rKarst_features = None
    
    #Creation du raster global a partir de la classification de Mangin
        #recuperation des bornes XY de la zone
    extension1 = gdal.Open(extension.source())
    ExtentInfo = extension1.GetGeoTransform()
    Xmin = str(ExtentInfo[0])
    Ymin = str(ExtentInfo[3])
    Xmax = str(ExtentInfo[0] + ExtentInfo[1] * extension1.RasterXSize)
    Ymax = str(ExtentInfo[3] + ExtentInfo[5] * extension1.RasterYSize)
    Extent =(Xmin, Xmax, Ymax, Ymin)
    StrExtent = ','.join(Extent)
    
    #recuperation du systeme de coordonnees
    source = gdal.Open(extension.source())
    Syst_coord = source.GetProjection()

    #Croisement des valeurs des rasters sur chaque pixel
    valCarteKa = numpy.zeros((extension1.RasterYSize, extension1.RasterXSize), numpy.int16)
    val_i = range(0, extension1.RasterXSize, 1)
    val_j = range(0, extension1.RasterYSize, 1)
    if rKarst_features is None:
        pKarst_features = None
    else:
        pKarst_features = rKarst_features.dataProvider()
    for j in val_j:
        for i in val_i:        
            pos = QgsPoint((ExtentInfo[0] + (i+1) * ExtentInfo[1]) - ExtentInfo[1]/2, (ExtentInfo[3] - j * ExtentInfo[1]) - ExtentInfo[1]/2)
            if pKarst_features:
                valKarst_features = pKarst_features.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
                if valKarst_features:
                    valCarteKa[j,i] = 4
                else :
                    valCarteKa[j,i] = Mangin
            else:
                valCarteKa[j,i] = Mangin

    #ecriture du raster a partir de l'array
    Raster = gdal.GetDriverByName('Gtiff').Create(str(doss)+'/Ka_factor.tif', extension1.RasterXSize, extension1.RasterYSize, 1, gdal.GDT_Byte)
    proj = osr.SpatialReference()
    proj.ImportFromWkt(Syst_coord)
    Raster.SetProjection(proj.ExportToWkt())
    Raster.SetGeoTransform(ExtentInfo)
    Band = Raster.GetRasterBand(1)
    Band.WriteArray(valCarteKa, 0, 0)
    Band.FlushCache()
    Band.SetNoDataValue(0)
    
    #fermeture des connexions
    rKarst_features = None
    Raster = None
