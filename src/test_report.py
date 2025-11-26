# prueba_mail

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Aseguramos importación correcta
try:
    from reports_manager import generar_carta_postal_pdf
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from reports_manager import generar_carta_postal_pdf

# 1. Definimos datos de prueba (simulando lo que vendría de la BBDD)
id_incidencia_test = 99999
cliente_test = {
    'cliente_id': 999, # Añadido para que aparezca en el asunto de la carta
    'nombre': 'Juan Pérez García',
    'direccion': 'Av. Diagonal 211, 4º 2ª, 08018 Barcelona',
    # Simulamos que no tenemos contacto digital
    'telefono': None,
    'email': None
}

print("--- Iniciando prueba de generación de CARTA POSTAL ---")

# 2. Llamamos a la función directamente
try:
    ruta_generada = generar_carta_postal_pdf(id_incidencia_test, cliente_test)

    # 3. Verificamos el resultado
    if ruta_generada:
        print(f"\n✅ ¡ÉXITO! La Carta PDF se ha generado correctamente.")
        print(f"📂 Búscalo aquí: {ruta_generada}")
        print("   (Verifica que el logo y el enlace de contacto aparecen bien)")
    else:
        print("\n❌ ERROR: No se pudo generar el PDF. Revisa los logs de error arriba.")

except Exception as e:
    print(f"\n❌ EXCEPCIÓN: {e}")
    
    
# prueba_informe

# Aseguramos que pueda importar reports_manager si se ejecuta desde src/
try:
    from reports_manager import generar_informe_tecnico_pdf
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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

# Actualizado para incluir las probabilidades separadas
datos_incidencia = {
    'fecha': datetime.now().strftime("%d/%m/%Y"),
    'estado': 'Fuga Grave',
    'descripcion': 'Anomalía detectada por IA. Consumo nocturno elevado constante.',
    'prob_hoy': 0.98,      # Necesario para el nuevo informe
    'prob_manana': 0.99,   # Necesario para el nuevo informe
    'prob_7dias': 0.99     # Necesario para el nuevo informe
}

# B) Datos Históricos (DataFrame falso para la gráfica)
# Generamos 30 días de datos con un pico al final
fechas = [datetime.now() - timedelta(days=x) for x in range(30)]
fechas.reverse() # Ordenar cronológicamente

# Consumo normal (10-50L) con un pico de fuga al final (200L)
consumos = [np.random.uniform(10, 50) for _ in range(25)] + \
           [np.random.uniform(150, 250) for _ in range(5)]

df_historico = pd.DataFrame({
    'FECHA_HORA': fechas,  # <--- CORREGIDO: Coincide con reports_manager.py
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
        print("   (Ábrelo para ver la gráfica de consumo y el nuevo formato)")
    else:
        print("\n❌ Error: La función devolvió None.")

except Exception as e:
    print(f"\n❌ EXCEPCIÓN CRÍTICA: {e}")
    import traceback
    traceback.print_exc()