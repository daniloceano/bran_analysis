import os
from glob import glob
import xarray as xr
import pandas as pd

# Diretório onde estão os arquivos
files_directory = '/media/daniloceano/Seagate Expansion Drive/Brazil'
files_eta = glob(files_directory + '/*eta*.nc')

# Coordenadas referências do SIMCOSTA
coords_pontos = {
    'Rio Grande': {'lat': -32.0236, 'lon': -52.1056},
    'Tramandai': {'lat': -30.0050, 'lon': -50.1289}
}

# Definir delta x e delta y para buffer, pois os pontos selecionados caem em solo
dummy_ds = xr.open_dataset(files_eta[0])
delta_x = float(dummy_ds.xt_ocean[1] - dummy_ds.xt_ocean[0])
delta_y = float(dummy_ds.yt_ocean[1] - dummy_ds.yt_ocean[0])

# Função para processar um único arquivo e extrair os dados das coordenadas de interesse
def process_file(file_path, coords_pontos, dx, dy):
    # Abrir o dataset
    ds = xr.open_dataset(file_path)

    # CPegar o campo de eta_t
    ds["eta_t"] = ds.eta_t
    
    # Converter longitude de 0-360 para -180-180
    ds = ds.assign_coords(xt_ocean=(((ds.xt_ocean + 180) % 360) - 180))
    
    # Extrair dados para Rio Grande e Tramandaí
    data_rg = ds.eta_t.sel(yt_ocean=coords_pontos['Rio Grande']['lat'] - dy,
                           xt_ocean=coords_pontos['Rio Grande']['lon'] + dx,
                           method='nearest')
    
    data_ta = ds.eta_t.sel(yt_ocean=coords_pontos['Tramandai']['lat'] - dy,
                           xt_ocean=coords_pontos['Tramandai']['lon'] + dx,
                           method='nearest')
    
    # Retornar os dados extraídos para as duas localidades
    return data_rg, data_ta

# Listas para armazenar os dados de todos os arquivos
all_data_rg = []
all_data_ta = []

# Processar todos os arquivos e armazenar os dados
for file_path in files_eta:
    # DataFrames temporários para cada arquivo
    df_rg_temp = pd.DataFrame()
    df_ta_temp = pd.DataFrame()

    # Fazer 5 pontos espaçados pelo dx e dy
    for buffer in range(6):
        dx, dy = delta_x * buffer, delta_y * buffer

        data_rg, data_ta = process_file(file_path, coords_pontos, dx, dy)
        
        # Adicionar os dados ao DataFrame temporário
        df_rg_temp[f"ponto_{buffer}"] = data_rg.values
        df_ta_temp[f"ponto_{buffer}"] = data_ta.values

        # Usar tempo como índice do DataFrame
        df_rg_temp.index = data_rg.Time.values
        df_ta_temp.index = data_ta.Time.values

    # Adicionar os DataFrames temporários à lista
    all_data_rg.append(df_rg_temp)
    all_data_ta.append(df_ta_temp)

# Concatenar os DataFrames de todos os arquivos ao longo do eixo 0 (tempo)
df_rg = pd.concat(all_data_rg)
df_ta = pd.concat(all_data_ta)

# Organizar o DataFrame em ordem cronológica
df_rg = df_rg.sort_index()
df_ta = df_ta.sort_index()

# Nomear o índice do DataFrame
df_rg.index.name = 'data'
df_ta.index.name = 'data'

# Função para adicionar cabeçalho de metadados e depois gravar o DataFrame no CSV
def save_with_metadata(df, file_name, coords_pontos):
    with open(file_name, 'w') as f:
        # Escrever os metadados no início do arquivo
        f.write(f"Metadados:\n")
        f.write(f"Rio Grande Coordenadas (Lat, Lon): {coords_pontos['Rio Grande']['lat']}, {coords_pontos['Rio Grande']['lon']}\n")
        f.write(f"Tramandai Coordenadas (Lat, Lon): {coords_pontos['Tramandai']['lat']}, {coords_pontos['Tramandai']['lon']}\n")
        f.write(f"Delta X: {delta_x}, Delta Y: {delta_y}\n")
        f.write(f"\nDados:\n")
    
    # Gravar o DataFrame no arquivo
    df.to_csv(file_name, mode='a')

# Salvar os DataFrames concatenados como arquivos CSV com metadados
save_with_metadata(df_rg, "eta_Rio_Grande.csv", coords_pontos)
save_with_metadata(df_ta, "eta_Tramandai.csv", coords_pontos)

print("Dados extraídos, metadados adicionados e salvos para Rio Grande e Tramandaí em 5 pontos consecutivos.")
