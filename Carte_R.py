from qgis.core import *
import processing
from osgeo import gdal, ogr, osr
import numpy
from shutil import copyfile
import os

def genere_carteR (doss, extension, lithology, field_lithology, structure, field_structure):

	#recuperation des bornes XY de la zone
	extension1 = gdal.Open(extension.source())
	ExtentInfo = extension1.GetGeoTransform()
	Xmin = str(ExtentInfo[0])
	Ymin = str(ExtentInfo[3])
	Xmax = str(ExtentInfo[0] + ExtentInfo[1] * extension1.RasterXSize)
	Ymax = str(ExtentInfo[3] + ExtentInfo[5] * extension1.RasterYSize)
	Extent = Xmin,Xmax,Ymax,Ymin
	StrExtent = ','.join(Extent)
	print ExtentInfo
	print StrExtent
	
	#Rasterisation et ouverture de la couche Lithology
	copyfile(str(doss)+'/Extension.tif',str(doss)+'/rLithology.tif')
	processing.runalg("gdalogr:rasterize_over", lithology, field_lithology, str(doss)+'/rLithology.tif')
	rLithology = QgsRasterLayer(str(doss)+'/rLithology.tif', 'rLithology')
	
	#Rasterisation et ouverture de la couche Structure
	if structure is None:
		print 'Structure is None'
	else:
		copyfile(str(doss)+'/Extension.tif',str(doss)+'/rStructure.tif')
		processing.runalg("gdalogr:rasterize_over", structure, field_structure, str(doss)+'/rStructure.tif')
		rStructure = QgsRasterLayer(str(doss)+'/rStructure.tif', 'rStructure')
	
	#Preparation des donnees pour la comparaison des valeurs des rasters sur chaque pixel
	val_i = range(0, extension1.RasterXSize, 1)
	val_j = range(0, extension1.RasterYSize, 1)
	
	if lithology is None:
		pass
	else:
		pLithology = rLithology.dataProvider()
	if structure is None:
		pStructure = None
	else:
		pStructure = rStructure.dataProvider()
		
	#iteration sur les pixels
	ValCarteR = numpy.zeros((extension1.RasterYSize, extension1.RasterXSize), numpy.int16)
	for j in val_j:
		for i in val_i:
			valeur = []
			pos = QgsPoint((ExtentInfo[0] + i * abs(ExtentInfo[1])) - abs(ExtentInfo[1])/2, (ExtentInfo[3] - j * abs(ExtentInfo[1])) - abs(ExtentInfo[1])/2)
			if lithology is None:
				valLithology = 6
			else:
				valLithology = pLithology.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
				if valLithology is None:
					valLithology = 6
			if structure is None:
				valStructure = 0
			else:
				valStructure = pStructure.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
				if valStructure is None or valStructure == 0:
					valStructure = 0
				else:
					valStructure = 1
					
			ValCarteR[j,i] = valLithology + valStructure
			
	#recuperation du systeme de coordonnees
	source = gdal.Open(extension.source())
	Syst_coord = source.GetProjection()

	#ecriture du raster a partir de l'array
	Raster = gdal.GetDriverByName('Gtiff').Create(str(doss)+'/R_factor.tif', extension1.RasterXSize, extension1.RasterYSize, 1, gdal.GDT_Byte)
	proj = osr.SpatialReference()
	proj.ImportFromWkt(Syst_coord)
	Raster.SetProjection(proj.ExportToWkt())
	Raster.SetGeoTransform(ExtentInfo)
	Band = Raster.GetRasterBand(1)
	Band.WriteArray(ValCarteR, 0, 0)
	Band.FlushCache()
	Band.SetNoDataValue(6)
	
	#fermeture des connexions
	rLithology = None
	rStructure = None
	Raster = None
	
	
	
	
	
	
	
	