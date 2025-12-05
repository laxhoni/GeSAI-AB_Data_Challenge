# GeSAI Project Notebooks 

Este directorio contiene el flujo de trabajo secuencial ("Pipeline") de Ciencia de Datos desarrollado para el proyecto GeSAI. Los *notebooks* están numerados para asegurar la reproducibilidad de los experimentos, desde la ingesta de datos crudos hasta la validación de negocio y la auditoría de seguridad.

-----

## Índice de Notebooks

### [01\_data\_preparation.ipynb](https://www.google.com/search?q=data-preparation.ipynb)

**Ingeniería de Datos y ETL Distribuido**

Este *notebook* aborda el desafío de procesar el dataset masivo proporcionado por Aigües de Barcelona ($>75$ millones de registros) superando las limitaciones de memoria RAM local.

  * **Tecnología:** Utilización de **Dask** para procesamiento paralelo y *lazy evaluation*.
  * **Fusión de Datos (Data Enrichment):** Integración del dataset de consumo con fuentes de *Open Data*:
      * **Meteorología (AEMET):** Temperatura y precipitación histórica.
      * **Catastro:** Antigüedad de los edificios.
      * **Socioeconómico:** Renta familiar disponible.
  * **Limpieza:** Imputación de valores nulos, corrección de tipos de datos y eliminación estricta de duplicados.
  * **Salida:** Generación del archivo maestro `dataset_FINAL_COMPLETO.parquet`.

### [02\_model\_training.ipynb](https://www.google.com/search?q=model-training.ipynb)

**Entrenamiento, Optimización y Exportación de Modelos**

Núcleo del modelado predictivo. Se justifica el cambio de arquitectura de LSTM (Redes Recurrentes) a **LightGBM** (Gradient Boosting) por eficiencia y rendimiento en datos tabulares.

  * **Feature Engineering Avanzado:** Creación de variables sintéticas para capturar la temporalidad sin usar redes recurrentes:
      * *Lags* (Retardos): Consumo hace 1h, 24h, 7 días.
      * *Rolling Windows*: Medias móviles y desviación estándar semanal.
      * *Ratios*: Desviación del consumo actual respecto a la media histórica.
  * **Estrategia Multi-Horizonte:** Entrenamiento de tres modelos independientes para predecir la probabilidad de fuga en:
    1.  **Target HOY:** Riesgo inmediato.
    2.  **Target MAÑANA:** Proyección a 24 horas.
    3.  **Target 7 DÍAS:** Proyección estructural a una semana.
  * **Optimización (Threshold Tuning):** Análisis de sensibilidad para ajustar el umbral de decisión (fijado finalmente en **0.30**) para maximizar el *F1-Score* y el *Recall*.
  * **Salida:** Exportación de modelos `.joblib` y el dataset de simulación `datos_simulacion_features.csv`.

### [03\_meta\_analysis.ipynb](https://www.google.com/search?q=prediction-meta-analysis.ipynb)

**Meta-Análisis y Lógica de Negocio**

Este *notebook* no entrena modelos, sino que define las reglas de negocio que interpretan las predicciones de la Inteligencia Artificial. Transforma una probabilidad matemática en una decisión operativa.

  * **Cálculo de Deltas:** Análisis de la derivada del riesgo (diferencia entre la probabilidad futura y la actual) para identificar tendencias.
      * `Delta Corto = Prob. Mañana - Prob. Hoy`
      * `Delta Largo = Prob. 7 Días - Prob. Hoy`
  * **Matriz de Decisión (Semáforo):** Implementación de la lógica jerárquica para clasificar las incidencias:
      * 🔴 **Fuga Grave:** Probabilidad crítica o crecimiento acelerado.
      * 🟠 **Fuga Moderada:** Alta probabilidad pero estable.
      * 🟢 **Fuga Leve / No Fuga:** Riesgo bajo o decreciente.
  * **Validación:** Visualización de la distribución de alertas para confirmar la reducción de falsos positivos.

### [04\_xai\_explainability.ipynb](https://www.google.com/search?q=prediction-XAI.ipynb)

**Explicabilidad del Modelo (XAI)**

Enfoque de "Caja Blanca" para garantizar la transparencia y confianza en el algoritmo.

  * **Metodología:** Uso de **SHAP (SHapley Additive exPlanations)**.
  * **Análisis Global:** Identificación de las variables más influyentes en el modelo (ej. Consumo mínimo nocturno, Antigüedad del contador).
  * **Análisis Local:** Explicación caso por caso. Permite responder a la pregunta: *"¿Por qué el sistema ha marcado esta lectura específica como una fuga grave?"*, desglosando la contribución de cada variable a la puntuación final.

### [05\cyber\_security\_.ipynb](https://www.google.com/search?q=05_Security_Audit.ipynb)

**Auditoría de Seguridad y Criptografía**

Validación técnica de las medidas de ciberseguridad implementadas en la aplicación final, demostrando el cumplimiento de estándares de protección de datos (RGPD) e integridad documental.

  * **Protección de Datos (Confidencialidad):** Simulación de un ataque de extracción de datos ("Dump SQL") para demostrar que la información personal (PII) está cifrada con **AES-128** y es ilegible sin la clave maestra.
  * **Gestión de Credenciales:** Verificación de la resistencia del algoritmo de hashing **Scrypt** frente a ataques de diccionario y fuerza bruta.
  * **Firma Digital (Integridad):** Generación y validación de firmas criptográficas (**RSA-2048 / PKI**) para certificar la autenticidad e inmutabilidad de los informes PDF generados por el sistema.

-----

## Requisitos de Ejecución

Para ejecutar estos *notebooks* en el orden correcto, asegúrese de instalar las dependencias listadas en `requirements.txt` en la raíz del proyecto.

**Orden de Ejecución Recomendado:**

1.  `01_data_preparation.ipynb` (Genera los datos limpios).
2.  `02_model_training.ipynb` (Entrena y guarda los modelos).
3.  `03_meta_analysis.ipynb` (Valida las reglas de negocio).
4.  `04_prediction_XAI.ipynb` (Genera gráficos de interpretación).
5.  `05_cyber_security.ipynb` (Verifica la seguridad y criptografía).
