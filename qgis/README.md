# Floodwater Depth Estimation Tool (FwDET) QGIS Processing Script

A QGIS Processing script to implement FwDET v2.1

Tested against QGIS 3.28.11

## 1 Installation Instructions

### Install QGIS with GRASS
download and install the QGIS version shown above (other versions may also work) and ensure you have the GRASS processing provider enabled. 

### download the scripts
download [processing_scripts/fwdet_21.py](./qgis/processing_scripts/fwdet_21.py) script to your local machine

### add to your QGIS profile
In the QGIS [Processing Toolbox](https://docs.qgis.org/3.22/en/docs/user_manual/processing/toolbox.html#the-toolbox), select the python icon drop down ![Scripts](/qgis/assets/mIconPythonFile.png) , and `Add Script to Toolbox...` then point to the downloaded script. This should load new algorithms to the `Scripts/FwDET` group on the Processing Toolbox.

## 2 Use
Instructions are provided on the algorithm dialog

## 3 Example Data
Example DEM and inundation polygon are provided in the [test_case\PeeDee](/test_case/PeeDee) folder (see [Issue #12](https://github.com/csdms-contrib/fwdet/issues/12)).
 

## 5 Development
create a virtual environment from the supported QGIS version and the `./requirements.txt` file. 

add a ./definitions.py file similar to the below:

```
import pathlib, os

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

wrk_dir = os.path.expanduser('~')
```

## 6 Known Issues and Limitations

- verify that the filtering/smoothing operations match the ArcPy  equivalents
- could not find a QGIS pre-installed equivalent to ArcPy's CostAllocation. Instead, we use `grass7:r.grow.distance` which provides a similar result with a neutral cost surface. This is also quite slow. A better alternative would use WhiteBoxTools; however, this adds a dependency. 
- the algorithm is sensitive to tiny holes in the inundation polygon.  These could be fixed through pre-processing to remove small holes.
- did not test a coastal scenario
