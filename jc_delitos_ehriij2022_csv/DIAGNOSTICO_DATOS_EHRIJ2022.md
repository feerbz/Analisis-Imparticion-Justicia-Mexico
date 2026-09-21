# Diagnóstico de Estructura y Calidad de Datos - EHRIJ 2022 (Delitos en Juzgados de Control)

**Fecha de análisis:** Septiembre 2026  
**Ubicación de la carpeta:** `/home/diana/Escritorio/jc_delitos_ehriij2022_csv`  
**Fuente de datos:** INEGI - Estadística de Judicialización en Materia Penal (EHRIJ 2022 / Causas Penales 2021)

---

## 1. Estructura General de los Archivos

La carpeta contiene un esquema estandarizado de difusión de datos del INEGI compuesto por datos, diccionario, metadatos, catálogos y modelo de entidad-relación.

| Componente | Ruta / Archivo | Codificación | Formato | Descripción / Tamaño |
| :--- | :--- | :--- | :--- | :--- |
| **Conjunto de datos principal** | `conjunto_de_datos/delit_jc_ehriij2022.csv` | `UTF-8` | CSV | **404,264 filas × 17 columnas** (~27 MB) |
| **Diccionario de datos** | `diccionario_de_datos/diccionario_de_datos_jc_delitos_ehriij2022.csv` | `UTF-8` | CSV | 17 registros descriptivos de variables |
| **Catálogos de referencia** | `catalogos/*.csv` (12 archivos) | `UTF-8` | CSV | Tablas de codificación (delitos, ubicación, modalidades, etc.) |
| **Metadatos** | `metadatos/metadatos_ehriij_2022.txt` | `Latin-1` | TXT | Descripción metodológica y alcance del censo |
| **Modelo ER** | `modelo_entidad_relacion/modelo_er_jc_delitos_ehriij2022.png` | N/A | PNG | Diagrama Entidad-Relación |
| **Artefacto corrupto/residual** | `metadatos\` | N/A | Archivo | **0 bytes**, creado por residuo de descompresión en Windows |

> [!WARNING]
> Existe un archivo residual inservible llamado `metadatos\` (de 0 bytes) generado por un error de secuencias de escape de separadores de directorio en Windows. Se recomienda su eliminación en la fase inicial.

---

## 2. Tratamiento de Valores Nulos e Imputación Implícita

El dataset **no contiene valores vacíos estándar (`""` o `NaN` directos)** en ninguna de sus 17 columnas. En su lugar, el INEGI utiliza **códigos centinela de dominio** para representar valores no especificados o no identificados:

| Columna | Nombre Descriptivo | Código Centinela | Descripción del Centinela | Registros Afectados | % del Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `clasitip` | Clasificación típica del delito | `9` | No especificado | 247,175 | **61.14%** |
| `foraccio` | Forma de acción del delito | `9` | No especificado | 222,689 | **55.09%** |
| `fec_ocur` | Fecha de ocurrencia del delito | `'NO IDENTIFICADA'` | Fecha no identificada | 209,949 | **51.93%** |
| `modadel` | Modalidad del delito | `9` | No especificado | 206,742 | **51.14%** |
| `califide` | Calificación del delito | `9` | No especificado | 197,847 | **48.94%** |
| `forcomis` | Forma de comisión | `9` | No especificado | 136,920 | **33.87%** |
| `consumac` | Grado de consumación | `9` | No especificado | 134,060 | **33.16%** |
| `entiocur` | Entidad federativa de ocurrencia | `99` / `9` | No identificado / No especificado | 55,548 | **13.74%** |
| `muocurri` | Municipio de ocurrencia | `99999` | No identificado / No especificado | 30,902 | **7.64%** |
| `totalca2` | Total de víctimas | `'NSS'` / `9` | No Se Sabe / No especificado | 30,443 | **7.53%** |
| `totalca1` | Total de imputados | `'NSS'` / `9` | No Se Sabe / No especificado | 5,153 | **1.27%** |

> [!IMPORTANT]
> Convertir ciega o directamente la columna entera a entero o fecha fallará debido a la presencia de cadenas como `'NO IDENTIFICADA'` y `'NSS'`, así como valores numéricos centinelas (`9`, `99`, `99999`). Requiere una estrategia de mapeo explícita a `NaN` o a tipos anulables (*nullable types*).

---

## 3. Manejo de Duplicados e Identificadores Únicos

1. **Filas duplicadas exactas:** **0 filas duplicadas** (el 100% de las 404,264 filas son distintas en al menos un atributo).
2. **Clave Primaria compuesta:** Se evaluó la combinación `(ubicgeoc, cod_expe, cod_deli)` (Órgano Jurisdiccional + Código de Causa Penal / Expediente + Código de Delito):
   - **Resultado:** **404,264 combinaciones únicas**.
   - **Conclusión:** La tupla `(ubicgeoc, cod_expe, cod_deli)` garantiza una identificación unívoca para cada registro de delito dentro del dataset.

---

## 4. Conversión de Tipos de Datos (*Type Casting*)

Todas las columnas son leídas originalmente como tipos `object` (cadenas de texto). A continuación se resume la naturaleza de cada columna y su tipo de destino recomendado:

| Columna | Tipo Actual | Tipo Destino Recomendado | Razón / Transformación |
| :--- | :--- | :--- | :--- |
| `ubicgeoc` | Texto/String | `String` (formato `05000`) | Código INEGI de ubicación del juzgado (5 dígitos, preserva ceros a la izquierda). |
| `cod_expe` | Texto/String | `Int64` / `String` | Identificador único de la causa penal / expediente. |
| `cod_deli` | Texto/String | `Int64` / `String` | Identificador secuencial del delito dentro del expediente. |
| `delirie8` | Texto/String | `Categorical` / `String` | Clasificación de delito (ej: `30500`). Enlaza con `catalogos/delirie8.csv`. |
| `califide` .. `clasitip` | Texto/String | `Int64` (Nullable) / `Categorical` | Códigos categóricos (`1`, `2`, `9` -> `NaN`). |
| `entiocur` | Texto/String | `Categorical` (Nullable) | Entidad federativa de ocurrencia (códigos `01` a `32`, `99` -> `NaN`). |
| `muocurri` | Texto/String | `String` (formato `01001`) | Municipio de ocurrencia (5 dígitos, ceros iniciales, `99999` -> `NaN`). |
| `fec_ocur` | Texto/String | `Date` (Nullable) | Fechas `'DD/MM/YYYY'` parsed a `YYYY-MM-DD`, y `'NO IDENTIFICADA'` mapeado a `NaT`/`NaN`. |
| `totalca1` | Texto/String | `Int64` (Nullable) | Conteo de imputados (`'NSS'` y `9` mapeados a `NaN` o centinela cuantitativo). |
| `totalca2` | Texto/String | `Int64` (Nullable) | Conteo de víctimas (`'NSS'` y `9` mapeados a `NaN` o centinela cuantitativo). |

---

## 5. Estandarización de Formato y Normalización de Nombres

### Normalización de Nombres de Columnas
- **Discrepancia detectada:** El diccionario de datos lista los campos en **MAYÚSCULAS** (`UBICGEOC`, `COD_EXPE`, `FEC_OCUR`), mientras que la cabecera del CSV utiliza **minúsculas** (`ubicgeoc`, `cod_expe`, `fec_ocur`).
- **Recomendación:** Adoptar la convención estándar `snake_case` en minúsculas y homogénea para todo el pipeline de análisis.

### Formato de Ceros a la Izquierda (*Zero Padding*)
- Columnas geográficas como `ubicgeoc` y `muocurri` requieren mantener los 5 caracteres con ceros a la izquierda (ejemplo: `'01001'` representa el municipio de Aguascalientes). Convertirlas a entero simple convertiría `'01001'` en `1001`, rompiendo los cruces con los catálogos geográficos `ubicgeoc.csv` y `muocurri.csv`.

---

## 6. Revisión de Valores Inválidos, Anómalo y Errores de Dominio

### Análisis de Fechas en `fec_ocur`
De las 404,264 filas:
- **`NO IDENTIFICADA`:** 209,949 registros (51.93%).
- **Fechas estructuradas (`DD/MM/YYYY`):** 194,315 registros (48.07%).

Al analizar el rango de años en las fechas estructuradas, se identificaron **anomalías severas por defectos de sistemas de origen o conversión de hojas de cálculo**:

```
Distribución de Años Anómalos / Outliers Históricos:
- Year 1899: 2 registros (Ej: 15/09/1899 y 25/09/1899) -> Error clásico de época base 0 de Excel.
- Year 1969: 171 registros (169 son 31/12/1969) -> Error de timestamp nulo de Unix (epoch -1).
- Years 1918 - 1958: 10 registros históricos inverosímiles para un censo 2021/2022.
- Years 2014 - 2021: Concentra el 98.5% del volumen válido (2021 cuenta con 83,308 registros).
```

> [!CAUTION]
> Los 169 registros con fecha `31/12/1969` y los 2 con año `1899` **no son fechas reales de delitos**, sino banderas de error de sistema importadas por los juzgados de origen. Deben ser tratados como valores no identificados o imputados como `NaT`.

### Integridad Referencial con Catálogos
Se evaluaron las claves de las columnas categóricas contra los 12 archivos de la carpeta `catalogos/`:
- **Resultado:** El **100% de las claves válidas** presentes en el dataset existen en las tablas maestras de catálogos (`delirie8`, `califide`, `consumac`, `forcomis`, `foraccio`, `modadel`, `ele_comi`, `ticoncur`, `clasitip`, `entiocur`, `muocurri`, `ubicgeoc`).

### Consistencia Cruzada (`entiocur` vs `muocurri`)
- Se verificó que los dos primeros dígitos de la clave de municipio `muocurri` coincidan con la entidad federativa `entiocur`.
- **Resultado:** **0 inconsistencias encontradas** entre entidad y municipio en los registros identificados.

---

## 7. Matriz Resumen Diagnóstica

| Aspecto Evaluado | Estado | Criticidad | Acción Requerida |
| :--- | :--- | :--- | :--- |
| **Estructura de Archivos** | Requiere Limpieza | Baja | Eliminar archivo residual `metadatos\` |
| **Valores Nulos** | Implícitos (Centinelas) | **Alta** | Mapear `9`, `99`, `99999`, `'NO IDENTIFICADA'`, `'NSS'` a `NaN`/`NaT` |
| **Duplicados** | Limpio (0 duplicados) | Ninguna | Usar `(ubicgeoc, cod_expe, cod_deli)` como Clave Primaria |
| **Conversión de Tipos** | Requiere Parseo | **Alta** | Convertir fechas a ISO-8601, `totalca1`/`totalca2` a enteros numéricos |
| **Formato y Normalización** | Requiere Formateo | Media | Estandarizar ceros a la izquierda en claves geográficas (5 dígitos) |
| **Valores Inválidos / Anómalos** | Fechas anómalas (1899/1969) | **Alta** | Filtrar o sustituir fechas irreales (< 1970) por `NaT` |
| **Catálogos** | Integridad 100% Válida | Ninguna | Unir con catálogos para enriquecimiento textual |
