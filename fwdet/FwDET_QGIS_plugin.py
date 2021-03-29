# -*- coding: utf-8 -*-

"""
License: GNU 2
Author: Austin Raney, Sagy Cohen
Contact: aaraney@crimson.ua.edu, sagy.cohen@ua.edu
"""

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsRaster,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsProject,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFolderDestination)
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
import processing
import os


class FWDET(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    DEM_INPUT = 'DEM_INPUT'
    FLOOD_POLYGON_INPUT = 'FLOOD_POLYGON_INPUT'
    FLOOD_DEPTH_OUTPUT = 'FLOOD_DEPTH_OUTPUT'
    # FLOOD_DEPTH_FILTERED_OUTPUT = 'FLOOD_DEPTH_FILTERED_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FWDET()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'fwdet'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('FwDET v1')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('FwDET')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'fwdet'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("""The Floodwater Depth Estimation Tool (FwDET) yields estimated flood water depth rasters by means of a digital elevation model (DEM) and flood extent shapefile. This tool is best\
            suited for inland riverine flooding events. More information about the methodology behind the tool can be found <a href="https://onlinelibrary.wiley.com/doi/full/10.1111/1752-1688.12609">here</a>.
            Source code for the tool can be found on the <a href="https://github.com/csdms-contrib/fwdet"> github</a>. \n Code Contributors: Austin Raney (<a href="mailto:aaraney@crimson.ua.edu">aaraney@crimson.ua.edu</a>), 
            Dr. Sagy Cohen (<a href="mailto:sagy.cohen@ua.edu">sagy.cohen@ua.edu</a>) \n Checkout sdml's <a href="http://sdml.ua.edu/usfimr">U.S. Flood Inundation Repository</a> for potential test cases or study areas!""")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FLOOD_POLYGON_INPUT,
                self.tr('Flood Extent')
                # [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM_INPUT,
                self.tr('Digital Elevation Model')
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.FLOOD_DEPTH_OUTPUT,
                self.tr('Output Directory')
            )
        )

        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         self.FLOOD_DEPTH_FILTERED_OUTPUT,
        #         self.tr('Gaussian Filtered Flood Water Depth Output')
        #     )
        # )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # Retrieve parameters from the gui
        OUTPUTFOLDER = self.parameterAsFile(parameters, self.FLOOD_DEPTH_OUTPUT, context)

        if parameters["FLOOD_DEPTH_OUTPUT"] == "TEMPORARY_OUTPUT":
            OUTPUTFOLDER = os.path.dirname(OUTPUTFOLDER)

        DEM = self.parameterAsRasterLayer(parameters, self.DEM_INPUT, context).source()
        INUNDPOLYGON = self.parameterAsVectorLayer(parameters, self.FLOOD_POLYGON_INPUT, context).source()
        
        # feedback.pushInfo('The output directory is {}'.format(self.parameterAsFile(
            # parameters, self.FLOOD_DEPTH_OUTPUT, context)))
        feedback.pushInfo(DEM)

        # Raster specifications that are needed by JSON inputs
        # Load the DEM to extract the layer extent and pixel size
        demLayer = QgsRasterLayer(DEM, 'dem_extent')
        inundpolygonLayer = QgsVectorLayer(INUNDPOLYGON, 'indund_extent')

        # Extract the DEM extent in a float format. 
        demExtent = self.floatDemExtent(demLayer)
        inundpolygonExtent = self.floatDemExtent(inundpolygonLayer) 

        # It is assumed that the unit per pixel size for the X direction is the same for the Y direction
        demSize = demLayer.rasterUnitsPerPixelX()
        # End raster specifications that are needed by JSON inputs

        # JSON input setup
        clip_input = {
          "INPUT": DEM,
          "OUTPUT": os.path.join(OUTPUTFOLDER,'clippingMask.sdat'), # this will need to change
          "POLYGONS": INUNDPOLYGON
        }

        polygons_to_lines_input = {
          "LINES": os.path.join(OUTPUTFOLDER,'polyline.shp'),
          "POLYGONS":  INUNDPOLYGON 
        }

        rasterize_input = {'INPUT': os.path.join(OUTPUTFOLDER,'polyline.shp'),
                            'FIELD': None,
                            'BURN': 1,
                            'UNITS': 1,
                            # width and height should match that of the cell size of the DEM input
                            'WIDTH': demSize,
                            'HEIGHT': demSize,
                            # the extent of the area must be given in a comma seperated list
                            # ending with an uncommaed CRS within e.g. [EPSG:26712]
                            'EXTENT': inundpolygonExtent,
                            'NODATA': 0,
                            'OPTIONS': '',
                            'DATA_TYPE': 0,
                            'INIT': 0,
                            'INVERT': False,
                            'OUTPUT': os.path.join(OUTPUTFOLDER, 'rasterLine.tif')
                           }

        grow_distance_input = {'input': os.path.join(OUTPUTFOLDER, 'extractElevation.tif'),
                                # euclidean distance
                                'metric': 0,
                                '-m': False,
                                '-': False,
                                'distance': os.path.join(OUTPUTFOLDER,'scratch.tif'),
                                'value': os.path.join(OUTPUTFOLDER,'growDistance.tif'),
                                'GRASS_REGION_PARAMETER': demExtent,
                                'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                                'GRASS_RASTER_FORMAT_OPT': '',
                                'GRASS_RASTER_FORMAT_META': ''
                               }

        gaussian_filter_input = {'INPUT': os.path.join(OUTPUTFOLDER, 'waterDepth.tif'),
                                    'MODE': 0,
                                    'RADIUS': 3,
                                    'RESULT': os.path.join(OUTPUTFOLDER, 'waterDepthFiltered.sdat'),
                                    'SIGMA': 1
                                 }

        # End json input setup

        # create a clipping mask from the DEM to later be used to subtract from the calculated gross waterdepth
        processing.run("saga:cliprasterwithpolygon", clip_input, context=context, feedback=feedback)

        feedback.setProgress(12)

        # convert floodextent to polyline outline
        POLYLINE = processing.run("saga:convertpolygonstolines", polygons_to_lines_input,  context=context, feedback=feedback)['LINES']

        feedback.setProgress(24)

        polyLineExtent = self.floatDemExtent(QgsVectorLayer(POLYLINE, 'line_extent', 'ogr'))

        feedback.setProgress(36)

        # convert the above polyline to a raster line so that raster opperations may be preformed
        processing.run("gdal:rasterize", rasterize_input, context=context, feedback=feedback)

        feedback.setProgress(48)

        # associate underlying DEM values to rasterized line
        extractElevation = self.rasterCalculator([rasterize_input['OUTPUT'], DEM], '({0} * {1}) / {0}', 0, 'extractElevation.tif')

        feedback.setProgress(60)

        processing.run("grass7:r.grow.distance", grow_distance_input, context=context, feedback=feedback)

        feedback.setProgress(72)

        # clip grow distance output using clipDEM
        waterDepth = self.rasterCalculator([clip_input['OUTPUT'], grow_distance_input['value']],
                                           '(({1} - {0}) > 0) * ({1} - {0})', 0, fname='waterDepth.tif')
        feedback.setProgress(84)

        # filter inputs will need to change once gaussianfilter wrapper is updated to saga >= 4
        processing.run("saga:gaussianfilter", gaussian_filter_input, context=context, feedback=feedback)

        feedback.setProgress(100)

        return {'OUTPUT': os.path.join(OUTPUTFOLDER, 'waterDepthFiltered.sdat')}

    def floatDemExtent(self, QgsLayer):
        """
        This function takes in either and QgsRasterLayer or Vector layer and returns a string that
        contains both it's correctly formatted extent and crs. It was made to be used as input for
        qgis3 processing tools

        takes in QgsLayer so QgsRasterLayer(path,'name') or QgsVectorLayer(path,'name') and returns extent
        [xmin, xmax, ymin, ymax] in a string of .f4 float formated numbers
        """
        xm, xM, ym, yM = QgsLayer.extent().xMinimum(), QgsLayer.extent().xMaximum(), QgsLayer.extent().yMinimum(), QgsLayer.extent().yMaximum()
        crs = QgsLayer.crs().authid()
        del QgsLayer
        # 14 numbers after the dot making it much more accurate also, the crs was added for Qgis3 support
        return '{:.14f},{:.14f},{:.14f},{:.14f} [{}]'.format(xm, xM, ym, yM, crs)


    def rasterCalculator(self, layerPath, expression, extentPathIndex=0, fname=None):
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
