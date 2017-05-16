from osgeo import gdal, ogr, osr

def genere_guide(impluvium, resolution, doss):

	# 1. Define pixel_size and NoData value of new raster
	NoData_value = -9999
	x_res = resolution # assuming these are the cell sizes
	y_res = resolution # change as appropriate
	pixel_size = resolution

	# 2. Filenames for in- and output
	_in = impluvium.source()

	# 3. Open Shapefile and get its SCR
	source_ds = ogr.Open(_in)
	if source_ds is None:
		raise Exception("Could not open vector file")

	source_layer = source_ds.GetLayer()
	Syst_coord = source_layer.GetSpatialRef()
	Syst_coord = Syst_coord.ExportToWkt()
	x_min, x_max, y_min, y_max = source_layer.GetExtent()
	Xmin = x_min - 1000
	Ymin = y_min - 1000
	Xmax= x_max + 1000
	Ymax = y_max + 1000

	# 4. Create Target - TIFF - and apply SCR
	cols = int( (Xmax - Xmin) / x_res )
	rows = int( (Ymax - Ymin) / y_res )

	_raster = gdal.GetDriverByName('GTiff').Create(str(doss)+'/Extension.tif', cols, rows, 1, gdal.GDT_Byte)
	proj = osr.SpatialReference() 
	proj.ImportFromWkt(Syst_coord)
	_raster.SetProjection(proj.ExportToWkt())
	_raster.SetGeoTransform((Xmin, x_res, 0, Ymax, 0, -y_res))
	_band = _raster.GetRasterBand(1)
	_band.SetNoDataValue(NoData_value)
	
