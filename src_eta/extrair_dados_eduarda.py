import xarray as xr
import pandas as pd
import glob
import multiprocessing as mp
from joblib import Parallel, delayed

# Caminho para os arquivos NetCDF
data_path = "BRAN_data/ocean_eta_t_*.nc"

# Carregar a lista de arquivos disponíveis
nc_files = sorted(glob.glob(data_path))
print(f"📂 Arquivos encontrados: {len(nc_files)}")
if not nc_files:
    print("❌ Nenhum arquivo NetCDF encontrado. Verifique o caminho.")
    exit()

# Carregar as estações do CIRAM a partir do arquivo CSV
stations_file_path = "/mnt/data/Estações da rede maregráfica do CIRAM.csv"
df_stations = pd.read_csv(stations_file_path)
print("📊 Arquivo de estações carregado com sucesso.")

# Processar os dados das estações
stations = []
for index, row in df_stations.iterrows():
    station_name = row['Estação'].strip()
    latitude = float(row['Latitude(Graus, Dec)'].replace(",", "."))
    longitude = float(row['Longitude(Graus,Dec)'].replace(",", "."))
    stations.append({"station": station_name, "lat": latitude, "lon": longitude})

print(f"\n🌍 Total de estações carregadas: {len(stations)}")

# Abrir todos os arquivos NetCDF ao mesmo tempo, ignorando variáveis problemáticas
def load_dataset():
    try:
        print("🔄 Carregando os arquivos NetCDF...\n")
        ds = xr.open_mfdataset(nc_files, combine="by_coords", compat="override",
                               data_vars="minimal", coords="minimal", parallel=True,
                               drop_variables=["Time_bounds", "average_T1", "average_T2", "average_DT"])
        print("📂 Arquivos NetCDF carregados com sucesso.\n")
        return ds
    except Exception as e:
        print(f"❌ Erro ao carregar os arquivos NetCDF: {e}")
        exit()

# Função para processar uma única estação
def process_station(station, ds):
    lat, lon = station["lat"], station["lon"]
    print(f"🔍 Processando estação: {station['station']} (Lat: {lat}, Lon: {lon})")
    records = []
    try:
        # Encontrar os índices mais próximos
        lat_idx = abs(ds["yt_ocean"] - lat).argmin()
        lon_idx = abs(ds["xt_ocean"] - lon).argmin()
        print(f"📍 Índices encontrados - Latitude: {lat_idx}, Longitude: {lon_idx}")
        
        # Extrair os valores de eta_t
        eta_values = ds["eta_t"].isel(yt_ocean=lat_idx, xt_ocean=lon_idx).values
        time_values = ds["Time"].values
        
        # Salvar os dados
        for time, eta in zip(time_values, eta_values):
            records.append({
                "station": station["station"],
                "latitude": lat,
                "longitude": lon,
                "time": pd.to_datetime(time),
                "eta_t": eta
            })
        print(f"✅ Dados extraídos para {station['station']}.")
    except Exception as e:
        print(f"❌ Erro ao processar estação {station['station']}: {e}")
    return records

# Número de núcleos para processamento paralelo
num_cores = min(mp.cpu_count(), 111)  # Garantindo que não ultrapasse o disponível
print(f"⚙️ Usando {num_cores} núcleos para processamento paralelo.\n")

# Carregar os dados
dataset = load_dataset()

# Processar estações em paralelo
results = Parallel(n_jobs=num_cores)(delayed(process_station)(station, dataset) for station in stations)

# Flatten dos resultados
data_records = [item for sublist in results for item in sublist]

# Fechar dataset
dataset.close()
print("\n📂 Arquivos NetCDF fechados.\n")

# Criar DataFrame com os dados extraídos
df_results = pd.DataFrame(data_records)
print(f"📊 Número total de registros extraídos: {len(df_results)}")

# Salvar em CSV
output_file = "dados_eduarda/eta_t_ciram.csv"
df_results.to_csv(output_file, index=False)
print(f"✅ Extração concluída! Dados salvos em {output_file}")

