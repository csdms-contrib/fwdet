'''
Created on Oct. 24, 2022

@author: cefect
'''
#===============================================================================
# IMPORTS------
#===============================================================================
import os, pathlib, pytest, logging, sys
from pytest_qgis.utils import clean_qgis_layer
from qgis.core import (
    QgsRasterLayer, QgsProject, QgsProcessingFeedback, QgsProcessingContext, Qgis, 
    QgsSettings, QgsApplication, QgsVectorLayer,
    )

print(u'QGIS version: %s, release: %s'%(Qgis.QGIS_VERSION.encode('utf-8'), Qgis.QGIS_RELEASE_NAME.encode('utf-8')))
 
from definitions import src_dir

test_data_dir = os.path.join(src_dir, 'test_case')

assert os.path.exists(test_data_dir)

test_data_lib = {
    'PeeDee':{
        'INUN_VLAY':'WaterExtent_fixed.gpkg',
        'INPUT_DEM':'NEDelevation.tif'
        
        }
    }

#===============================================================================
# helpers
#===============================================================================
 
def get_fp(caseName, layName):
    fname = test_data_lib[caseName][layName]
    fp = os.path.join(test_data_dir, caseName, fname)
    assert os.path.exists(fp), layName
    
    return fp


class MyFeedBackQ(QgsProcessingFeedback):
    """special feedback object for testing"""
    
    def __init__(self,logger, *args, **kwargs):        
        self.logger=logger.getChild('FeedBack')        
        super().__init__(*args, **kwargs)
        
    def pushInfo(self, info):
        self.logger.info(info)
        
    def pushDebugInfo(self, info):
        self.logger.debug(info)
    
#===============================================================================
# fixtures
#===============================================================================

@pytest.fixture(scope='session')
def logger():
    logging.basicConfig(
                #filename='xCurve.log', #basicConfig can only do file or stream
                force=True, #overwrite root handlers
                stream=sys.stdout, #send to stdout (supports colors)
                level=logging.INFO, #lowest level to display
                )
    
    return logging.getLogger('r')
    


@pytest.fixture(scope='session')
def qproj(qgis_app, qgis_processing):
    

    

    
    #===========================================================================
    # searchTerm='wbt'
    # for alg in qgis_app.processingRegistry().algorithms():
    #     if searchTerm in alg.id() or searchTerm in alg.displayName():
    #         print(alg.id(), "->", alg.displayName())
    #===========================================================================
    """
    from qgis import processing
    
    processing.run('wbt:ConvertNodataToZero', { 'input' : r'L:\09_REPOS\03_TOOLS\FloodRescaler\examples\Ahr2021\wse.tif', 'output' : 'TEMPORARY_OUTPUT' })
    """
 
    return QgsProject.instance()

@pytest.fixture(scope='session')
def feedback(qproj, logger):
    return MyFeedBackQ(logger, False)

@pytest.fixture(scope='session')
def context(qproj):
    return QgsProcessingContext()
 
@pytest.fixture(scope='function')
@clean_qgis_layer
def INUN_VLAY(caseName, qproj):
    fp =  get_fp(caseName, 'INUN_VLAY')
    return QgsVectorLayer(fp, 'INUN_VLAY', 'ogr')
 

@pytest.fixture(scope='function')
@clean_qgis_layer
def INPUT_DEM(caseName, qproj):
    fp =  get_fp(caseName, 'INPUT_DEM')
    return QgsRasterLayer(fp, 'INPUT_DEM')
 
    
 
    
