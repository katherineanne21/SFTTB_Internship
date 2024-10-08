# -*- coding: utf-8 -*-
"""ArcGIS_Geodatabase_Merge.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/15KO9ylH5ymYmMC8BsvaCVknaGG2rUD8W

### Prep Workspace
"""

# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive', force_remount=True)

# Import required modules
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, shape
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tabulate import tabulate
import time

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Provide the path to the JSON file
creds = ServiceAccountCredentials.from_json_keyfile_name('/content/drive/Shareddrives/SFTT Shared Drive/0General Management & Admin/Employee Onboarding/SFTT Specific Employees/Summer 2024/Katherine Anne/Colabs/enhanced-keel-424914-m2-7c2e82d072b9.json', scope)

# Authorize the clientsheet
client = gspread.authorize(creds)

"""### Read In Data"""

# TES Data
shapefile_path = '/content/drive/Shareddrives/SFTT Shared Drive/0General Management & Admin/Employee Onboarding/SFTT Specific Employees/Summer 2024/Katherine Anne/Colabs/GIS/TESData/ma_tes.shp'
TESData = gpd.read_file(shapefile_path)

# Arc GIS Data
shapefile_path = '/content/drive/Shareddrives/SFTT Shared Drive/0General Management & Admin/Employee Onboarding/SFTT Specific Employees/Summer 2024/Katherine Anne/Colabs/GIS/ArcGISData/Parcels_Web_V4.shp'
ArcGIS_Data = gpd.read_file(shapefile_path)
ArcGIS_Data['ID_Num'] = range(1, len(ArcGIS_Data) + 1)

# Environmental Justice Populations Data
shapefile_path = '/content/drive/Shareddrives/SFTT Shared Drive/0General Management & Admin/Employee Onboarding/SFTT Specific Employees/Summer 2024/Katherine Anne/Colabs/GIS/ArcGISData/EJPops_Web_Clip.shp'
EJPop_Data = gpd.read_file(shapefile_path)

# Historical Disinvestment/ Redlining Data
shapefile_path =  '/content/drive/Shareddrives/SFTT Shared Drive/0General Management & Admin/Employee Onboarding/SFTT Specific Employees/Summer 2024/Katherine Anne/Colabs/GIS/ArcGISData/cartodb-query.shp'
HistDis_Data = gpd.read_file(shapefile_path)

"""###Linking Data

Geo Merges
"""

# Merge TES data

# Ensure both GeoDataFrames use the same CRS
TESData = TESData.to_crs(ArcGIS_Data.crs)

# Perform a spatial join
merged_gdf = gpd.sjoin(ArcGIS_Data, TESData, how = 'left', predicate = 'intersects')

# Merge EJ Pop Data

# Ensure both GeoDataFrames use the same CRS
EJPop_Data = EJPop_Data.to_crs(merged_gdf.crs)

# Perform a spatial join
merged_gdf = gpd.sjoin(merged_gdf, EJPop_Data, how='left', predicate='intersects', lsuffix='_left', rsuffix='_right')

# Merge Historical Disinvestment Data

HistDis_Data = HistDis_Data.to_crs(merged_gdf.crs)

# Perform a spatial join
merged_gdf = gpd.sjoin(merged_gdf, HistDis_Data, how='left', predicate='intersects', lsuffix='_l', rsuffix='_r')

"""###Columns Work

Add new columns
"""

# Add Available Area (sqm) column
merged_gdf['Lot Area (sqm)'] = (merged_gdf['sqm_imperv'] * 100)/ merged_gdf['pct_imperv']
merged_gdf['Available Area (sqm)'] = merged_gdf['Lot Area (sqm)'] - merged_gdf['sqm_imperv']

# Change PrioZone to True False

# Convert column to string
merged_gdf['PrioZone'] = merged_gdf['PrioZone'].astype(str)

for idx, row in merged_gdf.iterrows():
    prio_zone_value = row['PrioZone']
    if 'Y' in prio_zone_value:
      merged_gdf.at[idx, 'PrioZone'] = 'TRUE'
    elif 'N' in prio_zone_value:
      merged_gdf.at[idx, 'PrioZone'] = 'FALSE'
    else:
      merged_gdf.at[idx, 'PrioZone'] = None

# Create a column for EJ Flag and EJ #
merged_gdf['EJ Flag'] = 'FALSE'
merged_gdf['EJ #'] = None

merged_gdf['EJ'] = merged_gdf['EJ'].astype(str)

for idx, row in merged_gdf.iterrows():
  if 'Yes' in row['EJ']:
    merged_gdf.at[idx, 'EJ Flag'] = 'TRUE'
  if pd.notnull(row['EJ_CRITE_1']):
    merged_gdf.at[idx, 'EJ #'] = row['EJ_CRITE_1']

# Create historical disinvestment flag and letter columns
merged_gdf['HisDis (Historical Disinvestment)'] = 'FALSE'
merged_gdf['HisDis Letter'] = None

merged_gdf['holc_grade__r'] = merged_gdf['holc_grade__r'].astype(str)

for idx, row in merged_gdf.iterrows():
  if pd.notnull(row['holc_grade__r']):
    merged_gdf.at[idx, 'HisDis Letter'] = row['holc_grade__r']
  if row['holc_grade__r'] in ['C', 'D']:
    merged_gdf.at[idx, 'HisDis (Historical Disinvestment)'] = 'TRUE'

"""Select Columns"""

# Select all columns needed
selected_columns = [
    'ID_Num',
    'addr_str',
    'addr_num',
    'CITY',
    'Lot Area (sqm)',
    'Available Area (sqm)',
    'PrioZone',
    'EJ Flag',
    'EJ #',
    'HisDis (Historical Disinvestment)',
    'HisDis Letter',
    'MAP_PAR_ID',
    'muni',
    'site_addr',
    'addr_zip',
    'CanopyPerc',
    'pct_imperv',
    'tes',
    'LU_Recode_',
    'sqm_imperv'
]

# Shrink geodataframe
merged_gdf = merged_gdf[selected_columns]

"""###Write to CSV"""

# Define path/location of CSV
output_csv_path = '/content/drive/Shareddrives/SFTT Shared Drive/0General Management & Admin/Employee Onboarding/SFTT Specific Employees/Summer 2024/Katherine Anne/Colabs/Merged_Geodatabse.csv'

# Write geodatabse to CSV
merged_gdf.to_csv(output_csv_path, index=False)