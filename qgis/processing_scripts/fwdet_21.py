# -*- coding: utf-8 -*-

"""
2023-10-19 created by Seth Bryant 
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import pprint, os, datetime, tempfile
from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException, #still works
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsRasterLayer ,
                       QgsCoordinateTransformContext,
                       QgsMapLayerStore,
                       QgsProcessingOutputLayerDefinition,
                       QgsProject,
                       QgsProcessingParameterFeatureSource,
                       QgsVectorLayer,
 
                       )

from qgis.analysis import QgsNativeAlgorithms, QgsRasterCalculatorEntry, QgsRasterCalculator

import pandas as pd
 
class FwDET(QgsProcessingAlgorithm):
    """FwDET QGIS port from ArcMap script ./FwDET_2p1_Standalone.py
    """
 
    #input layers
    INPUT_DEM = 'INPUT_DEM'
    INUN_VLAY = 'INUN_VLAY'
    
    #input parameters
    numIterations = 'smooth_iters' #number of smoothing iterations
    slopeTH = 'slope_thresh' #filtering slope threshold
 
    #outputs
    OUTPUT_WSH = 'OUTPUT_WaterDepth'
 
 
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FwDET()

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
        return self.tr('Floodwater Depth Estimation Tool (FwDET)')

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
        return self.tr(
            """Floodwater Depth Estimation Tool (FwDET) 2.1 after Cohen et al. (2022) [10.3390/rs14215313].
             calculates floodwater depths using a digital elevation model (DEM) and a flood extentpolygon shapefile.
            """)

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        #=======================================================================
        # control
        #=======================================================================
 

        #=======================================================================
        # INPUTS-----------
        #=======================================================================
        #=======================================================================
        # raster layers
        #=======================================================================
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_DEM, self.tr('Terrain Raster (DEM)'))
        )
        
 

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INUN_VLAY,self.tr('Inundation Polygon'),
                                                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
 
        
        #=======================================================================
        # pars
        #======================================================================= 
        
        #add parameters
        param = QgsProcessingParameterNumber(self.numIterations, 'Number of Smoothing Iterations', 
                                             type=QgsProcessingParameterNumber.Integer, minValue=0)
        self.addParameter(param)
        
        
        param = QgsProcessingParameterNumber(self.slopeTH, 'Slope Threshold (percent)', 
                                             type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=100)
        self.addParameter(param)
 
 
        #=======================================================================
        # OUTPUTS
        #======================================================================= 
       
   
        self.addParameter(
            QgsProcessingParameterRasterDestination(self.OUTPUT_WSH, self.tr('Water Depths Output'))
        )
        
        


    def processAlgorithm(self, params, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        #=======================================================================
        # defaults
        #=======================================================================
        feedback.pushInfo('starting w/ \n%s'%(pprint.pformat(params, width=30)))
        
        self._init_algo(params, context, feedback)
        
        #=======================================================================
        # retrieve inputs---
        #=======================================================================
        #=======================================================================
        # layers
        #=======================================================================
        def get_rlay(attn):
            """load a raster layer and do some checks"""
            inrlay =  self.parameterAsRasterLayer(params, getattr(self, attn), context)
            if not isinstance(inrlay, QgsRasterLayer):
                raise QgsProcessingException(f'bad type on {attn}')            
 
            return inrlay                
 
 
        input_dem = get_rlay(self.INPUT_DEM)
 
        inun_vlay = self.parameterAsSource(params, self.INUN_VLAY, context)
        if not isinstance(inun_vlay, QgsVectorLayer):
            raise QgsProcessingException(f'bad type on {self.INUN_VLAY}')
        
 
        feedback.pushInfo('finished loading raster layers')
        
        #=======================================================================
        # params
        #=======================================================================
        numIterations = self.parameterAsInt(params, self.numIterations,context)
        slopeTH = self.parameterAsDouble(params, self.slopeTH, context)
        
 
 
        
        feedback.pushInfo(f'running with \'{inun_vlay.name()}\'') 
        
        if feedback.isCanceled():
            return {}
        #=======================================================================
        # exceute specified method----
        #=======================================================================.
 
 
        return self.run_algo(input_dem, inun_vlay, numIterations, slopeTH)
        
    def _init_algo(self, params, context, feedback):
        """common init for tests"""
        self.proc_kwargs = dict(feedback=feedback, context=context, is_child_algorithm=True)
        self.context, self.feedback, self.params = context, feedback, params
        
        
    def run_algo(self, dem_rlay, inun_vlay, numIterations, slopeTH,
                 cost_raster=None,):
        """main runner
        
        Params
        ------------
        cost_raster: QgsRasterLayer, optional
            cost surface. if not provided, all 1s where DEM>0
        """
        feedback=self.feedback
        
        feedback.pushInfo(f'on {inun_vlay.name()}')
        
        #=======================================================================
        # pre-check
        #=======================================================================
        
        for feature in inun_vlay.getFeatures():
            geom = feature.geometry()
            if not geom.isGeosValid():
                """better to let the user fix this first as the fix method may produce unexpected results"""
                raise IOError(f'passed inundation polygon layer \'{inun_vlay.name()}\''+\
                               'has invalid geometries. try \'Fix Geometries\'?')
        
 
        
        #=======================================================================
        # cost surface
        #=======================================================================
        if cost_raster is None:
            feedback.pushInfo(f'no cost raster provided... computing from DEM > 0')
            cost_fp = self._gdal_calc({'FORMULA':'A > 0', 'INPUT_A':dem_rlay, 'BAND_A':1, 'NO_DATA':0.0,
                             'RTYPE':5, 'OUTPUT':'TEMPORARY_OUTPUT'})
            
            cost_raster = QgsRasterLayer(cost_fp, 'cost_raster')
        
        #=======================================================================
        # clip
        #=======================================================================
        #TODO
        
        #=======================================================================
        # Beach Line
        #=======================================================================
        self.CalculateBoundary(dem_rlay,inun_vlay, numIterations, slopeTH)
        
        


                            

    def CalculateBoundary(self, dem_rlay, inun_vlay, numIterations, slopeTH,
                          neighborhood_size=5,
                          ):
        """beach line ops
        
        TODO: add some pre-clipping
        
        Params
        ---------
        neighborhood_size: int
            size of neighbourhood for smoothing kernal
        """
        feedback=self.feedback
        
        #=======================================================================
        # rastesrize inundatin boundary
        #=======================================================================
        feedback.pushInfo(f'rasterizing inundation boundary\n\n')
        #convert polygons to lines
        polyline = self._algo('native:polygonstolines', 
                                  {'INPUT':inun_vlay, 'OUTPUT':tfp('.gpkg')})['OUTPUT']
                                  
        #rasterize        
        raster_polyline = self._algo('gdal:rasterize', 
                   { 'BURN' : 1, 'DATA_TYPE' : 5, 
                    'EXTENT' : get_extent_str(dem_rlay),
                    #'EXTENT':'-80.118404571,-79.972518169,35.048219968,35.201742050 [EPSG:4326]', 
                    'EXTRA' : '', 'FIELD' : '', 'INIT' : None, 
                    'INPUT' :polyline, 'INVERT' : False,'NODATA' : 0, 'OPTIONS' : '', 
                    'OUTPUT' : 'TEMPORARY_OUTPUT',  'USE_Z' : False, 
                    'UNITS' : 0,#pixels 
                    'WIDTH' : dem_rlay.width(),  'HEIGHT' : dem_rlay.height(),}
                   )['OUTPUT']
                   
 
        #=======================================================================
        # extract beach values
        #=======================================================================
        feedback.pushInfo(f'sampling DEM values from beach line\n\n')
        boundary_fp = self._gdal_calc({'FORMULA':'(B > 0)*A', 
                         'INPUT_A':dem_rlay, 'BAND_A':1, 
                         'INPUT_B':raster_polyline, 'BAND_B':1,
                         'NO_DATA':0.0,'RTYPE':5, 'OUTPUT':'TEMPORARY_OUTPUT'})
        
        #=======================================================================
        # smooth beach values
        #=======================================================================
        feedback.pushInfo(f'smoothing beach values w/ {numIterations} iterations\n\n')
        boundary_fp_i = boundary_fp
        for i in range(numIterations):
            feedback.pushInfo(f'    {i+1}/{numIterations} smoothing')
            #compute 5x5 neighbour
            neigh_fp = self._r_neighbors(boundary_fp_i, neighborhood_size=neighborhood_size)
            
            #re-mask to input
            boundary_fp_i = self._gdal_calc_mask_apply(neigh_fp, raster_polyline)
            feedback.pushInfo(f'    finished smoothing w/ {boundary_fp_i}')
 
        #=======================================================================
        # handle ocean boundary
        #=======================================================================
        """consider adding an option to skip this 
        doesnt do anything if there are no negative DEM values in the beach line"""
        feedback.pushInfo(f'removing ocean boundary\n\n')
        #'fuzzy' nearest neighbour lowering of the DEM
        dem_min_fp = self._r_neighbors(dem_rlay, neighborhood_size=neighborhood_size,
                          circular=True, method='minimum')
        
        #mask out any negatives from the boundary
        boundary1_fp = self._gdal_calc({'FORMULA':'A*(B > 0)', 
                                'INPUT_A':boundary_fp_i, 'BAND_A':1, 'INPUT_B':dem_min_fp, 'BAND_B':1,
                                'NO_DATA':0.0,'OUTPUT':'TEMPORARY_OUTPUT', 'RTYPE':5})
        
        boundary1 = QgsRasterLayer(boundary1_fp, 'boundary1')
 
        #=======================================================================
        # slope filter
        #=======================================================================
        if slopeTH>0.0:
            feedback.pushInfo(f'applying slope filtering w/ threshold={slopeTH} \n\n')
            
            #clip DEM raster
            #TODO: fix clipping
            dem_rlay_c = self._algo('gdal:cliprasterbyextent', 
                       { 'DATA_TYPE' : 0, 'EXTRA' : '', 
                        'INPUT' : dem_rlay, 'NODATA' : -9999, 
                        'OUTPUT' : 'TEMPORARY_OUTPUT', 'OVERCRS' : False, 
                        'PROJWIN' : get_extent_str(inun_vlay) })['OUTPUT']
                        
            #clip boundary
            boundary1_fp_c = self._algo('gdal:cliprasterbyextent', 
                       { 'DATA_TYPE' : 0, 'EXTRA' : '', 
                        'INPUT' : boundary1_fp, 'NODATA' : -9999, 
                        'OUTPUT' : 'TEMPORARY_OUTPUT', 'OVERCRS' : False, 
                        'PROJWIN' : get_extent_str(inun_vlay) })['OUTPUT']
                        
            #compute slope
            #doesnt seem to work... maybe crs problem?
            #===================================================================
            # slope_fp = self._algo('gdal:slope', 
            #            { 'AS_PERCENT' : True, 'BAND' : 1, 'COMPUTE_EDGES' : False, 
            #             'EXTRA' : '', 'INPUT' :dem_rlay_c,
            #             'OPTIONS' : '', 'OUTPUT' : 'TEMPORARY_OUTPUT', 'SCALE' : 1, 'ZEVENBERGEN' : False }
            #            )['OUTPUT']
            #===================================================================
            #ranges from 0-76 for test
            slope_fp = self._algo('grass7:r.slope.aspect', 
                       { '-a' : True, '-e' : False, '-n' : False, 
                        'GRASS_RASTER_FORMAT_META' : '', 'GRASS_RASTER_FORMAT_OPT' : '', 
                        'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 'GRASS_REGION_PARAMETER' : None, 
                        'elevation' : dem_rlay_c, 
                        'format' : 1, 'min_slope' : 0, 'precision' : 0, 'slope' : 'TEMPORARY_OUTPUT', 
                        'zscale' : 1 })['slope']
                       
            #apply filter
            boundary2 = self._gdal_calc({'FORMULA':f'B*(A > {slopeTH})', 
                                'INPUT_A':slope_fp, 'BAND_A':1, 
                                'INPUT_B':boundary1_fp_c, 'BAND_B':1,
                                'NO_DATA':0.0,'OUTPUT':'TEMPORARY_OUTPUT', 'RTYPE':5})
            
        else:
            boundary2=boundary1
            
        feedback.pushInfo(f'finished constructing boundary beach raster\n    {boundary2} \n\n')
        
        return boundary2
                   
                   
        
    def _get_out(self, attn):
        return self.parameterAsOutputLayer(self.params, getattr(self, attn), self.context)
        
  
    def _gdal_calc(self, pars_d):
        """Raster calculator (gdal:rastercalculator)
        - 0: Byte
        - 1: Int16
        - 2: UInt16
        - 3: UInt32
        - 4: Int32
        - 5: Float32
        - 6: Float64
        """
 
        ofp =  processing.run('gdal:rastercalculator', pars_d, **self.proc_kwargs)['OUTPUT']
        
        if not os.path.exists(ofp):
            raise QgsProcessingException('gdal:rastercalculator failed to get a result for \n%s'%pars_d['FORMULA'])
        
        return ofp
    
    def _gdal_calc_mask_apply(self, rlay, mask, OUTPUT='TEMPORARY_OUTPUT'):
        return self._gdal_calc({'FORMULA':'A*B', 
                                'INPUT_A':rlay, 'BAND_A':1, 'INPUT_B':mask, 'BAND_B':1,
                                'NO_DATA':-9999,'OUTPUT':OUTPUT, 'RTYPE':5})
    
    
    def _gdal_calc_mask(self, rlay, OUTPUT='TEMPORARY_OUTPUT'):
        return self._gdal_calc({'FORMULA':'A/A', 'INPUT_A':rlay, 'BAND_A':1,'NO_DATA':-9999,'OUTPUT':OUTPUT, 'RTYPE':5})
    
    def _r_neighbors(self, input_rlay, 
                     neighborhood_size=5,
                     method='average',
                     output='TEMPORARY_OUTPUT',
                     circular=False,
                     ):
 
        return self._algo('grass7:r.neighbors', 
                          {'-a':False, '-c':circular, #Use circular neighborhood
                            'GRASS_REGION_CELLSIZE_PARAMETER':0, 'GRASS_REGION_PARAMETER':None, 
                            'gauss':None, 
                            'input':input_rlay, 
                            'method':{'average':0, 'minimum':3}[method], 
                            'output':output, 'selection':None, 
                            'size':neighborhood_size})['output']
    
    def _algo(self, algoName, pars_d):
        return processing.run(algoName, pars_d, **self.proc_kwargs)
        
 

    
#===============================================================================
# HELPERS----------
#===============================================================================
"""cant do imports without creating a provider and a plugin"""


        
def now():
    return datetime.datetime.now()

def tfp(suffix='.tif'):
    return tempfile.NamedTemporaryFile(suffix=suffix).name

def get_resolution_ratio( 
                             rlay_s1, #fine
                             rlay_s2, #coarse
                             ):
        
        
    s1 = rlay_get_resolution(rlay_s1)
    s2 = rlay_get_resolution(rlay_s2)
    assert (s2/ s1)>=1.0
    return s2 / s1

def rlay_get_resolution(rlay):
    
    return (rlay.rasterUnitsPerPixelY() + rlay.rasterUnitsPerPixelX())*0.5

def assert_extent_equal(left, right, msg='',): 
    """ extents check"""
 
    assert isinstance(left, QgsRasterLayer), type(left).__name__+ '\n'+msg
    assert isinstance(right, QgsRasterLayer), type(right).__name__+ '\n'+msg
    __tracebackhide__ = True
    
    #===========================================================================
    # crs
    #===========================================================================
    if not left.crs()==right.crs():
        raise QgsProcessingException('crs mismatch')
    #===========================================================================
    # extents
    #===========================================================================
    if not left.extent()==right.extent():
        raise QgsProcessingException('%s != %s extent\n    %s != %s\n    '%(
                left.name(),   right.name(), left.extent(), right.extent()) +msg) 


def get_extent_str(layer):
    rect = layer.extent()
    return '%.8f,%.8f,%.8f,%.8f [%s]'%(
            rect.xMinimum(),  rect.xMaximum(),rect.yMinimum(), rect.yMaximum(),
            layer.crs().authid())
