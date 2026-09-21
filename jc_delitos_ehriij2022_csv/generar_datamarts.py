import os
import sys
sys.path.insert(0, os.path.expanduser('~/.local/lib/python3.13/site-packages'))
import csv
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE RUTAS
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_ENRIQUECIDO = os.path.join(BASE_DIR, 'datos_procesados', 'delit_jc_ehriij2022_enriquecido.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'datos_procesados')

print("=== INICIANDO PIPELINE DE CONSTRUCCIÓN DE DATAMARTS ANALÍTICOS ===")

if not os.path.exists(INPUT_ENRIQUECIDO):
    raise FileNotFoundError(f"No se encontró el archivo de entrada: {INPUT_ENRIQUECIDO}")

# ---------------------------------------------------------
# 2. FUNCIONES DE MAPEO Y REGION
# ---------------------------------------------------------

def obtener_macro_categoria(cod_deli_raw):
    """Clasifica los 151 delitos del INEGI en 7 Macro Categorías Penales."""
    try:
        val = int(cod_deli_raw)
    except (ValueError, TypeError):
        return "Otros Delitos del Fuero Común"

    if 10000 <= val < 20000:
        return "Delitos contra la Vida y la Integridad Personal"
    elif 20000 <= val < 30000:
        return "Delitos contra la Libertad Personal"
    elif 30000 <= val < 40000:
        return "Delitos contra la Libertad y Seguridad Sexual"
    elif 40000 <= val < 50000:
        return "Delitos contra el Patrimonio"
    elif 50000 <= val < 60000:
        return "Delitos contra la Familia"
    elif 60000 <= val < 70000:
        return "Delitos contra la Sociedad"
    elif 70000 <= val < 80000:
        return "Delitos contra la Salud y Delincuencia Organizada"
    elif 80000 <= val < 90000:
        return "Delitos por Hechos de Corrupción y Admón. Pública"
    else:
        return "Otros Delitos del Fuero Común"

REGION_MAP = {
    '02': 'Noroeste', '03': 'Noroeste', '18': 'Noroeste', '25': 'Noroeste', '26': 'Noroeste',
    '05': 'Noreste', '19': 'Noreste', '28': 'Noreste',
    '01': 'Centro-Norte', '08': 'Centro-Norte', '10': 'Centro-Norte', '11': 'Centro-Norte', '24': 'Centro-Norte', '32': 'Centro-Norte',
    '06': 'Occidente', '14': 'Occidente', '16': 'Occidente', '22': 'Occidente',
    '09': 'Centro', '13': 'Centro', '15': 'Centro', '17': 'Centro', '21': 'Centro', '29': 'Centro',
    '04': 'Sur-Sureste', '07': 'Sur-Sureste', '12': 'Sur-Sureste', '20': 'Sur-Sureste', '23': 'Sur-Sureste', '27': 'Sur-Sureste', '30': 'Sur-Sureste', '31': 'Sur-Sureste'
}

def obtener_region(cve_entidad):
    cve_clean = str(cve_entidad).zfill(2)
    return REGION_MAP.get(cve_clean, 'No especificada')

def obtener_trimestre(mes):
    try:
        m = int(mes)
        if 1 <= m <= 3: return 'Q1'
        elif 4 <= m <= 6: return 'Q2'
        elif 7 <= m <= 9: return 'Q3'
        elif 10 <= m <= 12: return 'Q4'
    except (ValueError, TypeError):
        pass
    return ''

DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

# ---------------------------------------------------------
# 3. CARGA Y FEATURE ENGINEERING EN PANDAS
# ---------------------------------------------------------
print("\n[Fase 1/3] Cargar dataset enriquecido e integrar variables derivadas...")

df = pd.read_csv(INPUT_ENRIQUECIDO, dtype=str)

print(f"  ✔ Registros leídos: {len(df):,}")

# A. Claves Geográficas Estandarizadas
df['cve_geo_juzgado'] = df['ubicgeoc'].str.zfill(5)
df['cve_geo_entidad_juzgado'] = df['cve_geo_juzgado'].str[:2]
df['cve_geo_entidad_ocurrencia'] = df['entiocur'].str.zfill(2)
df['cve_geo_municipio'] = np.where(
    (df['muocurri'].notna()) & (df['muocurri'] != ''),
    df['muocurri'].str.zfill(5),
    ''
)

# B. Movilidad Delictiva y Región
df['flag_movilidad_delictiva'] = np.where(
    (df['cve_geo_entidad_ocurrencia'] != '') & (df['cve_geo_entidad_juzgado'] != ''),
    df['cve_geo_entidad_ocurrencia'] != df['cve_geo_entidad_juzgado'],
    False
)

df['region_geografica_inegi'] = df['cve_geo_entidad_ocurrencia'].apply(obtener_region)

# C. Homologación Categórica Macro
df['macro_categoria_delito'] = df['delirie8'].apply(obtener_macro_categoria)

df['gravedad_intencionalidad'] = df['forcomis'].map({
    '1': 'Doloso / Intencional',
    '2': 'Culposo / No Intencional'
}).fillna('No Especificado')

df['grado_ejecucion'] = df['consumac'].map({
    '1': 'Consumado',
    '2': 'Tentativa'
}).fillna('No Especificado')

# D. Dimensión Temporal
df['fec_ocur_trimestre'] = df['fec_ocur_mes'].apply(obtener_trimestre)

# Día de la semana a partir de fec_ocur_iso
fec_dt = pd.to_datetime(df['fec_ocur_iso'], errors='coerce')
df['dia_semana_ocurrencia'] = fec_dt.dt.dayofweek.map(lambda d: DIAS_SEMANA[int(d)] if pd.notna(d) else '')

# Rezago en años (Censo 2021 - Año Ocurrencia)
anio_num = pd.to_numeric(df['fec_ocur_anio'], errors='coerce')
df['antiguedad_procesamiento_anios'] = (2021 - anio_num).astype('Int64')

# E. Dimensión de Impacto e Involucrados
num_imp = pd.to_numeric(df['totalca1'], errors='coerce').fillna(0)
num_vic = pd.to_numeric(df['totalca2'], errors='coerce').fillna(0)

df['flag_victima_multiple'] = num_vic > 1
df['flag_imputado_multiple'] = num_imp > 1

ratio_val = np.where(num_vic > 0, num_imp / num_vic, np.nan)
df['ratio_imputados_por_victima'] = np.round(ratio_val, 2)

def clasificar_impacto(vic):
    if pd.isna(vic) or vic == 0:
        return 'Sin víctimas directas'
    elif vic == 1:
        return 'Víctima individual'
    elif 2 <= vic <= 5:
        return 'Víctima múltiple (2-5)'
    else:
        return 'Víctima masiva (>5)'

df['clasificacion_impacto_victimas'] = num_vic.apply(clasificar_impacto)

print("  ✔ Feature Engineering completado exitosamente.")

# ---------------------------------------------------------
# 4. EXPORTACIÓN DEL DATAMART GRANULAR
# ---------------------------------------------------------
print("\n[Fase 2/3] Generando Datamart Granular (Parquet y CSV)...")

out_granular_parquet = os.path.join(OUTPUT_DIR, 'datamart_delitos_granular.parquet')
out_granular_csv = os.path.join(OUTPUT_DIR, 'datamart_delitos_granular.csv')

df.to_parquet(out_granular_parquet, index=False, engine='pyarrow', compression='snappy')
df.to_csv(out_granular_csv, index=False, encoding='utf-8')

print(f"  ✔ Granular Parquet: {out_granular_parquet} ({os.path.getsize(out_granular_parquet) / 1024 / 1024:.2f} MB)")
print(f"  ✔ Granular CSV:     {out_granular_csv} ({os.path.getsize(out_granular_csv) / 1024 / 1024:.2f} MB)")

# ---------------------------------------------------------
# 5. GENERACIÓN DE DATAMARTS AGREGADOS
# ---------------------------------------------------------
print("\n[Fase 3/3] Generando Datamarts Agregados...")

# 5.1 Datamart Agregado Municipal
df['tot_imputados'] = num_imp
df['tot_victimas'] = num_vic

agg_muni = df.groupby(
    ['cve_geo_municipio', 'descrip_muocurri', 'cve_geo_entidad_ocurrencia', 'descrip_entiocur', 'fec_ocur_anio', 'macro_categoria_delito'],
    dropna=False
).agg(
    total_delitos=('cod_deli', 'count'),
    total_imputados=('tot_imputados', 'sum'),
    total_victimas=('tot_victimas', 'sum'),
    delitos_dolosos=('gravedad_intencionalidad', lambda x: (x == 'Doloso / Intencional').sum()),
    delitos_culposos=('gravedad_intencionalidad', lambda x: (x == 'Culposo / No Intencional').sum()),
    delitos_consumados=('grado_ejecucion', lambda x: (x == 'Consumado').sum()),
    victimas_multiples=('flag_victima_multiple', 'sum')
).reset_index()

out_muni_parquet = os.path.join(OUTPUT_DIR, 'datamart_agregado_municipal.parquet')
out_muni_csv = os.path.join(OUTPUT_DIR, 'datamart_agregado_municipal.csv')
agg_muni.to_parquet(out_muni_parquet, index=False, engine='pyarrow', compression='snappy')
agg_muni.to_csv(out_muni_csv, index=False, encoding='utf-8')

print(f"  ✔ Agregado Municipal Parquet: {out_muni_parquet} ({os.path.getsize(out_muni_parquet) / 1024 / 1024:.2f} MB)")
print(f"  ✔ Agregado Municipal CSV:     {out_muni_csv} ({os.path.getsize(out_muni_csv) / 1024 / 1024:.2f} MB)")

# 5.2 Datamart Agregado Temporal
agg_temp = df.groupby(
    ['cve_geo_entidad_ocurrencia', 'descrip_entiocur', 'region_geografica_inegi', 'fec_ocur_anio', 'fec_ocur_mes', 'fec_ocur_trimestre', 'macro_categoria_delito'],
    dropna=False
).agg(
    total_delitos=('cod_deli', 'count'),
    total_imputados=('tot_imputados', 'sum'),
    total_victimas=('tot_victimas', 'sum')
).reset_index()

out_temp_parquet = os.path.join(OUTPUT_DIR, 'datamart_agregado_temporal.parquet')
out_temp_csv = os.path.join(OUTPUT_DIR, 'datamart_agregado_temporal.csv')
agg_temp.to_parquet(out_temp_parquet, index=False, engine='pyarrow', compression='snappy')
agg_temp.to_csv(out_temp_csv, index=False, encoding='utf-8')

print(f"  ✔ Agregado Temporal Parquet: {out_temp_parquet} ({os.path.getsize(out_temp_parquet) / 1024 / 1024:.2f} MB)")
print(f"  ✔ Agregado Temporal CSV:     {out_temp_csv} ({os.path.getsize(out_temp_csv) / 1024 / 1024:.2f} MB)")

print("\n=== PIPELINE DE DATAMARTS COMPLETADO CON ÉXITO ===")
