# Propuesta Técnica: Data Mart Relacional de Impartición de Justicia Criminal

## 1. Nombre del Data Mart

**Data Mart Relacional de Estadística Judicial y Caracterización de Delitos Penales (EHRIIJ 2022)**

---

## 2. Problema Actual

El Instituto Nacional de Estadística y Geografía (INEGI) publica los datos del *Esquema Homologado de Recolección de Información de Impartición de Justicia 2022 (EHRIIJ 2022)* en archivos planos CSV desagregados: un registro transaccional masivo de **404,265 eventos delictivos** y **12 archivos independientes de catálogos normalizados** (`delirie8`, `ubicgeoc`, `forcomis`, `ele_comi`, `consumac`, etc.).

Esta disposición genera las siguientes deficiencias para el análisis analítico:

1. **Degradación por Consultas Complejas:** Analizar correlaciones multidimensionales (por ejemplo, cruzar el tipo penal con el arma empleada, el grado de consumación y la demografía municipal) exige encadenar múltiples `JOINs` sobre catálogos normalizados transaccionales (3FN), degradando el rendimiento analítico.
2. **Sobrecarga en el Motor de BI:** Cargar 13 archivos desconectados directamente a Power BI satura la memoria del motor VertiPaq, genera modelos relacionales desordenados y eleva la complejidad de las métricas calculadas en DAX.
3. **Falta de Integridad y Tipado Robusto:** Los archivos planos carecen de restricciones de integridad referencial, tipos de datos fuertemente definidos y estrategias de indexación columnar para auditoría y consulta masiva.

---

## 3. Objetivos

### Objetivo General

Diseñar e implementar un **Data Mart relacional bajo un esquema dimensional en Microsoft SQL Server**, respaldado por un pipeline **ETL automatizado en Python (Pandas / SQLAlchemy)** y tableros analíticos en **Power BI**, para centralizar, consolidar y explotar eficientemente los datos estadísticos de delitos penales registrados en los Juzgados de Control en México (2022).

### Objetivos Específicos

1. **Análisis Geográfico de Incidencia Delictiva:** Centralizar los catálogos territoriales en una dimensión geográfica unificada para evaluar la densidad delictiva a nivel estatal y municipal, fundamentando la asignación eficiente de recursos judiciales y personal en zonas de alta prioridad.
2. **Caracterización de Violencia y Modus Operandi:** Diseñar dimensiones descriptivas sobre los medios de comisión (armas de fuego, armas blancas, fuerza física) y la intencionalidad (dolo vs. culpa) para correlacionar la severidad penal y respaldar el diagnóstico de seguridad pública.
3. **Análisis Temporal y Carga Operativa:** Construir una dimensión de tiempo estructurada que permita evaluar estacionalidad, tendencias mensuales y patrones por día de la semana, facilitando la proyección de demanda procesal en los órganos jurisdiccionales.

---

## 4. Arquitectura de Solución y Modelo de Datos

### Diagrama de Arquitectura de Extremo a Extremo

El siguiente diagrama representa la arquitectura propuesta para el Data Mart de Impartición de Justicia Criminal, desde la extracción de los datos originales hasta su explotación analítica en Power BI.

![Diagrama de Arquitectura](docs/arquitectura.png)
    

### Estructura del Modelo Dimensional (Star Schema)

En lugar de colecciones de documentos desnormalizados, SQL Server organiza la información en un modelo estrella:

* **Tabla de Hechos (`Fact_Delitos`):**
* `ID_Delito` (PK)
* `SK_Geografia` (FK)
* `SK_TipoDelito` (FK)
* `SK_ModusOperandi` (FK)
* `SK_Consumacion` (FK)
* `SK_Fecha` (FK)
* *Métricas:* `Cantidad_Delitos` (conteo base = 1), indicadores binarios de violencia.

* **Tablas de Dimensiones (`Dim_*`):**
* `Dim_Geografia`: Entidad federativa, municipio, clave INEGI.
* `Dim_TipoDelito`: Clasificación penal nacional, fuero, bien jurídico afectado.
* `Dim_ModusOperandi`: Forma de comisión (dolosa/culposa), elemento de comisión (arma de fuego, punzocortante, etc.).
* `Dim_Consumacion`: Grado de consumación (consumado, tentativa).
* `Dim_Tiempo`: Fecha del hecho, mes, trimestre, día de la semana, fin de semana (flag).

---

## 5. Stack Tecnológico

| Componente | Tecnología | Rol en la Solución |
| --- | --- | --- |
| **Almacenamiento Analítico** | **Microsoft SQL Server** | Motor de base de datos relacional para el Data Mart dimensional, optimizado con índices por columnas (*Columnstore*). |
| **Ingesta y Transformación (ETL)** | **Python (Pandas, SQLAlchemy)** | Lectura de archivos CSV, estandarización de tipos, imputación de nulos y carga estructurada mediante sentencias de inserción masiva. |
| **Modelado y Visualización** | **Power BI Desktop** | Modelado semántico mediante DAX, segmentación interactiva y publicación de tableros ejecutivos. |

