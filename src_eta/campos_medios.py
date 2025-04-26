import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from glob import glob
import matplotlib.colors as colors


# Diretório onde estão os arquivos
files_directory = '/media/daniloceano/Seagate Expansion Drive/Brazil'
files_eta = glob(files_directory + '/*eta*.nc')

ds = xr.open_mfdataset(files_eta, chunks={'time': 100})

ds = ds.assign_coords(xt_ocean=(((ds.xt_ocean + 180) % 360) - 180))

ds.eta_t.mean("Time").plot()

# # Domínio para o campo eta_t e plotagem
# min_lat, max_lat = -34, -28
# min_lon, max_lon = -55, -45

# # Redimensionar o domínio para o campo eta_t
# ds = ds.sel(xt_ocean=slice(min_lon, max_lon), yt_ocean=slice(min_lat, max_lat))
