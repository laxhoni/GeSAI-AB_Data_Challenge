## 1. Official data (`data/official-data/`)
*Datos propietarios proporcionados por la organización del AB Data Challenge.*

* **Archivo:** `data_ab3_complete.parquet`
* **Volumen:** >75 Millones de registros.
* **Descripción:** Registro histórico de telelectura horaria de contadores de agua.
* **Justificación:** Es la fuente de verdad (*Ground Truth*) del proyecto. Contiene la serie temporal del consumo (`CONSUMO_REAL`) y las etiquetas históricas de fugas (`FUGA_DETECTADA`), que actúan como la variable objetivo (*Target*) para el entrenamiento supervisado del modelo LightGBM.
