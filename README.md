# Updates:
Now supporting:
	- >= ArcGis 10.5
	- ArcGis Pro

# Floodwater Depth Estimation Tool
The Floodwater Depth Estimation Tool (FwDET) calculates floodwater
depths using a digital elevation model (DEM) and a flood extent
polygon shapefile. Within this repository resides the two versions of
FwDET. Version 1, featured in Estimating Floodwater Depths from Flood
Inundation Maps and Topography [Cohen et al. 2018], best works in
inland riverine regions and has been implemented using both Arcpy and
QGIS. Version 2, features an improved algorithm which better solves
coastal flooding as well as fluvial. Version 2 implements a much
different approach that is considerably more computationally
efficient, drastically reducing run time compared to version 1 of the
tool.

FwDET can be executed either as a standalone Python script or via a toolbox in
ArcMap (v1 & v2) or QGIS (v1). Version 1 and 2 have been implemented via Arcpy
scripts and Arc Toolboxs with version support for >= ArcGis 10.5 and ArcGis Pro.
Version 1 also has both a standalone and plugin open-source QGIS version, that
out preforms the ArcMap computationally. The plugin/toolbox versions can be
found inside the [fwdet](fwdet) directory. The standalone versions of the
scripts are located under [fwdet/source](fwdet/source).

## How to use FwDET ArcMap/Pro Toolbox
1. Clone this repository or download the 
[toolbox file](fwdet/FwDET.tbx).
2. Open ArcMap/Pro and navigate using the catalog to the directory
   containing `FwDET.tbx` or `FwDET_ArcGISPro.tbx`.
3. Expand the toolbox and double click on the tool version you wish to
   use.
   
## How to use FwDET QGIS Plugin
1. Clone this repository or download the
[plugin file](fwdet/FwDET_QGIS_plugin.py).
2. Open QGIS and open the processing toolbox panel.
3. Click on the small python logo in between the gears and clock icons,
   select add script to toolbox.
4. Expand the `Scripts` folder inside of the toolbox panel and open the folder
   `FwDET` and double click on `FwDET v1`.


### Publications from this work:
[Cohen et al. 2019](https://doi.org/10.5194/nhess-2019-78) -- The
Floodwater Depth Estimation Tool (FwDET v2.0) for Improved Remote
Sensing Analysis of Coastal Flooding 

Cohen, et al. (2017), Estimating Floodwater Depths from Flood
Inundation Maps and Topography, _Journal of the American Water
Resources Association_, 54 (4), 847–858.
[doi:10.1111/1752-1688.12609](https://doi.org/10.1111/1752-1688.12609)

### Contacts:
[Sagy Cohen](mailto:sagy.cohen@ua.edu)

[Austin Raney](mailto:aaraney@crimson.ua.edu)

### Other resources:

[SDML Website](https://sdml.ua.edu)

[FwDET CSDMS Tool Repo Description](https://csdms.colorado.edu/wiki/Model:FwDET)

