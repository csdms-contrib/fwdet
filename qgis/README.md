# Floodwater Depth Estimation Tool (FwDET) QGIS Processing Script

A QGIS Processing script to implement FwDET v2.1

Tested against QGIS 3.28.11

## 1 Installation Instructions

### download the scripts
download the algorithms of interest from the [processing_scripts folder](floodrescaler/processing_scripts) to your local machine

### add to your QGIS profile
In the QGIS [Processing Toolbox](https://docs.qgis.org/3.22/en/docs/user_manual/processing/toolbox.html#the-toolbox), select the python icon drop down ![Scripts](qgis/assets/mIconPythonFile.png) , and `Add Script to Toolbox...`. This should load new algorithms to the `Scripts/FwDET` group on the Processing Toolbox.


## 2 Use
Instructions are provided on the algorithm dialog

## 3 Example Data
Example DEM and inundation polygon is provided in the [test_case\PeeDee](test_case/PeeDee) folder
 

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
- could not find a QGIS pre-installed equivalent to ArcPy's CostAllocation. Instead, we use 'grass7:r.grow.distance' which provides a similar result with a neutral cost surface. This is also quite slow. A better alternative would use WhiteBoxTools; however, this adds a dependency. 
- the algorithim is sensitve to tiny holes in the inundation polygon.  These could be fixed through preprocessing to remove small holes.
- did not test a coastal scenario