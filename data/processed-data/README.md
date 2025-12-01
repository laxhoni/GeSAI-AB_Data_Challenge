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
