# This Python file uses the following en#############
'''
InundationDepth.py

Calculate water depth from a flood extent polygon (e.g. from remote sensing analysis) based on an underlying DEM.
Program procedure:
1. Flood extent polygon to polyline
2. Polyline to Raster - DEM extent and resolution (Env)
3. Con - DEM values to Raster
4. Focal Statistics to Con - loop 3x3 to 100x100
5. Iterative Con - if isNull than focal else last iteration (lower focal)

Created by Sagy Cohen, Surface Dynamics Modeling Lab, University of Alabama
email: sagy.cohen@ua.edu
web: http://sdml.ua.edu
June 30, 2016

Updated by Austin Raney April 27, 2019
email: aaraney@crimson.ua.edu
'''

import arcpy
from arcpy.sa import *
import arcgisscripting
import os

script = arcgisscripting.create(9.3)

def main():
    # Parameter and Environment initialization
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    WS = arcpy.env.workspace = script.GetParameterAsText(0)
    arcpy.env.scratchWorkspace = script.GetParameterAsText(0)
    DEMname = os.path.basename(script.GetParameterAsText(1))
    InundPolygon = os.path.basename(script.GetParameterAsText(2))
    i_count = int(script.GetParameterAsText(3))
    ClipDEM = script.GetParameterAsText(4) if script.GetParameterAsText(4) else 'ClipDEM'
    dem = arcpy.Raster(DEMname)

    # Generate boundary from provided DEM 
    cellSize = dem.meanCellHeight
    boundary = Raster(CalculateBoundary(dem, InundPolygon, cellSize, WS, 'boundary1'))

    # Obtain extent for clipping usage
    extent = "{} {} {} {}".format( dem.extent.XMin, dem.extent.YMin, dem.extent.XMax, dem.extent.YMax)
    arcpy.Clip_management(DEMname, extent, ClipDEM, InundPolygon, '9.2592593e-005', 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')
    arcpy.env.extent = arcpy.Extent(dem.extent.XMin,dem.extent.YMin,dem.extent.XMax,dem.extent.YMax)

    # Begin looping neighborhood analysis
    arcpy.AddMessage('First focal')
    OutRas = FocalStatistics(boundary, 'Circle 3 CELL', "MAXIMUM", "DATA")
    for i in range(3, i_count):
        arcpy.AddMessage('{}/{} Focal Iteration'.format(i,i_count-1))
        negihbor = 'Circle {} CELL'.format(i)
        OutRasTemp = FocalStatistics(boundary, negihbor, "MAXIMUM", "DATA")
        OutRas = Con(IsNull(OutRas), OutRasTemp, OutRas)
        del OutRasTemp
    OutRas.save('Focafin2m')

    # Subtract final neighborhood analysis output from clipping DEM
    waterDepth = Minus(OutRas, ClipDEM)
    waterDepth = Con(waterDepth < 0, 0, waterDepth)
    waterDepth.save('WaterDepth2m')

    # Gaussian filter the resulting water depth
    waterDepthFilter = Filter(waterDepth, "LOW", "DATA")
    waterDepthFilter.save('WaterDep2mf')
    arcpy.AddMessage('Done')

def CalculateBoundary(dem, InundPolygon,cellSize,WS, outputName):
    arcpy.PolygonToLine_management(InundPolygon, WS+'\polyline')
    arcpy.PolylineToRaster_conversion(WS+'\\polyline', 'OBJECTID', WS+'\linerast15', 'MAXIMUM_LENGTH', 'NONE', cellSize)
    arcpy.AddMessage('after polyline to raster')
    inRaster = Raster(WS+'\linerast15')
    inTrueRaster = dem
    inFalseConstant = '#'
    whereClause = "VALUE >= 0"
    arcpy.AddMessage('Con')
    boundary = Con(inRaster, inTrueRaster, inFalseConstant, whereClause)
    boundary.save(outputName)
    return outputName
main()


