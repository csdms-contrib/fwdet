'''
InundationDepth_Coastal_CostAllocation_manual.py

Calculate water depth from a flood extent polygon (e.g. from remote sensing analysis) based on an underlying DEM (or HAND).
Program procedure:
1. Flood extent polygon to polyline
2. Polyline to Raster - DEM extent and resolution (Env)
3. Con - DEM values to Raster
4. Euclidean Allocation - assign boundary cell elevation to nearest domain cells
5. Calculate water depth by deducting DEM by Euclidean Allocation
6. Run low-pass Filter

Created by Sagy Cohen and Austin Raney, Surface Dynamics Modeling Lab, University of Alabama
email: sagy.cohen@ua.edu; aaraney@crimson.ua.edu
web: http://sdml.ua.edu
October 1, 2018

Updated by Austin Raney
August 19, 2019
'''

import arcpy
import arcgisscripting
from arcpy.sa import *
import timeit
import os

#from p281 of python scripting for arcgis
script = arcgisscripting.create(9.3) #I have no clue why this is 9.3

start = timeit.default_timer()
def main(ws_path, dem_path, extent_path):
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    WS = arcpy.env.workspace = ws_path
    #THIS STILL NEEDS TO BE SET
    arcpy.env.scratchWorkspace = ws_path
    DEMname = dem_path
    InundPolygon = extent_path
    ClipDEM = 'clipDEM'
    dem = arcpy.Raster(DEMname)
    CostRaster = (((dem < 0)*9)+1)
    CostRaster.save(WS+'\CostRaster')

    cellSize = dem.meanCellHeight
    boundary = CalculateBoundary(dem, InundPolygon, cellSize, WS)
    #this will have to be uncommented for later areas

    extent = '{} {} {} {}'.format(dem.extent.XMin,dem.extent.YMin,dem.extent.XMax,dem.extent.YMax)
    arcpy.Clip_management(DEMname, extent, ClipDEM, InundPolygon, cellSize, 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')
    arcpy.env.extent = arcpy.Extent(dem.extent.XMin, dem.extent.YMin, dem.extent.XMax, dem.extent.YMax)
    print 'Conversion to Integer'
    boundaryInt = Int(boundary * 10000)
    boundaryInt.save('boundaryInt')
    print 'Cost Allocation'
    CostAlloc = CostAllocation(boundaryInt, CostRaster, '#', '#', 'Value')
    CostAlloc.save('CostAlloc_int')
    CostAlloc = Float(CostAlloc) / 10000
    CostAlloc.save('CostAlloc')
    print 'Water Depth'
    waterDepth = Minus(CostAlloc, ClipDEM)
    waterDepth = Con(waterDepth <= 0, 0, waterDepth)
    waterDepth.save(WS+'\waterDepth')
    print 'Filter'
    waterDepthFilter = Filter(waterDepth, "LOW", "DATA")
    whereClause = "VALUE > 0"
    waterDepthFilter2 = Con(ClipDEM, waterDepthFilter, '#', whereClause)
    waterDepthFilter2.save(WS+'\waterDepth_filtered')
    print 'Done'

def CalculateBoundary(dem, InundPolygon,cellSize,WS):
    arcpy.PolygonToLine_management(InundPolygon, WS+'\polyline') #Convert inundation extent polygon to polyline
    arcpy.PolylineToRaster_conversion(WS+'\\polyline', 'OBJECTID', WS+'\linerast15', 'MAXIMUM_LENGTH', 'NONE', cellSize) #Convert polyline to raster
    print ('after polyline to raster')
    inRaster = Raster(WS+'\linerast15')
    inTrueRaster = dem
    inFalseConstant = '#'
    whereClause = "VALUE >= 0"
    print ('Con')
    boundary = Con(inRaster, inTrueRaster, inFalseConstant, whereClause) #extract the boundary cells elevation from a DEM
    OutRasTemp = FocalStatistics(dem, 'Circle 2 CELL', "MINIMUM", "DATA")
    OutRasTemp.save('BoundaryFocal_circ2')
    whereClause = "VALUE > 0"
    boundary = Con(OutRasTemp, boundary, inFalseConstant, whereClause)
    boundary.save('boundary_elev') #name of output boundary cell elevation raster
    return boundary


if __name__ == '__main__':
    # Globals
    ws_path = ""
    dem_path = ""
    extent_path = ""

    main('')

    stop = timeit.default_timer()
    print 'start: ', start, '\n'
    print 'End: ', stop, '\n'
    print 'Run time: ', (stop - start)/60, 'min'
