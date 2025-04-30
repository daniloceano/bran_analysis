import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
# from cartopy.io.img_tiles import StamenTerrain
import numpy as np
from geopy.distance import geodesic
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# Abrir dados
ds = xr.open_dataset('../BRAN_currents_Aracatu/ocean_u_1997_01.nc')
ds['xu_ocean'] = ((ds['xu_ocean'] + 180) % 360) - 180

# Ponto de interesse
LAT_PONTO = -21.6389
LON_PONTO = -40.8693

# Selecionar ponto mais próximo no modelo
ds_ponto = ds.sel(xu_ocean=LON_PONTO, yu_ocean=LAT_PONTO, method='nearest')
lat_model = float(ds_ponto['yu_ocean'].values)
lon_model = float(ds_ponto['xu_ocean'].values)

# Calcular distância em km
dist_km = geodesic((LAT_PONTO, LON_PONTO), (lat_model, lon_model)).km

# Criar figura
fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([lon_model-1, lon_model+1, lat_model-1, lat_model+1], crs=ccrs.PlateCarree())

# Recursos do mapa
ax.add_feature(cfeature.LAND, zorder=0, facecolor='beige')
ax.add_feature(cfeature.OCEAN, zorder=0, facecolor='lightblue')
ax.coastlines(resolution='10m')
ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)

# Ponto real (interesse)
ax.plot(LON_PONTO, LAT_PONTO, 'ro', markersize=8, label='Aracatu')

# Ponto do modelo
ax.plot(lon_model, lat_model, marker='*', color='purple', markersize=12,
        label=f'BRAN_u (%.3fKm)' % dist_km)

# Linha entre os pontos
ax.plot([LON_PONTO, lon_model], [LAT_PONTO, lat_model], 'k--', lw=1)

# Legenda
ax.legend(loc='upper left')

# Escala gráfica (manual, simples)
ax.hlines(y=ax.get_extent()[2]+0.05, xmin=ax.get_extent()[0]+0.05,
          xmax=ax.get_extent()[0]+0.35, colors='k', linewidth=3)
ax.text(ax.get_extent()[0]+0.2, ax.get_extent()[2]+0.1, '30 km',
        horizontalalignment='center', transform=ccrs.PlateCarree())

# Inset com localização no Brasil
# Adiciona inset com Cartopy manualmente
inset_ax = fig.add_axes([0.65, 0.7, 0.25, 0.25], projection=ccrs.PlateCarree())
inset_ax.set_extent([-55, -30, -35, -10], crs=ccrs.PlateCarree())
inset_ax.coastlines(resolution='10m')
inset_ax.add_feature(cfeature.LAND, facecolor='lightgray')
inset_ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
inset_ax.plot(LON_PONTO, LAT_PONTO, 'r.', transform=ccrs.PlateCarree())
inset_ax.add_patch(mpatches.Rectangle((lon_model-1, lat_model-1), 2, 2,
                                      edgecolor='red', facecolor='none',
                                      lw=1.5, transform=ccrs.PlateCarree()))

plt.tight_layout()
plt.savefig('mapa_ponto_correntes_Aracatu.png', dpi=300)
