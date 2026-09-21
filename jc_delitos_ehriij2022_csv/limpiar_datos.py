import os
import csv
import glob
from datetime import datetime

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE RUTAS Y DIRECTORIOS
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_CSV = os.path.join(BASE_DIR, 'conjunto_de_datos', 'delit_jc_ehriij2022.csv')
CATALOGS_DIR = os.path.join(BASE_DIR, 'catalogos')
OUTPUT_DIR = os.path.join(BASE_DIR, 'datos_procesados')

print("=== INICIANDO PIPELINE DE LIMPIEZA DE DATOS EHRIJ 2022 ===")

# Crear carpeta de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1.1 Eliminar archivo corrupto residual 'metadatos\' de 0 bytes
corrupt_file = os.path.join(BASE_DIR, 'metadatos\\')
if os.path.exists(corrupt_file):
    try:
        os.remove(corrupt_file)
        print(f"✔ Archivo residual inservible eliminado: {corrupt_file}")
    except Exception as e:
        print(f"⚠️ No se pudo eliminar {corrupt_file}: {e}")

# ---------------------------------------------------------
# 2. CARGA Y PROCESAMIENTO DE CATÁLOGOS
# ---------------------------------------------------------
print("\n[Fase 1/4] Cargando catálogos de referencia...")
catalogs = {}

cat_files = glob.glob(os.path.join(CATALOGS_DIR, '*.csv'))
for cat_path in cat_files:
    cat_name = os.path.splitext(os.path.basename(cat_path))[0]
    cat_dict = {}
    with open(cat_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row:
                continue
            key = row[0].strip()
            # Casos con múltiples descripciones como municipio y juzgado
            if cat_name in ['muocurri', 'ubicgeoc'] and len(row) >= 5:
                cat_dict[key] = f"{row[2].strip()} - {row[4].strip()}"
            elif len(row) >= 2:
                cat_dict[key] = row[1].strip()
            else:
                cat_dict[key] = ""
    catalogs[cat_name] = cat_dict
    print(f"  - Catálogo '{cat_name}': {len(cat_dict)} entradas cargadas.")

# Helper de búsqueda en catálogo flexible para claves numéricas o con ceros a la izquierda
def get_catalog_desc(cat_name, raw_val):
    if not raw_val:
        return ""
    cat = catalogs.get(cat_name, {})
    if raw_val in cat:
        return cat[raw_val]
    # Intentar conversión a entero sin ceros iniciales
    try:
        val_clean = str(int(raw_val))
        if val_clean in cat:
            return cat[val_clean]
    except ValueError:
        pass
    return ""

# ---------------------------------------------------------
# 3. PROCESAMIENTO Y LIMPIEZA DEL DATASET PRINCIPAL
# ---------------------------------------------------------
print("\n[Fase 2/4] Procesando conjunto de datos principal (404,264 filas)...")

output_limpio_csv = os.path.join(OUTPUT_DIR, 'delit_jc_ehriij2022_limpio.csv')
output_enriquecido_csv = os.path.join(OUTPUT_DIR, 'delit_jc_ehriij2022_enriquecido.csv')

headers_limpio = [
    'ubicgeoc', 'cod_expe', 'cod_deli', 'delirie8', 'califide',
    'consumac', 'forcomis', 'foraccio', 'modadel', 'ele_comi',
    'ticoncur', 'clasitip', 'entiocur', 'muocurri',
    'fec_ocur', 'fec_ocur_iso', 'fec_ocur_anio', 'fec_ocur_mes', 'fec_ocur_es_identificada',
    'totalca1', 'totalca2'
]

headers_enriquecido = headers_limpio + [
    'descrip_delito', 'descrip_califide', 'descrip_consumac',
    'descrip_forcomis', 'descrip_foraccio', 'descrip_modadel',
    'descrip_elecomi', 'descrip_ticoncur', 'descrip_clasitip',
    'descrip_entiocur', 'descrip_muocurri', 'descrip_ubicgeoc'
]

total_rows = 0
pk_set = set()
pk_duplicates = 0
dates_repaired = 0

with open(MAIN_CSV, 'r', encoding='utf-8') as f_in, \
     open(output_limpio_csv, 'w', encoding='utf-8', newline='') as f_out_limpio, \
     open(output_enriquecido_csv, 'w', encoding='utf-8', newline='') as f_out_enri:

    reader = csv.DictReader(f_in)
    writer_limpio = csv.writer(f_out_limpio)
    writer_enri = csv.writer(f_out_enri)

    writer_limpio.writerow(headers_limpio)
    writer_enri.writerow(headers_enriquecido)

    for row in reader:
        total_rows += 1

        # 3.1 Preservar ceros a la izquierda en campos de 5 dígitos
        ubicgeoc = row['ubicgeoc'].strip().zfill(5)
        cod_expe = row['cod_expe'].strip()
        cod_deli = row['cod_deli'].strip()
        muocurri_raw = row['muocurri'].strip()
        muocurri = muocurri_raw.zfill(5) if muocurri_raw not in ['99999', '99', '9', ''] else '99999'

        # Audit de Clave Primaria (ubicgeoc, cod_expe, cod_deli)
        pk = (ubicgeoc, cod_expe, cod_deli)
        if pk in pk_set:
            pk_duplicates += 1
        else:
            pk_set.add(pk)

        # 3.2 Mapeo de valores centinela categónicos a nulo (cadena vacía)
        delirie8 = row['delirie8'].strip()
        califide = '' if row['califide'].strip() in ['9', ''] else row['califide'].strip()
        consumac = '' if row['consumac'].strip() in ['9', ''] else row['consumac'].strip()
        forcomis = '' if row['forcomis'].strip() in ['9', ''] else row['forcomis'].strip()
        foraccio = '' if row['foraccio'].strip() in ['9', ''] else row['foraccio'].strip()
        modadel  = '' if row['modadel'].strip()  in ['9', ''] else row['modadel'].strip()
        ele_comi = row['ele_comi'].strip()
        ticoncur = row['ticoncur'].strip()
        clasitip = '' if row['clasitip'].strip() in ['9', ''] else row['clasitip'].strip()
        entiocur = '' if row['entiocur'].strip() in ['9', '99', ''] else row['entiocur'].strip()
        muocurri_val = '' if muocurri == '99999' else muocurri

        # 3.3 Parseo y corrección de fechas
        fec_raw = row['fec_ocur'].strip()
        fec_iso = ''
        fec_anio = ''
        fec_mes = ''
        fec_es_identificada = 'False'

        if fec_raw != 'NO IDENTIFICADA' and fec_raw != '':
            parts = fec_raw.split('/')
            if len(parts) == 3:
                dd, mm, yyyy = parts[0], parts[1], parts[2]
                if yyyy not in ['1899', '1969'] and int(yyyy) >= 1970:
                    fec_iso = f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
                    fec_anio = yyyy
                    fec_mes = mm.zfill(2)
                    fec_es_identificada = 'True'
                else:
                    dates_repaired += 1
            else:
                dates_repaired += 1

        # 3.4 Conteo de imputados y víctimas (NSS y 9 a nulo)
        totalca1_raw = row['totalca1'].strip()
        totalca2_raw = row['totalca2'].strip()
        totalca1 = '' if totalca1_raw in ['NSS', '9', ''] else totalca1_raw
        totalca2 = '' if totalca2_raw in ['NSS', '9', ''] else totalca2_raw

        # Fila limpia
        row_limpia = [
            ubicgeoc, cod_expe, cod_deli, delirie8, califide,
            consumac, forcomis, foraccio, modadel, ele_comi,
            ticoncur, clasitip, entiocur, muocurri_val,
            fec_raw, fec_iso, fec_anio, fec_mes, fec_es_identificada,
            totalca1, totalca2
        ]

        # 3.5 Enriquecimiento con descripciones de catálogos
        desc_delito   = get_catalog_desc('delirie8', delirie8)
        desc_califide = get_catalog_desc('califide', califide)
        desc_consumac = get_catalog_desc('consumac', consumac)
        desc_forcomis = get_catalog_desc('forcomis', forcomis)
        desc_foraccio = get_catalog_desc('foraccio', foraccio)
        desc_modadel  = get_catalog_desc('modadel', modadel)
        desc_elecomi  = get_catalog_desc('ele_comi', ele_comi)
        desc_ticoncur = get_catalog_desc('ticoncur', ticoncur)
        desc_clasitip = get_catalog_desc('clasitip', clasitip)
        desc_entiocur = get_catalog_desc('entiocur', entiocur)
        desc_muocurri = get_catalog_desc('muocurri', muocurri_val)
        desc_ubicgeoc = get_catalog_desc('ubicgeoc', ubicgeoc)

        row_enriquecida = row_limpia + [
            desc_delito, desc_califide, desc_consumac,
            desc_forcomis, desc_foraccio, desc_modadel,
            desc_elecomi, desc_ticoncur, desc_clasitip,
            desc_entiocur, desc_muocurri, desc_ubicgeoc
        ]

        writer_limpio.writerow(row_limpia)
        writer_enri.writerow(row_enriquecida)

# ---------------------------------------------------------
# 4. REPORTES DE VALIDACIÓN Y CONTROL DE CALIDAD
# ---------------------------------------------------------
print("\n[Fase 3/4] Validando integridad de los datos procesados...")
print(f"  ✔ Registros totales procesados: {total_rows}")
print(f"  ✔ Registros con Clave Primaria única: {len(pk_set)}")
print(f"  ✔ Claves Primarias duplicadas: {pk_duplicates}")
print(f"  ✔ Fechas anómalas (1899/1969) reasignadas a nulo: {dates_repaired}")

print("\n[Fase 4/4] Archivos generados exitosamente en 'datos_procesados/':")
print(f"  1. Dataset Limpio: {output_limpio_csv}")
print(f"  2. Dataset Enriquecido (con Catálogos): {output_enriquecido_csv}")
print("\n=== PIPELINE DE LIMPIEZA FINALIZADO CON ÉXITO ===")
