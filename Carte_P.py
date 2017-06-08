from qgis.core import *
import processing
from osgeo import gdal, ogr, osr
import numpy
from shutil import copyfile
import os

def genere_carteP(extension, doss, ZNS,Sol, field_sol, Epikarst, field_epikarst, Sinking, field_sinking):
	"""algorithme de generation de la Carte P"""
	
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
	
	#Rasterisation et ouverture de la couche sol
	if Sol is None:
		print 'Sol None'
		pass
	else :
		copyfile(str(doss)+'/Extension.tif',str(doss)+'/rSol.tif')
		processing.runalg("gdalogr:rasterize_over", Sol, field_sol, str(doss)+'/rSol.tif')
		rSol = QgsRasterLayer(str(doss)+'/rSol.tif','rSol')
		print 'rSol generate'

	#Reechantillonage du raster ZNS
	if ZNS is None:
		print 'ZNS None'
		pass
		
	else:
		processing.runalg("grass7:r.resample",ZNS.source(),StrExtent,abs(ExtentInfo[1]), str(doss)+'/ZNS')
		src_ds_zns = gdal.Open(str(doss)+'/ZNS.tif')
		driver_zns = gdal.GetDriverByName("GTiff") 
		dst_ds_zns = driver_zns.CreateCopy(str(doss)+'/rZNS.tif', src_ds_zns, 0 )
		src_ds_zns = None
		dst_ds_zns = None
		os.remove(str(doss)+'/ZNS.tif')
		os.remove(str(doss)+'/ZNS.tfw')
		rZNS = QgsRasterLayer(str(doss)+'/rZNS.tif','rZNS')
		print 'rZNS generate'
	
	#Rasterisation et ouverture de la couche epikarst
	if Epikarst is None:
		print 'Epikarst none'
		pass
	else:
		print Epikarst.name()
		copyfile(str(doss)+'/Extension.tif',str(doss)+'/rEpikarst.tif')
		processing.runalg("gdalogr:rasterize_over", Epikarst, field_epikarst, str(doss)+'/rEpikarst.tif')
		rEpikarst = QgsRasterLayer(str(doss)+'/rEpikarst.tif','rEpikarst')
	
	#Rasterisation et ouverture de la couche Sinking Stream Catchment
	if Sinking is None :
		print 'Sinking none'
		pass
	else:
		print Sinking.name()
		copyfile(str(doss)+'/Extension.tif',str(doss)+'/rSinking.tif')
		processing.runalg("gdalogr:rasterize_over", Sinking, field_sinking, str(doss)+'/rSinking.tif')
		rSinking = QgsRasterLayer(str(doss)+'/rSinking.tif','rSinking')


	#Preparation des donnees pour la comparaison des valeurs des rasters sur chaque pixel
	val_i = range(0, extension1.RasterXSize, 1)
	val_j = range(0, extension1.RasterYSize, 1)
	if Epikarst is None:
		pass
	else:
		pEpikarst = rEpikarst.dataProvider()
	if ZNS is None:
		print 'ZNS is none'
		pass
	else:
		pZNS = rZNS.dataProvider()
		print 'pZNS OK'
	if Sol is None:
		print 'Sol is none'
		pass
	else:
		pSol = rSol.dataProvider()
		print 'pSol OK'
	if Sinking is None:
		pSinking = None
	else:
		pSinking = rSinking.dataProvider()

	#iteration sur les pixels: selection de la valeur la plus faible et ecriture dans l'array
	ValCarteP = numpy.zeros((extension1.RasterYSize, extension1.RasterXSize), numpy.int16)
	for j in val_j:
		for i in val_i:
			valeur = []
			pos = QgsPoint((ExtentInfo[0] + i * abs(ExtentInfo[1])) - abs(ExtentInfo[1])/2, (ExtentInfo[3] - j * abs(ExtentInfo[1])) - abs(ExtentInfo[1])/2)
			if Sol is None:
				valSol = 6
			else:
				valSol = pSol.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
				if valSol is None or valSol == 0:
					valSol = 6
			if ZNS is None:
				valZNS = 6
			else:
				valZNS = pZNS.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
				if valZNS is None or valZNS == 0:
					valZNS = 6
			if Epikarst is None:
				valEpikarst = 6
			else:
				valEpikarst = pEpikarst.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
				if valEpikarst is None or valEpikarst == 0: 
					valEpikarst = 6
			if Sinking is None:
				valSinking = 6
			else:
				valSinking = pSinking.identify(pos, QgsRaster.IdentifyFormatValue).results()[1]
				if valSinking is None or valSinking == 0:
					valSinking = 6
			#print valSol, valZNS, valEpikarst,valSinking		
			valeur.append(valSol)
			valeur.append(valZNS)
			valeur.append(valEpikarst)
			valeur.append(valSinking)
			ValCarteP[j,i] = min(valeur)
			 

	#recuperation du systeme de coordonnees
	source = gdal.Open(extension.source())
	Syst_coord = source.GetProjection()

	#ecriture du raster a partir de l'array
	Raster = gdal.GetDriverByName('Gtiff').Create(str(doss)+'/P_factor.tif', extension1.RasterXSize, extension1.RasterYSize, 1, gdal.GDT_Byte)
	proj = osr.SpatialReference()
	proj.ImportFromWkt(Syst_coord)
	Raster.SetProjection(proj.ExportToWkt())
	Raster.SetGeoTransform(ExtentInfo)
	Band = Raster.GetRasterBand(1)
	Band.WriteArray(ValCarteP, 0, 0)
	Band.FlushCache()
	Band.SetNoDataValue(6)


