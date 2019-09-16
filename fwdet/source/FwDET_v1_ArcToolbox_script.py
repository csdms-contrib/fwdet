import arcpy
from arcpy.sa import *
import arcgisscripting
import os

script = arcgisscripting.create(9.3)

def main():
    """
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
    """

    ####################
    #   INPUT/OUTPUT   #
    ####################

    WS = arcpy.env.workspace = script.GetParameterAsText(0)
    arcpy.env.scratchWorkspace = script.GetParameterAsText(0)
    DEMname = os.path.basename(script.GetParameterAsText(1))
    InundPolygon = os.path.basename(script.GetParameterAsText(2))
    i_count = int(script.GetParameterAsText(3))
    ClipDEM = script.GetParameterAsText(4) if script.GetParameterAsText(4) else 'ClipDEM'
    dem = arcpy.Raster(DEMname)

    ####################
    # END INPUT/OUTPUT #
    ####################

    # Parameter and Environment initialization
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True


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


def CalculateBoundary(dem, inund_polygon, cell_size, ws):
    """
    Return a raster line representation with associated underlying DEM values as the values.

    Take in a inundated flood polygon, create a polyline representation of the input inundation_polygon.
    Next, convert flood polygon polyline calculated in the first step to a raster.
    Then, set values of newly created 'raster line' to the underlying dem values.
    Finally, save the raster line to the workspace

    Much of the naming conventions found in this function follow the arcpy documentation for the 'Con' function.

    Input:
        dem -> ArcPy raster object
        inundation_polygon -> str
        cell_size -> int
        ws -> str

    Return:
        str of raster line
    """

    print('Converting inundation polygon to inundation polyline')

    # Convert inundation extent polygon to polyline
    arcpy.PolygonToLine_management(inund_polygon, ws + '\polyline')

    print('Converting inundation polyline to raster')

    # Convert polyline to raster
    arcpy.PolylineToRaster_conversion(ws + '\\polyline', 'OBJECTID', ws + '\linerast15',
                                      'MAXIMUM_LENGTH', 'NONE', cell_size)

    raster_polyline = Raster(ws+'\linerast15')

    # The input whose values will be used as the output cell values if the condition is false.
    input_false_constant = '#'

    where_clause = 'VALUE >= 0'

    # Extract the boundary cells elevation from DEM
    boundary = Con(raster_polyline, dem, input_false_constant, where_clause)

    # TODO: Ask Cohen about this and its purpose
    # Minimum neighborhood analysis
    OutRasTemp = FocalStatistics(dem, 'Circle 2 CELL', 'MINIMUM', 'DATA')
    OutRasTemp.save('BoundaryFocal_circ2')

    where_clause = 'VALUE > 0'
    boundary = Con(OutRasTemp, boundary, input_false_constant, where_clause)
    boundary.save('boundary_elev')
    return boundary


main()


