from osgeo import gdal, ogr, osr
from qgis.core import *

def genere_guide(impluvium, resolution, doss):

	# 1. Define pixel_size and NoData value of new raster
	NoData_value = -9999
	x_res = resolution 
	y_res = resolution
	pixel_size = resolution

	# 3. Open Shapefile and get its SCR
	Syst_coord = impluvium.crs().toWkt()
	print Syst_coord
	implu = [f for f in impluvium.getFeatures()] 
	geom = implu[0].geometry().buffer(1000,5).boundingBox()
	Xmin = geom.xMinimum()
	Ymin = geom.yMinimum()
	Xmax= geom.xMaximum()
	Ymax = geom.yMaximum()
	print Xmin,Ymin,Xmax,Ymax

	# 4. Create Target - TIFF - and apply SCR
	cols = int( (Xmax - Xmin) / x_res )
	rows = int( (Ymax - Ymin) / y_res )
	print cols,rows

	raster = gdal.GetDriverByName('GTiff').Create(str(doss)+'/Extension.tif', cols, rows, 1, gdal.GDT_Byte)
	proj = osr.SpatialReference() 
	proj.ImportFromWkt(Syst_coord)
	raster.SetProjection(proj.ExportToWkt())
	raster.SetGeoTransform((Xmin, resolution, 0, Ymax, 0, -resolution))
	band = raster.GetRasterBand(1)
	band.SetNoDataValue(NoData_value)
	
