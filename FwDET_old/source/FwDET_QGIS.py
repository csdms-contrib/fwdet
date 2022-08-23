# This Python file uses the following encoding: utf-8
'''
FwDET_QGIS.py

README:
Verified to work on QGIS 3.12.1

To use, either import the function into a script, or use it by importing it
into qgis. If you choose to import the script into qgis, just change the
variables dem, inund_polygon, and water_depth_output_filename.

Written by Austin Raney, Sagy Cohen, Surface Dynamics Modeling Lab, University of Alabama
email: aaraney@crimson.ua.edu, sagy.cohen@ua.edu
web: http://sdml.ua.edu
'''
import os

# Qgis imports
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator

# begin helper functions
def float_extent(QgsLayer):
	# takes in QgsLayer so QgsRasterLayer(path,'name') or QgsVectorLayer(path,'name') and returns extent [xmin, xmax, ymin, ymax] in a string of .f4 float formated numbers
	xm, xM, ym, yM = QgsLayer.extent().xMinimum(), QgsLayer.extent().xMaximum(), QgsLayer.extent().yMinimum(), QgsLayer.extent().yMaximum()
	del QgsLayer
	return '{:.4f},{:.4f},{:.4f},{:.4f}'.format(xm, xM, ym, yM)

def raster_calculator(layerPath, expression, extentPathIndex=0, fname=None):
	'''
	calculate solution of one of more raster.

	Usage: 
		layerPath is a List of paths to rasters (e.g. ['var/myfile.tif',
		'var/myfile2.tif']) the expression variable will be passed to python's
		.format string function. Theirfore an example of a multiplying two
		rasters goes as follows. '{0} * {1}' where 0 and 1 are the indcies of the
		layerPath list, so in the example myfile.tif * myfile2.tif would be
		calculated. extentPathIndex sets the extent to be used during the
		calculation to the given index of the layerPath. It is set by default to
		0. fname is an optional variable which sets the output file name that is
		saved in the layerPath[0]'s parent folder if left as default, the layer
		will be named layerPath[0]'s value + _.output.tif
	'''
	from qgis.core import QgsRasterLayer

	if type(layerPath) != list:
		layerPath = [layerPath]
	layerNameList = [os.path.basename(x).split('.')[0] for x in layerPath]
	layerList = [QgsRasterLayer(layerPath[x], layerNameList[x]) for x in range(len(layerPath))]
	entries = [QgsRasterCalculatorEntry() for _ in range(len(layerPath))]

	def helper(L,L2,x):
		L[x].ref, L[x].raster, L[x].bandNumber = L2[x].name() + '@1', L2[x], 1 

	[helper(entries, layerList, x) for x in range(len(entries))]
	rasterCalculationExpression = expression.format(*map(lambda x: x.ref, entries))
	if fname:
		# Creates the path for which the calculation is saved to. 
		# THE FILE EXTENSION IS ASSUMED TO BE IN FNAME ex: fname = foo.tif
		fnamePath = os.path.join(os.path.dirname(layerPath[0]), fname)
	else:
		fnamePath = os.path.join(os.path.dirname(layerPath[0]), layerNameList[0] + '_output.tif')

	arglist = [rasterCalculationExpression, fnamePath, 'GTiff', layerList[extentPathIndex].extent(), layerList[extentPathIndex].width(), layerList[extentPathIndex].height(), entries]
	rasterCalculation = QgsRasterCalculator(*arglist)
	if rasterCalculation.processCalculation() != 0:
		print("Houston we have a problem with the rasters")
	else:
		return os.path.join(os.path.dirname(layerPath[0]), fnamePath)
# end helper functions


def fwdet(inundation_polygon, dem, water_depth_output_filename=None):
	'''
	Calculate water depth from a flood extent polygon (e.g. from remote sensing analysis) based on an underlying DEM.
	Program procedure:
	1. Extract a clipping DEM using the inundPolygon and elevation DEM
	2. Extract polyline from inundPolygon
	3. Convert polyline to raster
	4. Associate raster line values with underlying DEM values
	5. Use grass7 Grow Distance function to calculate approximated flooding water level 
	6. Run saga gaussian filter to smooth the the grass7 Grow Distance output

	Publication: Cohen et al., https://doi.org/10.1111/1752-1688.12609

	'''
	from os import system
	from os.path import dirname, join, splitext
	from shutil import copyfile, copy2

	# Qgis imports
	import processing
	from qgis.core import QgsRasterLayer, QgsRasterFileWriter, QgsRasterPipe, QgsVectorLayer, QgsProject

	dem_layer = QgsRasterLayer(dem, 'dem_extent')
	dem_extent = float_extent(dem_layer)
	dem_size_x, dem_size_y = dem_layer.rasterUnitsPerPixelX(), dem_layer.rasterUnitsPerPixelY()

	# Function input parameter dictionaries
	inudation_polygon_input = {
		'INPUT': inundation_polygon,
		'OUTPUT':'TEMPORARY_OUTPUT',
		}

	clip_input = {
		'INPUT': dem,
		'POLYGONS': inundation_polygon,
		'OUTPUT':'TEMPORARY_OUTPUT',
		}
	# End function input parameter dictionaries

	# Begin processing
	# Fix inundation polygon geometries 
	flood_extent_polygon = processing.run("native:fixgeometries", inudation_polygon_input)['OUTPUT']

	polygons_to_lines_input = {
		'INPUT': flood_extent_polygon,
	 	'OUTPUT':'TEMPORARY_OUTPUT',
		}

	# Polygons to polylines proceedure
	flood_extent_polyline =  processing.run("native:polygonstolines", polygons_to_lines_input)['OUTPUT']

	# Clip dem to inundation polygon
	clip_dem = processing.run("saga:cliprasterwithpolygon", clip_input)['OUTPUT']

	rasterize_input = {
		'INPUT': flood_extent_polyline,
		'FIELD': '',
		'BURN': 1,
		'UNITS': 1,
		'WIDTH': dem_size_x,
		'HEIGHT': dem_size_y,
		'EXTENT': float_extent(flood_extent_polyline),
		'NODATA': 0,
		'OPTIONS': '',
		'DATA_TYPE': 0,
		'INIT': None,
		'INVERT': False,
		'EXTRA': '',
		'OUTPUT': 'TEMPORARY_OUTPUT'
		}

	flood_extent_rasterized = processing.run("gdal:rasterize", rasterize_input)['OUTPUT']

	# associate underlying dem values to lineRaster
	extracted_elevation = raster_calculator([flood_extent_rasterized, dem], '({0} * {1}) / {0}', 0, 'extracted_elevation.tif')

	grow_distance_input = {
		'input': extracted_elevation,
		'metric': 0,
		'-m': False,
		'-': False,
		'distance': 'TEMPORARY_OUTPUT',
		'value': 'TEMPORARY_OUTPUT',
		'GRASS_REGION_PARAMETER': None,
		'GRASS_REGION_CELLSIZE_PARAMETER': 0,
		'GRASS_RASTER_FORMAT_OPT': '',
		'GRASS_RASTER_FORMAT_META': '',
		'value': join(dirname(extracted_elevation), 'euclidean_nearest.tif')
		}

	euclidean_nearest = processing.run("grass7:r.grow.distance", grow_distance_input)['value']

	# clip grow distance output using clipDEM
	flood_water_depth = raster_calculator([clip_dem, euclidean_nearest], '(({1} - {0}) > 0) * ({1} - {0})', 0, 'waterDepth.tif')

	low_pass_filter_input = {
		'INPUT': flood_water_depth,
		'SIGMA': 1,
		'MODE': 0,
		'RADIUS': 3,
		'RESULT': 'TEMPORARY_OUTPUT'
		}

	low_pass_filter = processing.run("saga:gaussianfilter", low_pass_filter_input)['RESULT']

	if water_depth_output_filename:
		copyfile(flood_water_depth, water_depth_output_filename)

		low_pass_water_depth_output_filename = '{}_low_pass.{}'.format(splitext(water_depth_output_filename)[0], 'tif')

		low_pass_outfile_input = {
			'INPUT': low_pass_filter,
			'TARGET_CRS': None,
			'NODATA': None,
			'COPY_SUBDATASETS': False,
			'OPTIONS': '',
			'EXTRA': '',
			'DATA_TYPE': 0,
			'OUTPUT': low_pass_water_depth_output_filename
			}

		processing.run("gdal:translate", low_pass_outfile_input)

if __name__ == "builtins":
	import timeit

	# FILE INPUTS
	dem = 'absolute/path/to/your/dem.tif'

	inund_polygon = 'absolute/path/to/your/flood/polygon.shp'

	water_depth_output_filename = 'path/to/output/floodwater_depth.tif'
	# END FILE INPUTS

	time_init = timeit.default_timer()

	fwdet(inund_polygon, dem, water_depth_output_filename=water_depth_output_filename)

	print('Time: {}'.format(round(timeit.default_timer() - time_init)))