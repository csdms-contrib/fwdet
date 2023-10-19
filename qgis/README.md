# Floodwater Depth Estimation Tool (FwDET) QGIS Processing Script

A QGIS Processing script to implement FwDET v2.1

The algorithms are tested against QGIS 3.28.11 and require [WhiteboxTools for QGIS plugin](https://www.whiteboxgeo.com/manual/wbt_book/qgis_plugin.html).

## 1 Installation Instructions

### download the scripts
download the algorithms of interest from the [processing folder](floodrescaler/processing) to your local machine

### add to your QGIS profile
In the QGIS [Processing Toolbox](https://docs.qgis.org/3.22/en/docs/user_manual/processing/toolbox.html#the-toolbox), select the python icon drop down ![Scripts](/assets/mIconPythonFile.png) , and `Add Script to Toolbox...`. This should load new algorithms to the `Scripts/FloodRescaling` group on the Processing Toolbox as shown below:

![screen capture](/assets/processingToolbox_screengrab.png)

### install and configure WhiteboxTools
Ensure the [WhiteboxTools for QGIS plugin](https://www.whiteboxgeo.com/manual/wbt_book/qgis_plugin.html) is installed and configured. 
Note this is only required for the Downscaling/CostGrow algo. 

## 2 Use
Instructions are provided on the algorithm dialog

## 3 Example Data

Example data is provided in the [examples](/examples) folder

 

## 5 Development

create a virtual environment from the supported QGIS version and the `./requirements.txt` file. 

add a ./definitions.py file similar to the below:

```
import pathlib, os
src_dir = os.path.dirname(os.path.abspath(__file__))

wrk_dir = os.path.expanduser('~')

#add your WhiteBoxTools executable file
wbt_exe = r'l:\06_SOFT\whitebox\v2.2.0\whitebox_tools.exe'
```
