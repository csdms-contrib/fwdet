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
Created by Sagy Cohen, Surface Dynamics Modeling Lab, University of Alabama
email: sagy.cohen@ua.edu
web: http://sdml.ua.edu
"""
import arcpy
from arcpy.sa import *
# Checkout the Spatial Analyst Toolkit
arcpy.CheckOutExtension(['Spatial'])
arcpy.env.overwriteOutput = True

def main():
    ####################
    #   INPUT/OUTPUT   #
    ####################
    # Inputs#
    ws = arcpy.env.workspace = r'C:\Workspace\Boise\Geodatabase.gdb'
    dem_name = r'C:\Workspace\Boise\NEDelevation.tif'
    inund_polygon = r'C:\Workspace\Boise\WaterExtent.shp'

    clip_dem = '' #[Optional] - If empty, the clip_dem will be calculated with the Clip_management function
    cost_raster ='' #[Optional] - If empty, the CostRaster will be calculated below

    #Parameters#
    numIterations = 10 #number of smoothing iterations
    slopeTH = 0.5 #filtering slope threshold

    #Output# water depth raster
    Out_WaterDepth = 'WaterDepth'

    # Create raster object from DEM
    dem = arcpy.Raster(dem_name)
    # Check if optional Cost Raster was provided
    if not cost_raster:
        cost_raster = (((dem <= 0)*999)+1)
        cost_raster.save(ws + '\CostRaster')

    # Cell size here would be the x or y distance resolution from the raster
    # i.e., a 30 meter dem would have a cell size of 30
    cell_size = dem.meanCellHeight
    # Proper string representation of dem extent to be accepted by Clip_management method
    extent = '{} {} {} {}'.format(dem.extent.XMin, dem.extent.YMin, dem.extent.XMax, dem.extent.YMax)
    
    # If optional clip dem no provided then create a clipping dem cut out from the flood inundation polygon
    if not clip_dem:
        clip_dem = 'ClipDEM'
        arcpy.management.Clip(dem, extent, clip_dem, inund_polygon, nodata_value= "-9999", clipping_geometry="ClippingGeometry", maintain_clipping_extent="NO_MAINTAIN_EXTENT")
    clip_dem_ras = arcpy.Raster(clip_dem)
    # Generate raster line. See CalculateBoundary docstring for more info
    boundary = CalculateBoundary(dem, clip_dem_ras, inund_polygon, cell_size, numIterations, slopeTH)
    arcpy.AddMessage('Calculated Boundary')
   
 #   arcpy.env.extent = arcpy.Extent(dem.extent.XMin, dem.extent.YMin, dem.extent.XMax, dem.extent.YMax)
    # Convert boundary, i.e., raster line to int for cost allocation function. It only takes int rasters
    MULTIPLIER = 10000
    boundary_int = Int(boundary * MULTIPLIER)
    boundary_int.save("boundary_int")
    arcpy.AddMessage('Running cost allocation')
    with arcpy.EnvManager(snapRaster=None, extent="DEFAULT", mask=clip_dem):
      # cost_alloc = CostAllocation(boundary, cost_raster, '#', '#', 'Value')
        cost_alloc = CostAllocation(boundary_int, cost_raster, '#', '#', 'Value')
    
    # Divide the result from the cost allocation function using the same constant used to create the integer
    # representation of the boundary
    cost_alloc = Float(cost_alloc) / MULTIPLIER
    arcpy.AddMessage('Cost Allocation raster generated')
    arcpy.AddMessage('Calculating estimated water depth')
    # Raster calculator cost_alloc - clip_dem
    water_depth = (cost_alloc - clip_dem_ras)
    
    # Remove estimated water depths below 0 and change them to 0
    #water_depth = Con(water_depth <= 0, 0, water_depth)
    water_depth = Con(water_depth > 0, water_depth,"#")
    water_depth.save(Out_WaterDepth)
    arcpy.AddMessage('Floodwater depth computed')
    #Run a low-pass filter
    arcpy.AddMessage('Running low-pass Filter')
    water_depth_filtered = Filter(water_depth, 'LOW', 'DATA')
    waterDepthFilter2 = Con(clip_dem_ras, water_depth_filtered, '#', 'VALUE > 0')
    waterDepthFilter2.save(Out_WaterDepth+'_filtered')
    
def CalculateBoundary(dem, clip_dem_ras, inund_polygon, cell_size,numIterations,slopeTH):
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
    Return:
        str of raster line
    """
    arcpy.AddMessage('Converting inundation polygon to inundation polyline')
    # Convert inundation extent polygon to polyline
    polyline = 'polyline'
    arcpy.PolygonToLine_management(inund_polygon, polyline)
    arcpy.AddMessage('Converting inundation polyline to raster')
    # Convert polyline to raster
    with arcpy.EnvManager(snapRaster=clip_dem_ras):
        arcpy.conversion.PolylineToRaster(polyline, 'OBJECTID', 'linerast15', "MAXIMUM_LENGTH", "NONE", cell_size)
    raster_polyline = Raster('linerast15')
    raster_polyline.save("raster_polylin")
    # The input whose values will be used as the output cell values if the condition is false.
    inFalseConstant = '#'
    where_clause = 'VALUE >= 0'
    #Extract the boundary cells elevation from DEM
    boundary = Con(raster_polyline, dem, inFalseConstant, where_clause)
   # boundary.save('boundary1')
    #Smooth boundary raster
    iterations = int(numIterations)
    for i in range(iterations):
        arcpy.AddMessage('Focal iteration '+str(i+1))
        OutRasTemp = FocalStatistics(boundary, "Rectangle 5 5 CELL", 'MEAN', 'DATA')
        boundary = Con(raster_polyline, OutRasTemp, inFalseConstant, where_clause)
        boundary.save('boundary'+str(i+1))
    #Identify and remove ocean boundary cells
    OutRasTemp = FocalStatistics(dem, 'Circle 2 CELL', 'MINIMUM', 'DATA') 
    whereClause2 = 'VALUE > 0'
    boundary = Con(OutRasTemp, boundary, inFalseConstant, whereClause2)
    boundary.save("boundaryAfterOcean")
    if slopeTH>0.0:
    #calculate topo slope
        arcpy.AddMessage('Calculating Slope')
        extent_clip = '{} {} {} {}'.format(boundary.extent.XMin, boundary.extent.YMin, boundary.extent.XMax, boundary.extent.YMax)
        with arcpy.EnvManager(extent=extent_clip):
            out_slope = arcpy.sa.Slope(dem, "PERCENT_RISE", 1, "GEODESIC", "METER")
            out_slope.save("Slope_m")
    #Remove erroneous boundary cells 
        whereClause_slope = 'VALUE > ' + str(slopeTH)
        #boundary = arcpy.sa.Con(out_slope, boundary, None, "VALUE > 1.0")
        boundary = Con(out_slope, boundary, inFalseConstant, whereClause_slope)
  
    boundary.save("boundFinal")
    # Removing created eronious generated objects
   # arcpy.Delete_management(raster_polyline)
   # arcpy.Delete_management(polyline)
    return boundary
main()
