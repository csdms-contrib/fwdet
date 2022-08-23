'''
InundationDepth_Coastal_CostAllocation.py

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
'''

import arcpy
import arcgisscripting
from arcpy.sa import *
import timeit
import os

#from p281 of python scripting for arcgis 
script = arcgisscripting.create(9.3) #I have no clue why this is 9.3


start = timeit.default_timer()
def main():
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    WS = arcpy.env.workspace = script.GetParameterAsText(0)
    #THIS STILL NEEDS TO BE SET
    arcpy.env.scratchWorkspace = script.GetParameterAsText(0)
    DEMname = os.path.basename(script.GetParameterAsText(2))
    InundPolygon = os.path.basename(script.GetParameterAsText(1))
    ClipDEM = os.path.basename(script.GetParameterAsText(3))
    dem = arcpy.Raster(DEMname)
    CostRaster = (((dem < 0)*9)+1)
    CostRaster.save(WS+'\CostRaster')

    cellSize = dem.meanCellHeight
    boundary = CalculateBoundary(dem, InundPolygon, cellSize, WS)
    #this will have to be uncommented for later areas

    #boundary = Raster('boundary_elev')  # a raster layer with only the boundary cells having value (elevation)
    #extent = str(dem.extent.XMin) + " " + str(dem.extent.YMin) + " " + str(dem.extent.XMax) + " " + str(dem.extent.YMax)
    extent = '{} {} {} {}'.format(dem.extent.XMin,dem.extent.YMin,dem.extent.XMax,dem.extent.YMax)
    #arcpy.Clip_management(DEMname, extent, ClipDEM, InundPolygon, cellSize, 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')
    arcpy.env.extent = arcpy.Extent(dem.extent.XMin, dem.extent.YMin, dem.extent.XMax, dem.extent.YMax)
    print 'Conversion to Integer'
    boundaryInt = Int(boundary * 10000)
    boundaryInt.save('boundaryInt')
    print 'Cost Allocation'
    #EucAll = EucAllocation(boundary, cellSize, "Value", "Euc_Distance")
    #arcpy.CostAllocation_sa('boundary_elev_int6', 'weight_dem', 'Cost_alloc_weight', '#', '#', 'Value')
    CostAlloc = CostAllocation(boundaryInt, CostRaster, '#', '#', 'Value')
    CostAlloc.save('CostAlloc_int')
    CostAlloc = Float(CostAlloc) / 10000
    CostAlloc.save('CostAlloc')
    print 'Water Depth'
    waterDepth = Minus(CostAlloc, ClipDEM)
    waterDepth = Con(waterDepth <= 0, 0, waterDepth)
    waterDepth.save(os.path.basename(script.GetParameterAsText(4)))
    print 'Filter'
    waterDepthFilter = Filter(waterDepth, "LOW", "DATA")
    whereClause = "VALUE > 0"
    waterDepthFilter2 = Con(ClipDEM, waterDepthFilter, '#', whereClause)
    waterDepthFilter2.save(os.path.basename(script.GetParameterAsText(4))+'_filtered')
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

main()

stop = timeit.default_timer()
print 'start: ', start, '\n'
print 'End: ', stop, '\n'
print 'Run time: ', (stop - start)/60, 'min'
