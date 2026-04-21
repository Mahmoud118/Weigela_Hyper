**README**

**Overview**

This repository provides an end-to-end pipeline for processing hyperspectral imagery and extracting pixel-level spectral data from defined regions of interest (ROIs). The workflow integrates ENVI header handling and automated spectral extraction using Python.

Beyond extraction, the pipeline includes data cleaning and analysis. Extracted spectral data is filtered using Isolation Forest to remove outliers, then reorganized into a structured matrix suitable for multivariate analysis. Each row represents an individual plant observation, and each column corresponds to a spectral reflectance variable (wavelength).

To analyze spectral variability, Principal Component Analysis (PCA) is applied to reduce dimensionality and capture dominant patterns associated with plant water stress.

**Project Structure**

The pipeline consists of the following main components:

**1. Data Preparation (Geospatial Setup)**


•	Export ENVI header files

•	Define regions of interest (ROIs) using shapefiles 

•	Annotate plots using GIS tools (e.g., QGIS) 


**2. Spectral Data Extraction**

•	Extract pixel-level reflectance values across all spectral bands 

•	Associate each pixel with its corresponding plot/region ID 

•	Export results to structured CSV format for downstream analysis 

Implemented using:

•	spec_extract.py — core extraction script (GDAL-based) 

•	envi_header_handler.py — ENVI metadata parsing and handling 

•	extract_spectral_data.ipynb — interactive workflow execution 

**3. Data Preprocessing & Analysis**

•	Clean extracted data and remove noise using Isolation Forest 

•	Standardize and normalize spectral features 

•	Restructure dataset into a matrix format (samples × wavelengths) 

•	Apply PCA for dimensionality reduction and feature extraction 

Implemented using:

•	preprocess.ipynb 

**Requirements**

•	Python 3.x 
•	GDAL (≥ 3.x recommended) 
Core Libraries
•	numpy 
•	pandas 
•	matplotlib 
•	seaborn 
•	scikit-learn 
•	GDAL / osgeo 
•	argparse 

**Analysis**

•	IsolationForest (outlier detection) 
•	StandardScaler (feature scaling) 
•	PCA (dimensionality reduction) 

**Installation**

Clone the repository:
git clone https://github.com/Mahmoud118/Weigela_Hyper
cd Weigela_Hyper
Install dependencies:
pip install -r requirements.txt

**Usage**

Run the spectral extraction script:
python spec_extract.py \
  -r Calib_K00256 \
  -p Calib_K00256.shp \
  -f Plot_ID \
  -c 01_extraction.csv \
  -l Calib_K00256

**Parameters**

•	-r : Path to the multiband raster image 
•	-p : Path to the polygon shapefile 
•	-f : Attribute field used as polygon ID 
•	-c : Output CSV file 
•	-l : Flightline or dataset identifier 

**Output**

•	CSV file containing: 

o	Plot/region IDs 

o	Spectral reflectance values for each band 

•	Preprocessed dataset: 

o	Cleaned matrix (samples × wavelengths) 

o	PCA-transformed features for analysis

