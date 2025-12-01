# 🗂️ Documentación del data lake: GeSAI

Este directorio almacena y gestiona el ciclo de vida de los datos del proyecto, desde la ingesta de fuentes crudas hasta la generación de artefactos para el modelo predictivo.

La estrategia de datos se basa en el enriquecimiento contextual: no analizamos el consumo de agua en el vacío, sino que lo cruzamos con factores **físicos** (infraestructura), **ambientales** (clima) y **sociales** (demografía) para entender la *causalidad* de las anomalías.

---

## 1. Official data (`data/official-data/`)
*Datos propietarios proporcionados por la organización del AB Data Challenge.*

* **Archivo:** `data_ab3_complete.parquet`
* **Volumen:** >75 Millones de registros.
* **Descripción:** Registro histórico de telelectura horaria de contadores de agua.
* **Justificación:** Es la fuente de verdad (*Ground Truth*) del proyecto. Contiene la serie temporal del consumo (`CONSUMO_REAL`) y las etiquetas históricas de fugas (`FUGA_DETECTADA`), que actúan como la variable objetivo (*Target*) para el entrenamiento supervisado del modelo LightGBM.

---

## 2. Open data (`data/open-data/`)
*Fuentes externas de datos abiertos utilizadas para enriquecer el dataset oficial (Data Enrichment).*

### A. Infraestructura y urbanismo
Factores físicos que afectan a la probabilidad de avería o a la interpretación del consumo.

* **Catastro: Edad de las edificaciones**
    * **Fuente:** [Ajuntament de Barcelona - Catastro](https://opendata-ajuntament.barcelona.cat/data/es/dataset/est-cadastre-edificacions-any-const/resource/f0af7dd5-2550-4acb-af97-c1a2dceb31ee#additional-info)
    * **Archivo:** `antiguitat_pivotada.csv`
    * **Justificación de Valor:** La antigüedad del parque inmobiliario es el predictor físico más fuerte de una fuga estructural. Cruzar el consumo con la edad del edificio permite al modelo distinguir entre un *pico de consumo humano* y una *rotura por fatiga de materiales* en redes antiguas (>50 años).

* **Obras en la vía pública**
    * **Fuente:** [Ajuntament de Barcelona - Obras](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/obres)
    * **Archivo:** `obres_procesadas.csv`
    * **Justificación de Valor:** **Reducción de Falsos Positivos.** Las obras cercanas pueden causar fluctuaciones de presión o cortes que alteran la telelectura. Al incorporar esta variable, el modelo aprende a no alertar sobre anomalías que coinciden espacio-temporalmente con intervenciones activas en la calle.

### B. Contexto socioeconómico y demográfico
Datos clave para la detección de vulnerabilidad y la gestión de la brecha digital.

* **Renta familiar disponible**
    * **Fuente:** [Ajuntament de Barcelona - Renta](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/renda-disponible-llars-bcn/resource/3df0c5b9-de69-4c94-b924-57540e52932f)
    * **Archivo:** `renda_procesada.csv`
    * **Justificación de Valor:** Permite identificar patrones de consumo asociados al nivel socioeconómico (ej. mayor uso en zonas con jardines/piscinas vs. consumo esencial). Además, ayuda a priorizar la atención en zonas de vulnerabilidad económica donde una factura elevada por fuga tiene un impacto crítico.

* **Estructura de edades (Padrón)**
    * **Fuente:** [Ajuntament de Barcelona - Padrón](https://portaldades.ajuntament.barcelona.cat/ca/microdades/33dd918f-bbf1-4b1a-8898-6bb8709f8139)
    * **Archivo:** `poblacion_pivotada.csv`
    * **Justificación de Valor:** **Gestión de la Brecha Digital.** Detectamos secciones censales con alta densidad de población >65 años. Esta variable no solo ajusta la predicción de consumo (patrones más estables), sino que alimenta la lógica de negocio para priorizar el envío de **Cartas Postales** en lugar de notificaciones digitales.

### C. Contexto ambiental
Variables exógenas que justifican variaciones de consumo.

* **Meteorología histórica (AEMET)**
    * **Fuente:** [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/inicio)
    * **Archivos:** `data_aemet_1.json`, `data_aemet_2.json`
    * **Justificación de Valor:** Elimina el ruido estacional. El consumo de agua correlaciona directamente con la temperatura (duchas, hidratación) e inversamente con la precipitación (riego). Al "explicar" estos picos con datos climáticos, el modelo aísla mejor las anomalías que *no* tienen justificación ambiental (fugas reales).

### D. Marco geoespacial
La llave maestra para la integración.

* **Cartografía de Distritos y Barrios**
    * **Fuente:** [Cartografía BCN](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/20170706-districtes-barris/resource/cd800462-f326-429f-a67a-c69b7fc4c50a)
    * **Uso:** Permite realizar *Spatial Joins*. Dado que las obras tienen coordenadas (X, Y) y los contadores tienen Sección Censal, este dataset actúa como el traductor geométrico que permite vincular una obra en una calle concreta con los abonados afectados en esa zona.

---

## 3. Processed data (`data/processed-data/`)
*Artefactos generados por el pipeline de Ingeniería de Datos y Modelado.*

* **`dataset_FINAL_COMPLETO.parquet`**:
    * El **Dataset maestro**. Resultado de limpiar el *Official Data* y enriquecerlo con todos los *Open Data* anteriores mediante Dask. Es la matriz de entrada para el entrenamiento.
* **`datos_simulacion_features.csv`**:
    * Subconjunto de datos "futuros" (Test Set) con la ingeniería de características ya aplicada (Lags, Rolling Means). Es el combustible que alimenta la **Demo en Tiempo Real** (`simulador_backend.py`).
* **`analisis_predicciones.csv`**:
    * Log de resultados del modelo (Predicción vs Realidad). Utilizado por el notebook de **Meta-Análisis** para ajustar los umbrales de decisión y validar el impacto económico.
* **Modelos `.joblib`**:
    * `lgbm_model_TARGET_HOY.joblib`, `...MANANA.joblib`, `...7DIAS.joblib`: Los cerebros entrenados listos para inferencia.
