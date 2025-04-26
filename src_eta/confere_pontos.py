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

# Abrir o primeiro arquivo NetCDF
ds = xr.open_mfdataset(files_eta)

# Converter longitude de 0-360 para -180-180
ds = ds.assign_coords(xt_ocean=(((ds.xt_ocean + 180) % 360) - 180))

# Domínio para o campo eta_t e plotagem
min_lat, max_lat = -34, -28
min_lon, max_lon = -55, -45

# Redimensionar o domínio para o campo eta_t
ds = ds.sel(xt_ocean=slice(min_lon, max_lon), yt_ocean=slice(min_lat, max_lat))

# Correção do campo de eta_t
ds["eta_t"] = ds.eta_t

# Calcular a média do campo eta_t ao longo do tempo
eta_mean = ds.eta_t.mean("Time")

# Configurações do mapa
fig = plt.figure(figsize=(10, 8))
ax = plt.axes(projection=ccrs.PlateCarree())

# Adicionar características geográficas
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAND, zorder=0, edgecolor='black')
ax.add_feature(cfeature.OCEAN)

# Adcionar gridlines
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  linewidth=2, color='gray', alpha=0.5, linestyle='--')
gl.xlabels_top = False
gl.ylabels_right = False

# Definir a extensão do mapa (ajuste conforme necessário)
ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())

# Contornos do campo médio eta_t
contour = ax.contourf(ds.xt_ocean, ds.yt_ocean, eta_mean, cmap="coolwarm",
                      norm=colors.CenteredNorm(), transform=ccrs.PlateCarree())
plt.colorbar(contour, fraction=0.03, pad=0.06)

# Coordenadas referencias do SIMCOSTA
coords_pontos = {
    'Rio Grande': {'lat': -32.0236, 'lon': -52.1056},
    'Tramandai': {'lat': -30.0050, 'lon': -50.1289}
}

# Definir delta x e delta y para buffer, pois os pontos selecionados caem em solo
delta_x = ds.xt_ocean[1] - ds.xt_ocean[0]
delta_y = ds.yt_ocean[1] - ds.yt_ocean[0]

# Fazer 5 pontos espaçados pelo dx e dy
for buffer in range(6):
    if buffer == 0:
        markerfacecolor = 'k'
    else:
        markerfacecolor = 'none'

    # Adicionar os pontos de Rio Grande e Tramandaí
    for ponto, coord in coords_pontos.items():
        ax.plot(coord['lon'] + delta_x * buffer,
                coord['lat'] - delta_y * buffer,
                'ko', markersize=8, alpha=0.8,
                linewidth=2,
                markerfacecolor=markerfacecolor,
                transform=ccrs.PlateCarree())
        ax.text(coord['lon'] + 0.5, coord['lat'], ponto, fontsize=12, transform=ccrs.PlateCarree())

# Salvar o plot
plt.savefig('eta e.png', dpi=300, bbox_inches='tight')