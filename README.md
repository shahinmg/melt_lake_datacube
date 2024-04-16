### melt_lake_datacube

How to detect melt lakes on ice sheets using STACs 

The `melt_lake_sample_tutorial.ipynb` in the `melt_lake_datacube` shows how to sample melt lakes using [Microsoft Planetary Computer's Sentinel 1 Radiometrically Terrain Corrected (RTC)](https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc) catalog. 'melt_lake_detection_s1_rtc_ec2.py' is the scipt I ran on my ec2 instance and saved the resulting xarray dataset as a csv `surface_CW2019_lake_mean_da_asc_hv.csv` in the `output` directory. The `read_csv_from_flox.ipynb` is the code I wrote to plot the time series plots. 


## Thoughts on improvements 
I tried to make a GPU native version using cupy-xarray `cupy_xarray_test.ipynb`, which is not working as of now. We should also try to speed things up for when we scale up. Some thoughts might be to use the `cohorts` method in the group by. More on that is [here](https://flox.readthedocs.io/en/latest/user-stories/climatology.html). 