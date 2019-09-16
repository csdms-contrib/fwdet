import arcpy
import arcgisscripting
from arcpy.sa import *
import timeit
import os

# From p. 281 of python scripting for ArcGis
script = arcgisscripting.create(9.3)

start = timeit.default_timer()


def main():
    """
    Calculate water depth from a flood extent polygon (e.g. from remote sensing analysis) based on
    an underlying DEM (or HAND).

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
    """
    ####################
    #   INPUT/OUTPUT   #
    ####################

    # Set the Workspace and Scratch space to the first param provided
    ws = arcpy.env.workspace = script.GetParameterAsText(0)
    arcpy.env.scratchWorkspace = script.GetParameterAsText(0)

    # Set Input DEM, Inundation Polygon.
    dem_name = os.path.basename(script.GetParameterAsText(2))

    # Create raster object from DEM
    dem = arcpy.Raster(dem_name)

    inund_polygon = os.path.basename(script.GetParameterAsText(1))

    # If this is not provided, the clip_dem will be calculated with the Clip_management function
    clip_dem = script.GetParameterAsText(4)

    # Check if optional Cost Raster was provided
    if script.GetParameterAsText(5):
        cost_raster = script.GetParameterAsText(5)
    else:
        cost_raster = (((dem <= 0)*999)+1)
        cost_raster.save(ws + '\cost_raster')

    ####################
    # END INPUT/OUTPUT #
    ####################

    # Checkout the Spatial Analyst Toolkit
    arcpy.CheckOutExtension('Spatial')

    # Set overriding within the Workspace to True
    arcpy.env.overwriteOutput = True

    # Cell size here would be the x or y distance resolution from the raster
    # i.e., a 30 meter dem would have a cell size of 30
    cell_size = dem.meanCellHeight

    # Generate raster line. See CalculateBoundary docstring for more info
    boundary = CalculateBoundary(dem, inund_polygon, cell_size, ws)

    # Proper string representation of dem extent to be accepted by Clip_management method
    extent = '{} {} {} {}'.format(dem.extent.XMin, dem.extent.YMin, dem.extent.XMax, dem.extent.YMax)

    # If optional clip dem no provided then create a clipping dem cut out from the flood inundation polygon
    if not clip_dem:
        clip_dem = 'Clip_DEM'
        arcpy.Clip_management(dem_name, extent, clip_dem, inund_polygon,
                              cell_size, 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')

    arcpy.env.extent = arcpy.Extent(dem.extent.XMin, dem.extent.YMin, dem.extent.XMax, dem.extent.YMax)

    print('Convert boundary to integer')

    # Must convert boundary, i.e., raster line to int for cost allocation function. It only takes int rasters
    MULTIPLIER = 10000
    boundary_int = Int(boundary * MULTIPLIER)
    boundary_int.save('boundary_int')

    print('Running cost allocation')
    cost_alloc = CostAllocation(boundary_int, cost_raster, '#', '#', 'Value')
    cost_alloc.save('CostAlloc_int')

    # Divide the result from the cost allocation function using the same constant used to create the integer
    # representation of the boundary
    cost_alloc = Float(cost_alloc) / MULTIPLIER
    cost_alloc.save('cost_alloc')

    print('Calculating estimated water depth')

    # Raster calculator cost_alloc - clip_dem
    water_depth = Minus(cost_alloc, clip_dem)

    # Remove estimated water depths below 0 and change them to 0
    water_depth = Con(water_depth <= 0, 0, water_depth)
    water_depth.save(os.path.basename(script.GetParameterAsText(3)))

    print('Calculating low pass filter')

    water_depth_filtered = Filter(water_depth, 'LOW', 'DATA')

    waterDepthFilter2 = Con(clip_dem, water_depth_filtered, '#', 'VALUE > 0')
    waterDepthFilter2.save(os.path.basename(script.GetParameterAsText(3))+'_filtered')
    print('Done')


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

    # TODO: Can this be removed?
    # inTrueRaster = dem

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

stop = timeit.default_timer()
print('start: ', start, '\n')
print('End: ', stop, '\n')
print('Run time: ', (stop - start)/60, 'min')
