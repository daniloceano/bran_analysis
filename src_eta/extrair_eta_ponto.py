import xarray as xr
import pandas as pd
from glob import glob
import os

# Define o ponto de interesse
LAT_PONTO = -21.30076
LON_PONTO = -40.96420


# Lista e ordena todos os arquivos
files = sorted(glob("/p1-sto-swell/danilocs/BRAN2020/BRAN_data/ocean_eta_t_*.nc"))

# Cria uma lista para acumular DataFrames
lista_dfs = []

for f in files:
    # Abre o arquivo individualmente
    ds = xr.open_dataset(f)
    
    # Seleciona o gridpoint mais próximo
    pt = ds.sel(yt_ocean=LAT_PONTO, xt_ocean=LON_PONTO, method="nearest")
    
    # Extrai as variáveis de interesse
    time = pt["Time"].values
    eta  = pt["eta_t"].values
    
    # Monta um DataFrame temporário
    df = pd.DataFrame({
        "time": time,
        "eta_t": eta
    })
    lista_dfs.append(df)
    
    # Fecha o dataset para liberar memória
    ds.close()

# Concatena todos em um único DataFrame
df_all = pd.concat(lista_dfs, ignore_index=True)

# Garante que o diretório de saída exista
out_dir = "../BRAN_outputs"
os.makedirs(out_dir, exist_ok=True)

# Salva em CSV
out_path = os.path.join(out_dir, "eta_t_Itabapoana.csv")
df_all.to_csv(out_path, index=False)

print(f"Salvo em {out_path}")

