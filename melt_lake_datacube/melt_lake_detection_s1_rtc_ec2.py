#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 14:21:57 2024

@author: laserglaciers
"""
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import rich.table
import planetary_computer
from pystac_client import Client
from shapely.geometry import Polygon
import rioxarray as rio
import pystac
from shapely.geometry import box
from shapely  import buffer
from IPython.display import Image
import stackstac
import os
# %%


catalog = Client.open('https://planetarycomputer.microsoft.com/api/stac/v1')
#melt_paths = '../lake_locations-20240322T205617Z-001/lake_locations/dunmire_2021/surface/surface_CW2019.geojson'
#melt_lake_df = gpd.read_file(melt_paths)

lake_rasters = rio.open_rasterio(
    "../surface_CW2019_rasterized_single_grid.tif", chunks="auto"
).squeeze()

bound_box_3413 = box(*lake_rasters.rio.bounds())
gdf_box = gpd.GeoDataFrame(geometry=[bound_box_3413],crs=3413)
gdf_box_4326 = gdf_box.to_crs(4326)

time_range = '2019-01-01/2019-12-31'

search = catalog.search(collections=["sentinel-1-rtc"], intersects=gdf_box_4326.geometry[0], datetime=time_range)
items = search.get_all_items()

df = gpd.GeoDataFrame.from_features(items.to_dict(), crs='epsg:4326')
print('df created')

# %%
#from dask.distributed import Client

#client = Client(processes=False)
#print(client.dashboard_link)

#from dask.distributed import LocalCluster
#cluster = LocalCluster()          # Fully-featured local Dask cluster
#client = cluster.get_client()
#print(client.dashboard_link)

bounds = gdf_box_4326.geometry[0].bounds

da = stackstac.stack(
    planetary_computer.sign(items), bounds_latlon=bounds, epsg=3413
)

print('made datacube')

stac_item = pystac.read_file(f'https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-1-rtc/items/{items[0].id}')

def power_to_db(input_arr):
    return (10*np.log10(np.abs(input_arr)))

print('clip zarr cube')
da = da.rio.clip([bound_box_3413],da.rio.crs, drop=True,invert=False, all_touched=True) #not sure if this is right but we need to make them match somehow
lake_rasters = lake_rasters.rio.reproject_match(da) #magic

# # Remove any small floating point error in coordinate locations
_, lakes_aligned = xr.align(da, lake_rasters, join="override")


lake_id = np.unique(lakes_aligned.data)
# 0 is used as NULL
lake_id = lake_id[lake_id != 0]

print(f"There are {len(lake_id)} lakes!")

da_asc = da.where(da['sat:orbit_state'] == 'ascending', drop=True)
da_desc = da.where(da['sat:orbit_state'] == 'descending', drop=True)
da_asc_hv = da_asc.sel(band='hv')

# play with chunk sizes
da_asc_hv = da_asc_hv.chunk({"time": 114, "x": 2048, "y": 2048}) 
#da_asc_hv = da_asc_hv.chunk({"time": 114, "x": 907, "y": 907}) 
#da_asc_hv = da_asc_hv.chunk({"time": 10, "x": 9977, "y": 9977})
da_asc_hv.attrs['spec'] = str(da_asc_hv.attrs['spec'])
da_asc_hv.attrs['spec']

da_asc_hv = power_to_db(da_asc_hv)
# %%
import flox.xarray
print('start taking mean of lakes')
lake_mean = flox.xarray.xarray_reduce(
    da_asc_hv,
    lakes_aligned.rename("lake"),
    func="nanmean",
    expected_groups=(lake_id,),
)
print('load output into memory')
lake_mean = lake_mean.load()
print(lake_mean.time)
lake_mean_df = lake_mean.to_dataframe()
lake_mean_df.to_csv('./surface_CW2019_lake_mean_da_asc_hv.csv')
#Cluster.shutdown() 
#print('save output')
#lake_mean.to_netcdf('./surface_CW2019_lake_mean_da_asc_hv.nc')

