# Floodwater Depth Estimation Tool (FwDET)
Calculates floodwater depths using a digital elevation model (DEM) and a flood extent polygon

![screen capture](/assets/remotesensing-14-05313-g009.png)

# Updates:
### 2023-10-20
Implemented in [QGIS as a processing script](qgis/README.md)

### 2022-08-24
Implemented in:
- >= ArcGis 10.5
- ArcGis Pro
- Google Earth Engine
    
# Description
Within this repository resides the three versions of
FwDET. Version 1, featured in Estimating Floodwater Depths from Flood
Inundation Maps and Topography [Cohen et al. 2018], best works in
inland riverine regions and has been implemented using both Arcpy and
QGIS. Version 2, features an improved algorithm which better solves
coastal flooding as well as fluvial [Cohen et al. 2019]. Version 2 implements a much
different approach that is considerably more computationally
efficient, drastically reducing run time compared to version 1 of the
tool. Version 2.1 introduces a boundary cell smoothing and filtering procedure which
improves the tool's accuracy [Cohen et al. 2022].

# Installation

## ArcMap/Pro Toolbox
1. Clone this repository or download the 
[toolbox file](fwdet/FwDET.tbx).
2. Open ArcMap/Pro and navigate using the catalog to the directory
   containing `FwDET_ArcGISPro.tbx`.
3. Expand the toolbox and double click on the tool version you wish to
   use.
   
## QGIS
see [qgis/README.md](qgis/README.md)


# Related Publications:
[Cohen et al. 2022](https://doi.org/10.3390/rs14215313)  Sensitivity of Remote Sensing Floodwater Depth Calculation to Boundary Filtering and Digital Elevation Model Selections. _Remote Sensing_

[Peter et al. 2020](https://doi.org/10.1109/LGRS.2020.3031190) Google Earth Engine 
Implementation of the Floodwater Depth Estimation Tool (FwDET-GEE) for Rapid and Large Scale Flood Analysis. 
_IEEE Geoscience and Remote Sensing Letters._

[Cohen et al. 2019](https://doi.org/10.5194/nhess-2019-78) -- The
Floodwater Depth Estimation Tool (FwDET v2.0) for Improved Remote
Sensing Analysis of Coastal Flooding. _Natural Hazards and Earth System Sciences_, 19, 2053–2065. 

[Cohen et al. (2017)](https://doi.org/10.1111/1752-1688.12609), Estimating Floodwater Depths from Flood
Inundation Maps and Topography, _Journal of the American Water
Resources Association_, 54 (4), 847–858.

# Contacts:
[Sagy Cohen](mailto:sagy.cohen@ua.edu)

# Other resources:

[SDML Website](https://sdml.ua.edu)

[FwDET CSDMS Tool Repo Description](https://csdms.colorado.edu/wiki/Model:FwDET)

