import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# URL do OPeNDAP
url = 'https://thredds.nci.org.au/thredds/dodsC/gb6/BRAN/BRAN2020/daily/ocean_u_2002_02.nc'
ds = xr.open_dataset(url)

# Coordenadas e datas
lat = ds['yu_ocean']
lon = ds['xu_ocean']
depth = ds['st_ocean']
time = ds['Time']
time_start = np.datetime_as_string(time.values[0], unit='D')
time_end = np.datetime_as_string(time.values[-1], unit='D')

# Região: Porto de Ubu (ES) com buffer de 5°
lat_min, lat_max = -25.8, -15.8
lon_min, lon_max = -45.6, -35.6

# Subset espacial e vertical
ds_sub = ds.sel(yu_ocean=slice(lat_min, lat_max), xu_ocean=slice(lon_min % 360, lon_max % 360))
ds_sub = ds_sub.isel(st_ocean=slice(0, 5))

# Média temporal
u_mean = ds_sub['u'].mean(dim='Time')

# Projeção
proj = ccrs.PlateCarree()

# Figura e subplots
fig, axs = plt.subplots(nrows=1, ncols=5, figsize=(18, 5), subplot_kw={'projection': proj})

# Gráficos
for i in range(5):
    ax = axs[i]
    u_plot = u_mean.isel(st_ocean=i)

    im = ax.pcolormesh(
        ds_sub['xu_ocean'], ds_sub['yu_ocean'], u_plot,
        transform=proj, cmap='RdBu_r', shading='auto', vmin=-0.5, vmax=0.5
    )
    
    ax.coastlines()
    ax.set_title(f'Nível {i+1}\nProfundidade ≈ {float(depth[i].values):.1f} m')
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=proj)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='white')

# Ajuste do layout
fig.subplots_adjust(bottom=0.2, top=0.85, wspace=0.1)

# Colorbar abaixo de todos os subplots
cbar_ax = fig.add_axes([0.2, 0.1, 0.6, 0.03])  # [left, bottom, width, height]
cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal')
cbar.set_label('Componente zonal da corrente (m/s)')

# Título geral com período
fig.suptitle(f"Velocidade zonal média (u) nos 5 primeiros níveis\nPeríodo: {time_start} a {time_end}", fontsize=14)

plt.show()
