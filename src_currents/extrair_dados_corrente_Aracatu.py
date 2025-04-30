import xarray as xr
import pandas as pd
from glob import glob
from pathlib import Path
import numpy as np

# Diretório onde os arquivos BRAN estão salvos
BRAN_DIR = Path("BRAN_currents_Aracatu")
OUTPUT_CSV = "dados_u_v_Aracatu.csv"

# Coordenadas do ponto de interesse (Porto de Ubu - ES)
LAT_PONTO = -21.6389
LON_PONTO = -40.8693

# Encontrar os arquivos de u e v
files_u = glob(f"{BRAN_DIR}/ocean_u*.nc")
files_v = glob(f"{BRAN_DIR}/ocean_v*.nc")

print("🔍 Abrindo arquivos de corrente...")

# Abrir os datasets
ds_u = xr.open_mfdataset(files_u, combine='by_coords')
ds_v = xr.open_mfdataset(files_v, combine='by_coords')

# Ajustar as coordenadas de longitude para o intervalo [-180, 180]
ds_u = ds_u.assign_coords(xu_ocean=(((ds_u.xu_ocean + 180) % 360) - 180))
ds_v = ds_v.assign_coords(xu_ocean=(((ds_v.xu_ocean + 180) % 360) - 180))

print("🌍 Arquivos carregados com sucesso!")

print(f"🔎 Localizando o ponto de interesse: Latitude = {LAT_PONTO}, Longitude = {LON_PONTO}...")

# Extrair os dados de u e v para o ponto específico e para todos os níveis verticais
u_data = ds_u.sel(yu_ocean=LAT_PONTO, xu_ocean=LON_PONTO, method='nearest').u
v_data = ds_v.sel(yu_ocean=LAT_PONTO, xu_ocean=LON_PONTO, method='nearest').v

print("📊 Dados extraídos com sucesso para o ponto especificado!")

# Criar DataFrames separando os dados por profundidade
df_u = u_data.to_dataframe().reset_index()
df_v = v_data.to_dataframe().reset_index()

# Verificar as profundidades disponíveis
lev_u = df_u['st_ocean'].unique()
lev_v = df_v['st_ocean'].unique()

print(f"🔎 Níveis de profundidade encontrados para u: {lev_u}")
print(f"🔎 Níveis de profundidade encontrados para v: {lev_v}")

# Reorganizar os dados para ter uma coluna por profundidade
df_u_pivot = df_u.pivot(index='Time', columns='st_ocean', values='u')
df_v_pivot = df_v.pivot(index='Time', columns='st_ocean', values='v')

# Concatenar os dados de u e v no mesmo DataFrame
df = pd.concat([df_u_pivot, df_v_pivot], axis=1)

# Adicionar a coluna de coordenadas de latitude e longitude (apenas uma vez)
df['yu_ocean'] = LAT_PONTO
df['xu_ocean'] = LON_PONTO

# Organizar as colunas para ter as coordenadas no final
df = df[['yu_ocean', 'xu_ocean'] + [col for col in df.columns if col not in ['yu_ocean', 'xu_ocean']]]

print(f"📊 Dados extraídos e reorganizados. Total de registros: {len(df)}")

# Salvar os dados em um CSV
df.to_csv(OUTPUT_CSV, index=True)
print(f"✅ Dados salvos no arquivo: {OUTPUT_CSV}")
