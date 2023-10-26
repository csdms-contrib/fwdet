'''
Created on Oct. 17, 2023

@author: cefect
'''


import pytest, copy, os, gc
from qgis.core import (
    QgsRasterLayer, QgsProject,
    QgsProcessingOutputLayerDefinition, QgsApplication,
    
    )

 
from processing_scripts.fwdet_21 import FwDET as AlgoClass




@pytest.fixture(scope='function')
def output_params(qproj):
    """setting up default output parameters for tests"""    
    def get_out():
        return QgsProcessingOutputLayerDefinition(sink='TEMPORARY_OUTPUT', destinationProject=qproj)
    
    return {
        AlgoClass.OUTPUT_WSH:get_out(),
        AlgoClass.OUTPUT_SHORE:get_out(),
        AlgoClass.OUTPUT_WSH_SMOOTH:get_out(),
        
        }

@pytest.mark.dev
def test_init(context, feedback):
        #execute
    algo=AlgoClass()
    algo.shortHelpString()
    algo.initAlgorithm()
    

 
@pytest.mark.parametrize('caseName, grow_distance',[
    ('PeeDee','geodesic'),
    ('FtMac', 'euclidean'),
    ])
@pytest.mark.parametrize('numIterations',[
                                        0,
                                          1,
                                          #5
                                          ])
@pytest.mark.parametrize('slopeTH',[
                                    0, 
                                    0.5
                                    ])
def test_runner(
        INUN_VLAY, 
        INPUT_DEM,   
        numIterations, slopeTH, caseName, grow_distance,
        output_params, context, feedback,
        ):
    """test the main runner
    
    NOTE: wraps with '.Windows fatal exception: access violation'
    but test still passes
    
    """ 
 
    
    #execute
    algo=AlgoClass()
    algo.initAlgorithm()
    algo._init_algo(output_params, context, feedback)
    res_d = algo.run_algo(INPUT_DEM, INUN_VLAY, numIterations, slopeTH, grow_distance)
     
    #validate
    assert isinstance(res_d, dict)
    assert set(res_d.keys()).symmetric_difference(output_params.keys())==set()
    
    #todo: add quantiative validation
    

