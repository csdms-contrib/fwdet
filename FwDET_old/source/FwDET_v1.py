import arcpy
from arcpy.sa import *

def main(workspace_location, scratch_location, dem_name, inundation_polygon_name):
    """
    Floodwater Depth Estimation Tool (FwDET)

    Calculate water depth from a flood extent polygon (e.g. from remote sensing analysis) based on an underlying DEM.
    Program procedure:
    1. Flood extent polygon to polyline
    2. Polyline to Raster - DEM extent and resolution (Env)
    3. Con - DEM values to Raster
    4. Focal Statistics loop
    5. Water depth calculation - difference between Focal Statistics output and DEM

    See:
    Cohen, S., G. R. Brakenridge, A. Kettner, B. Bates, J. Nelson, R. McDonald, Y. Huang, D. Munasinghe, and J. Zhang (2017),
        Estimating Floodwater Depths from Flood Inundation Maps and Topography. Journal of the American Water Resources Association (JAWRA):1-12.

    Created by Sagy Cohen, Surface Dynamics Modeling Lab, University of Alabama
    email: sagy.cohen@ua.edu
    web: http://sdml.ua.edu
    June 30, 2016

    Updated by Austin Raney
    September 16, 2019

    Copyright (C) 2017 Sagy Cohen
    Developer can be contacted by sagy.cohen@ua.edu and Box 870322, Tuscaloosa AL 35487 USA
    This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public
    License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later
    version.
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
    details.
    You should have received a copy of the GNU General Public License along with this program; if not, write to the
    Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    """
    # Require an ArcGIS Spatial Analyst extension
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True

    # Location of workspace (preferably a GeoDatabase)
    WS = arcpy.env.workspace = r'{}'.format(workspace_location)

    # Location of the Scratch GeoDatabase (optional but highly recommended)
    arcpy.env.scratchWorkspace = r'{}'.format(scratch_location)

    # name of the input DEM (within the Workspace)
    DEMname = dem_name

    # Name of the input Inundation extent polygon layer (within the Workspace)
    InundPolygon = inundation_polygon_name

    # Name of the output clipped DEM (clipped by the inundation polygon extent)
    ClipDEM = 'dem_clip'

    dem = arcpy.Raster(DEMname)
    cellSize = dem.meanCellHeight
    boundary = CalculateBoundary(dem, InundPolygon, cellSize, WS)
    extent = str(dem.extent.XMin) + " " + str(dem.extent.YMin) + " " + str(dem.extent.XMax) + " " + str(dem.extent.YMax)
    print(extent)
    
    arcpy.Clip_management(DEMname, extent, ClipDEM, InundPolygon, cellSize, 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')

    print(arcpy.GetMessages())

    arcpy.env.extent = arcpy.Extent(dem.extent.XMin,dem.extent.YMin,dem.extent.XMax,dem.extent.YMax)

    print('First focal ')
    OutRas = FocalStatistics(boundary, 'Circle 3 CELL', "MAXIMUM", "DATA")

    # Focal Statistics loop - Number of iteration will depend on the flood inundation extent and DEM resolution
    # TO CHANGE NUMBER OF FOCAL STATS ITERATIONS CHANGE VARIABLE ITER_NUM. NOTE, python's range function is an
    # exclusive range
    ITER_NUM = 50
    for i in range(3, 50):         
        print(i)
        negihbor = 'Circle ' + str(i) + ' CELL'
        OutRasTemp = FocalStatistics(boundary, negihbor, "MAXIMUM", "DATA")

        # Assure that only 'empty' (NoDATA) cells are assigned a value in each iteration
        OutRas = Con(IsNull(OutRas), OutRasTemp, OutRas)
    print('Focal loop done!')
   
    OutRas.save('Focafin10m') #name of output final focal statistics raster

    # Calculate floodwater depth
    waterDepth = Minus(OutRas, ClipDEM)
    waterDepth = Con(waterDepth < 0, 0, waterDepth)
    # name of output floodwater depth raster
    waterDepth.save('WaterDepth10m')
    waterDepthFilter = Filter(waterDepth, "LOW", "DATA")

    # name of output floodwater depth raster after low-pass filter
    waterDepthFilter.save('WaterDep10mf')

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

    raster_polyline = Raster(ws + '\linerast15')

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


if __name__ == '__main__':
    main('Lyons.gdb', 'Scratch.gdb', 'Elevation', 'FloodExtent')
