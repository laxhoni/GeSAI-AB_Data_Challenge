# GeSAI: Gestió Segura i Automatitzada d'Incidències
> **Aigües de Barcelona Data Challenge** | Team GeSAI | UPF

## Resumen Ejecutivo
**GeSAI** es una plataforma integral para la detección temprana y gestión de fugas de agua. Combina un modelo de **Inteligencia Artificial (LightGBM)** entrenado con más de 75 millones de registros para predecir anomalías, con un sistema de **Meta-Análisis** que prioriza la gravedad según la tendencia futura.

El sistema destaca por su enfoque híbrido en la comunicación: notificaciones digitales automáticas y generación de **cartas postales físicas** para clientes afectados por la brecha digital.

# Estructura del Proyecto

A continuación se detalla la organización de carpetas y archivos del sistema GeSAI:

```text
GeSAI-AB_Data_Challenge/
│
├── .gitignore                  # Archivos y carpetas a excluir del control de versiones (ej. venv, __pycache__)
├── gesai.db                    # Base de datos SQLite principal (Persistencia de incidencias, clientes y usuarios)
├── LICENSE                     # Licencia del proyecto
├── README.md                   # Documentación general del proyecto
├── requirements.txt            # Lista de dependencias Python necesarias (pip install -r requirements.txt)
│
├── .vscode/                    # Configuración del entorno de desarrollo
│   └── settings.json
│
├── data/                       # Almacenamiento de datos (Inputs y Outputs)
│   ├── README.md
│   ├── official-data/          # Datos originales proporcionados por el reto (Raw Data)
│   │   ├── data_ab3_complete.parquet # Dataset oficial del reto (75M+ registros de consumo horario y fugas)
│   │   └── README.md
│   │
│   ├── open-data/              # Fuentes de datos abiertas externas (Enriquecimiento)
│   │   ├── antiguitat_pivotada.csv # Datos de catastro (edad edificios por sección censal)
│   │   ├── data_aemet_1.json       # Histórico meteorológico oficial (Parte 1)
│   │   ├── data_aemet_2.json       # Histórico meteorológico oficial (Parte 2)
│   │   ├── obres_procesadas.csv    # Datos de obras públicas activas en Barcelona
│   │   ├── poblacion_pivotada.csv  # Datos demográficos por sección censal
│   │   ├── renda_procesada.csv     # Datos socioeconómicos (Renta media por barrio)
│   │   └── README.md
│   │
│   └── processed-data/         # Datos procesados y Modelos (Artifacts)
│       ├── dataset_FINAL_COMPLETO/     # Dataset maestro enriquecido y procesado con Dask (formato Parquet)
│       ├── analisis_predicciones.csv   # Resultados del entrenamiento (Probabilidades y Deltas) para análisis
│       ├── datos_simulacion_features.csv # Dataset limpio con features calculadas (Lags/Rolling) para la simulación
│       ├── lgbm_model_TARGET_7DIAS.joblib  # Modelo IA entrenado (Predicción a 7 días vista)
│       ├── lgbm_model_TARGET_HOY.joblib    # Modelo IA entrenado (Predicción inmediata)
│       └── lgbm_model_TARGET_MANANA.joblib # Modelo IA entrenado (Predicción a 24h)
│
├── docs/                       # Documentación adicional sobre la gestión del proyecto
│   └── README.md
│
├── generated_reports/          # Salida de archivos generados por el sistema (PDFs)
│   ├── regular_mails/          # Cartas postales generadas automáticamente para clientes sin contacto digital
│   └── technical_reports/      # Informes técnicos detallados con gráficas para uso interno de la empresa
│
├── project-notebooks/          # Laboratorio de Data Science (Jupyter Notebooks)
│   ├── data-preparation.ipynb          # Notebook 1: ETL distribuido con Dask, limpieza y enriquecimiento de datos
│   ├── model-training.ipynb            # Notebook 2: Entrenamiento LightGBM, optimización de umbrales y exportación
│   ├── prediction-meta-analysis.ipynb  # Notebook 3: Definición de reglas de negocio, deltas y clasificación de gravedad
│   ├── prediction-XAI.ipynb            # Notebook 4: Explicabilidad del modelo (SHAP values) para caja blanca
│   └── README.md
│
└── src/                        # Código Fuente de la Aplicación (Producción)
    ├── app.py                  # Frontend: Dashboard web interactivo para gestores (Dash/Plotly)
    ├── motor_gesai.py          # Core: "Cerebro" del sistema. Orquesta IA, BBDD y reglas de negocio
    ├── reports_manager.py      # Módulo: Generador de PDFs profesionales (Cartas e Informes) con FPDF
    ├── setup_database.py       # Script: Inicialización de BBDD, creación de tablas y seeding de datos realistas
    ├── simulacion_backend.py   # Backend: Worker autónomo que simula la entrada de datos IoT en tiempo real
    ├── test_report.py          # Script de pruebas unitarias para la generación de informes PDF
    ├── __init__.py             # Archivo de inicialización del paquete Python
    │
    └── assets/                 # Recursos estáticos para la interfaz web
        ├── ios_homescreen.jpg  # Recurso gráfico para el marco del simulador móvil
        ├── logo_1.png          # Logo corporativo principal (Versión Login)
        ├── logo_2.png          # Logo corporativo secundario (Versión Header/PDF)
        └── style.css           # Hoja de estilos personalizada (Look & Feel Enterprise)
```

## Arquitectura Técnica

El sistema sigue un patrón de **Microservicios Desacoplados**:

1.  **Capa de Datos (ETL):** Procesamiento distribuido con **Dask** para manejar grandes volúmenes de datos históricos.
2.  **Capa de Inteligencia (AI Core):** Tres modelos **LightGBM** independientes predicen el riesgo a corto, medio y largo plazo.
3.  **Capa de Negocio (Meta-Análisis):** Un motor lógico evalúa los "Deltas" (tendencias de probabilidad) para clasificar la fuga como *Grave*, *Moderada* o *Leve*.
4.  **Capa de Presentación (App):** Interfaz web construida con **Dash/Plotly** que se actualiza en tiempo real mediante lectura de BBDD.

---

## Guía de ejecución (Demo)

Para levantar el entorno completo de simulación en local:

### 1. Instalación de las dependencias requeridas
```bash 
pip install -r requirements.txt
```

### 2. Inicialización de BBDD
Este script crea las tablas y genera 50 clientes sintéticos (mezclando perfiles digitales y analógicos).

```bash 
cd src
python setup_database.py
```

### 3. Ejecución de la simulación
El sistema requiere dos terminales abiertas simultáneamente para simular el flujo real.

TERMINAL 1 (Backend IoT): Simula la llegada de datos de contadores, ejecuta la IA y escribe alertas.
```bash 
python simulacion_backend.py
```

TERMINAL 2 (Frontend Dashboard): Arranca la interfaz visual para el gestor.
```bash 
python app.py
```

### 4. Acceso al MVP
* Panel de Control: Abra http://127.0.0.1:8050/ en su navegador.
* Simulación movil: Abra http://127.0.0.1:8050/sim-movil/ID_CLIENTE (Poliza suministro)
* Credenciales: empresa@gesai.com / 1234

