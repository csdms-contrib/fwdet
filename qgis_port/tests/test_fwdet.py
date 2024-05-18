'''
Created on Oct. 17, 2023

@author: cefect
'''


import pytest, copy, os, gc
from qgis.core import (
    QgsRasterLayer, QgsProject,
    QgsProcessingOutputLayerDefinition, QgsApplication,
    QgsProcessingRegistry
    
    )

 
from qgis_port.processing_scripts.fwdet_21 import FwDET as AlgoClass


#===============================================================================
# FIXTURES------------
#===============================================================================

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


#===============================================================================
# TESTS-------------
#===============================================================================

def test_00_version(qgis_version):
    assert qgis_version==33405, 'bad version: %s'%qgis_version
    
    

def test_init(context, feedback):
        #execute
    algo=AlgoClass()
    algo.shortHelpString()
    algo.initAlgorithm()
    


def test_grass7_provider_available(qgis_app, qgis_processing):
    """Tests if the GRASS 7 processing provider is available in QGIS.
    
    problem with pytest-qgis?    
        https://github.com/GispoCoding/pytest-qgis/issues/65
        
        no.. just needed to add the grass paths
    """ 

    # Get the processing registry    
    registry = qgis_app.processingRegistry() 
 
    #===========================================================================
    # by providers
    #===========================================================================
    d = {k.id():k.name() for k in registry.providers()}
    
    assert 'grass7' in d.keys() #passes    
    
    #===========================================================================
    # # by algos
    #===========================================================================
    alg_d = {a.id():a.displayName() for a in registry.algorithms()}    
    
    grass_found=False
    for k,v in alg_d.items():
        #print(f'    {k},    {v}')
        if 'grass' in k:
            grass_found=True
            
    assert grass_found #fails
 
 
    assert 'grass7:r.neighbors' in alg_d.keys()

        

 

@pytest.mark.dev
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
                                    #0.5
                                    ])
def test_runner(
        INUN_LAYER, 
        INPUT_DEM_LAYER,   
        numIterations, slopeTH, caseName, grow_distance,
        output_params, context, feedback,
        qgis_app, qgis_processing #redundant w/ conftest.qproj?
        ):
    """test the main runner
    
    NOTE: wraps with '.Windows fatal exception: access violation'
    but test still passes
    
    """ 
 
    
    #execute
    algo=AlgoClass()
    algo.initAlgorithm()
    algo._init_algo(output_params, context, feedback)
    res_d = algo.run_algo(INPUT_DEM_LAYER, INUN_LAYER, numIterations, slopeTH, grow_distance)
     
    #validate
    assert isinstance(res_d, dict)
    assert set(res_d.keys()).symmetric_difference(output_params.keys())==set()
    
    #todo: add quantiative validation
    

