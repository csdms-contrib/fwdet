# This Python file uses the following encoding: utf-8
'''
FwDET_QGIS.py

README:
Verified to work on QGIS 2.18.* 
Please change the outputFolder, dem, and inundPolygon PATH variables in lines 31-33 respectively to your appropriate
file's locations.
Open the python tool in QGIS, choose the icon to show editor, then use the blue icon to open a script and choose fwdet.py 

Calculate water depth from a flood extent polygon (e.g. from remote sensing analysis) based on an underlying DEM.
Program procedure:
1. Extract a clipping DEM using the inundPolygon and elevation DEM
2. Extract polyline from inundPolygon
3. Convert polyline to raster
4. Associate raster line values with underlying DEM values
5. Use grass7 Grow Distance function to calculate approximated flooding water level 
6. Run saga gaussian filter to smooth the the grass7 Grow Distance output

Created by Austin Raney, Sagy Cohen, Surface Dynamics Modeling Lab, University of Alabama
email: aaraney@crimson.ua.edu, sagy.cohen@ua.edu
web: http://sdml.ua.edu
March 23, 2018
Edited May 16, 2018, Aug 19, 2019
'''
import processing as proc
import os
import timeit
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator

time_init = timeit.default_timer()

# FILE INPUTS
outputFolder = 'output/folder'
dem = 'your/dem.tif'
inundPolygon = 'your/flood/polygon.shp'
# END FILE INPUTS

# begin helper functions
def floatDemExtent(QgsLayer):
	# takes in QgsLayer so QgsRasterLayer(path,'name') or QgsVectorLayer(path,'name') and returns extent [xmin, xmax, ymin, ymax] in a string of .f4 float formated numbers
	xm, xM, ym, yM = QgsLayer.extent().xMinimum(), QgsLayer.extent().xMaximum(), QgsLayer.extent().yMinimum(), QgsLayer.extent().yMaximum()
	QgsLayer = None
	return '{:.4f},{:.4f},{:.4f},{:.4f}'.format(xm, xM, ym, yM)

def rasterCalculator(layerPath, expression, extentPathIndex=0, fname=None):
	"""
	calculate solution of one of more raster.

	Usage: layerPath is a List of paths to rasters (e.g. ['var/myfile.tif', 'var/myfile2.tif'])
	the expression variable will be passed to python's .format string function. Theirfore an example of a multiplying two rasters
	goes as follows. '{0} * {1}' where 0 and 1 are the indcies of the layerPath list, so in the example myfile.tif * myfile2.tif would be calculated.
	extentPathIndex sets the extent to be used during the calculation to the given index of the layerPath. It is set by default to 0.
	fname is an optional variable which sets the output file name that is saved in the layerPath[0]'s parent folder if left as default,
	the layer will be named layerPath[0]'s value + _.output.tif
	"""
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

demLayer = QgsRasterLayer(dem, 'dem_extent')
demExtent = floatDemExtent(demLayer)
demSizeX, demSizeY = demLayer.rasterUnitsPerPixelX(), demLayer.rasterUnitsPerPixelY()

# process qgis algorithms

# clipping dem from dem and inundPolygon
clipDem = proc.runalg("saga:clipgridwithpolygon",dem,inundPolygon,3,os.path.join(outputFolder, 'clipDem.tif'))['OUTPUT']

polyLine = proc.runalg("qgis:polygonstolines",inundPolygon,os.path.join(outputFolder, 'polyline'))['OUTPUT']
polyLineExtent = floatDemExtent(QgsVectorLayer(polyLine,'line_extent','ogr'))

# note that gridcode might not be the right feature within the polyline. This may need to be editied
lineRaster = proc.runalg("gdalogr:rasterize",polyLine,"PARTS",1,demSizeX,demSizeY,polyLineExtent,False,0,
						 "",4,75,6,1,False,0,"",os.path.join(outputFolder, 'lineRaster'))['OUTPUT']

lineRaster = rasterCalculator([lineRaster], '{0} > 0', fname='lineRaster_fixed.tif')
print(lineRaster)

# associate underlying dem values to lineRaster
extractElevation = rasterCalculator([lineRaster, dem], '({0} * {1}) / {0}', 0, 'extractElevation.tif')
nearestCellRaster = proc.runalg("grass7:r.grow.distance",extractElevation,0,demExtent,0,None,os.path.join(outputFolder, 'growDistance'))['value']

# clip grow distance output using clipDEM
waterDepth = rasterCalculator([clipDem, nearestCellRaster], '(({1} - {0}) > 0) * ({1} - {0})', 0, 'waterDepth.tif')
lowPass = proc.runalg("saga:gaussianfilter",waterDepth,1,0,3,3,os.path.join(outputFolder, 'lowPass'))['RESULT']
os.system("open {}".format(waterDepth))
os.system("open {}".format(lowPass))
print('run time: {}'.format(timeit.default_timer() - time_init))