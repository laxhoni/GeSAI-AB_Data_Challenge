# src/test_report.py (CORREGIDO)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from reports_manager import generar_informe_tecnico_pdf

print("--- INICIANDO PRUEBA DE INFORME TÉCNICO ---")

# 1. DATOS DE PRUEBA (SIMULACIÓN)

# A) Datos de la Incidencia y Cliente
id_incidencia = 105
datos_cliente = {
    'cliente_id': 50,
    'nombre': 'Oscar Sanz (Cliente Prueba)',
    'direccion': 'C/ Balmes 123, Barcelona',
    'telefono': '600 123 456',
    'email': 'oscar.sanz@example.com'
}

datos_incidencia = {
    'fecha': datetime.now().strftime("%d/%m/%Y"),
    'estado': 'Fuga Grave',
    'descripcion': 'Anomalía detectada por IA. Consumo nocturno elevado constante.',
    'prob_hoy': 0.98,    # Necesario para la gráfica de riesgo
    'prob_manana': 0.99,
    'prob_7dias': 0.99
}

# B) Datos Históricos (DataFrame falso para la gráfica)
fechas = [datetime.now() - timedelta(days=x) for x in range(30)]
fechas.reverse() 

consumos = [np.random.uniform(10, 50) for _ in range(25)] + \
           [np.random.uniform(150, 250) for _ in range(5)]

df_historico = pd.DataFrame({
    'FECHA_HORA': fechas,  
    'CONSUMO_REAL': consumos
})

print(f"Datos generados: {len(df_historico)} registros de consumo.")


# 2. EJECUTAR LA GENERACIÓN
print("\nGenerando PDF...")
try:
    ruta_pdf = generar_informe_tecnico_pdf(
        incidencia_id=id_incidencia,
        datos_cliente=datos_cliente,
        datos_incidencia=datos_incidencia,
        historico_df=df_historico
    )
    
    if ruta_pdf:
        print(f"\n✅ ¡ÉXITO! Informe generado correctamente.")
        print(f"📂 Archivo: {ruta_pdf}")
    else:
        print("\n❌ Error: La función devolvió None.")

except Exception as e:
    print(f"\n❌ EXCEPCIÓN CRÍTICA: {e}")
    import traceback
    traceback.print_exc()