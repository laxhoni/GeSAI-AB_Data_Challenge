# GeSAI: Gestió Segura i Automatitzada d'Incidències
> **Aigües de Barcelona Data Challenge** | Team GeSAI | UPF

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




# Challenge Final Report (GeSAI) 
## Índice
## 1. Resumen Ejecutivo (Executive Summary)
* **1.1. Visión General:** Qué es GeSAI y qué problema resuelve (Detección proactiva + Inclusión social).
* **1.2. Cifras Clave:** Resumen de impacto (84% Precisión, 68% Reducción de Falsas Alarmas, 100% Cobertura de Clientes).
* **1.3. Valor Diferencial:** La combinación de IA avanzada con un canal de comunicación híbrido (Digital/Analógico).

## 2. Contexto y Definición del Problema (Background)
* **2.1. El Reto del AB Data Challenge:** Descripción del ámbito "Detección de consumos anómalos" y "Experiencia de cliente".
* **2.2. Problemática Detectada:**
    * Ineficiencia operativa por falsas alarmas.
    * Riesgo de exclusión para colectivos vulnerables (Brecha Digital).
* **2.3. Validación de Mercado (Estudio Inicial):**
    * Resultados de la encuesta ciudadana (N=100+).
    * Evidencia de la necesidad del canal postal (Datos sobre gestión de suministros para mayores).
    * Nivel de aceptación de la IA en la gestión del agua.

## 3. Solución Propuesta y Objetivos
* **3.1. Descripción del Producto (MVP):** Sistema integral de monitorización, detección y notificación multicanal.
* **3.2. Objetivos del Proyecto:**
    * **Negocio:** Optimización de recursos y reducción de costes operativos.
    * **Social:** Garantizar que la alerta llegue a todos, independientemente de su tecnología.
    * **Técnico:** Procesamiento escalable de Big Data en tiempo real.

## 4. Metodología Técnica: De los Datos al Modelo
* **4.1. Ingeniería de Datos (Data Engineering):**
    * Fuentes de Datos: Dataset Oficial (75M registros) + Open Data (AEMET, Catastro).
    * Estrategia Big Data: Procesamiento distribuido con Dask para superar limitaciones de memoria.
    * **Creación de Nuevos Datos (Feature Engineering):** Desarrollo de variables sintéticas (Lags, Rolling Windows, Ratios de Desviación) para capturar la temporalidad.
* **4.2. Modelado Predictivo (The AI Core):**
    * **Selección del Modelo:** Justificación del cambio de LSTM a LightGBM (Eficiencia vs. Coste computacional).
    * Estrategia de Entrenamiento: Clasificación Multi-Horizonte (Modelos a 1h, 24h y 7 días).
    * Optimización: Búsqueda de umbral óptimo (Threshold Tuning) para maximizar el F1-Score.
* **4.3. Meta-Análisis de Decisiones:**
    * Lógica de Negocio: Implementación de reglas basadas en "Deltas" (Tendencias de probabilidad) para clasificar la gravedad.
* **4.4. Resultados y Validación:**
    * Métricas finales: AUC-PR (0.86), Precisión (84%).
    * Explicabilidad (XAI): Análisis SHAP para entender los factores de riesgo.

## 5. Arquitectura del Sistema y Visualización (MVP)
* **5.1. Arquitectura de Microservicios:**
    * Diseño desacoplado: Backend Worker (Simulación IoT) vs. Frontend Dashboard (Visualización).
    * Persistencia: Base de datos centralizada (SQLite).
* **5.2. Flujo de Funcionamiento (End-to-End):**
    * Explicación del ciclo de vida del dato: Sensor -> Inferencia IA -> BBDD -> Alerta.
* **5.3. Interfaces de Usuario:**
    * **Dashboard de Empresa:** Panel de control en tiempo real para gestores.
    * **Simulador Móvil:** Experiencia del cliente digital (Notificación Push + Encuesta).
    * **Generador de Reportes:** Automatización de Informes Técnicos y Cartas Postales (PDF).

## 6. Innovación e Impacto (Justificación)
* **6.1. Impacto Social (Brecha Digital):** Detalle de la solución de Cartas Postales Automatizadas para clientes "incontactables".
* **6.2. Eficiencia Operativa:** Estimación de ahorro de costes por filtrado de falsas alarmas.
* **6.3. Cambio de Paradigma:** Transición de un modelo reactivo a uno predictivo basado en tendencias de crecimiento.

## 7. Gestión del Proyecto (Project Management)
* **7.1. Metodología:** Aplicación híbrida PM²/Agile (Iteraciones).
* **7.2. Retos y Soluciones:** Cómo se superó el bloqueo de memoria RAM (MemoryError) mediante reingeniería de datos.
* **7.3. Asunciones y Restricciones:** Limitaciones de hardware y disponibilidad de datos históricos.

## 8. Conclusiones y Próximos Pasos
* **8.1. Conclusiones:** Validación de la viabilidad técnica y comercial del MVP.
* **8.2. Roadmap Futuro (Next Steps):**
    * Implementación de Ciberseguridad (Hashing y Firma Digital en reportes).
    * Despliegue en Cloud (AWS/Azure).
    * Integración con sistemas de facturación reales.

## 9. Anexos
* **9.1. Stack Tecnológico:** Lista de librerías y herramientas.
* **9.2. Enlace al Repositorio:** Código fuente.
* **9.3. Guía Rápida de Uso:** Instrucciones para ejecutar la simulación.


## 1. Resumen Ejecutivo (Executive Summary)
* **1.1. Visión General:** Qué es GeSAI y qué problema resuelve (Detección proactiva + Inclusión social).
* **1.2. Cifras Clave:** Resumen de impacto (84% Precisión, 68% Reducción de Falsas Alarmas, 100% Cobertura de Clientes).
* **1.3. Valor Diferencial:** La combinación de IA avanzada con un canal de comunicación híbrido (Digital/Analógico).

## 2. Contexto y Definición del Problema (Background)
* **2.1. El Reto del AB Data Challenge:**
Challenge 3: **Fugas de agua y experiencia del cliente**
La gestión eficiente de las fugas de agua representa un desafío fundamental que impacta directamente en la experiencia de los clientes.
Cada incidente presenta características particulares que se reflejan en los patrones de consumo y generan diferentes respuestas por parte de los usuarios.

Este desafío busca profundizar en la comprensión de las tipologías de fugas y su relación con la experiencia del cliente, desde su detección hasta la resolución. El objetivo es evolucionar hacia una gestión más eficiente y proactiva de estas incidencias, mejorando tanto la conservación de los recursos hídricos como la satisfacción de los usuarios.

* **2.2. Problemática Detectada:**
En la actualidad, la empresa Aigües de Barcelona y otras empresas encargadas de la gestión del agua comparten unos antecedentes similares: 
- Detección y/o gestión ineficiente de las fugas de agua u otras anomalías relacionadas con el consumo.
- Comunicación poco satisfactoria debida a una baja fluidez o eficacia a través de alertas no optimizadas en términos de tiempo y cercanía con el cliente.
- Dependencia del CRM de usuarios: A la hora de comunicarse con el cliente cuando se detecta una fuga, el usuario debe estar registrado en el Área de usuarios de Aigües de Barcelona.

Estos antecedentes repercuten directamente en la sostenibilidad debido a la pérdida de recursos hídricos así como en la experiencia de los clientes con la empresa, en términos de confianza y satisfacción y ponen en manifiesto los retos y necesidades a los que se enfrentan este tipo de empresas. Por una parte, destacamos la necesidad de mejora en la detección y gestión de forma eficiente de las fugas de agua así como cualquier consumo anómalo en el consumo. Por otra parte, lograr una comunicación transparente, fluida, eficaz y cercana con los clientes.
 
* **2.3. Validación de Mercado (Estudio Inicial):**
Antes de desarrollar la solución que se explicará en los siguientes puntos, el equipo GeSAI ha desarrollado un estudio de mercado a través de un sistema de encuestas de Google. A través de esta metodología hemos podido analizar y comprender cual es el punto de partida de nuestro proyecto, detectar las preocupaciones de los usuarios y la opinión de los mismos sobre la solución GeSAI.
Se puede acceder a la encuesta a través del siguiente enlace: https://forms.gle/hEXmXkqDExmNg1TSA

INSIGHTSSSS???

## 3. Solución Propuesta y Objetivos
* **3.1. Descripción del Producto (MVP):**
Para dar solución a las necesidades descritas anteriormente, os presentamos nuestra propuesta de proyecto: GesAI, una innovadora plataforma de gestión automatizada de incidencias a través de agentes inteligentes, especializada en fugas que abarca desde la detección y evaluación de dichas incidencias a través de técnicas basadas en Data Science y Machine Learning; la comunicación efectiva y proactiva con el cliente a través de un sistema de alertas y doble verificación con el objetivo de minimizar los riesgos en términos de sostenibilidad y economía del cliente; la elaboración automatizada de informes y visualizaciones de los resultados obtenidos para cada una de las incidencias. Todo ello enmarcado en un entorno seguro de los datos a través técnicas de ciberseguridad y criptografía basadas en AES en modo Galois/Counter Mode y Firma digital con RSA y padding PSS.

* **3.2. Objetivos del Proyecto:**
    * **Negocio:** Optimización de recursos y reducción de costes operativos.
    * **Social:** Garantizar que la alerta llegue a todos, independientemente de su tecnología.
    * **Técnico:** Procesamiento escalable de Big Data en tiempo real.
