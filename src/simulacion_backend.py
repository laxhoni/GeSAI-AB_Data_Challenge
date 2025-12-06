# src/simulacion_backend.py

import sys
import os
import time
import random
import pandas as pd
from datetime import datetime

# Parche de ruta para importar módulos hermanos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from motor_gesai import ejecutar_deteccion_simulada, _conectar_bbdd

# Configuración
TIEMPO_ENTRE_LECTURAS = 3  # Segundos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_DATOS_SIMULACION = os.path.join(BASE_DIR, 'data', 'processed-data', 'datos_simulacion_features.csv')

def cargar_datos_simulacion():
    """Carga el CSV con los datos futuros para alimentar a la IA."""
    if not os.path.exists(PATH_DATOS_SIMULACION):
        print(f"[*] No se encuentra el fichero de simulación: {PATH_DATOS_SIMULACION}")
        return None
    try:
        # Leemos el CSV. Importante: asegurar tipos
        df = pd.read_csv(PATH_DATOS_SIMULACION)
        # Convertir a tipos numéricos lo que se pueda para evitar errores en el modelo
        return df
    except Exception as e:
        print(f" Error leyendo CSV simulación: {e}")
        return None

def main():
    print("===========================================================")
    print("                 GeSAI BACKEND: SIMULADOR IOT + IA ACTIVA")
    print(f"   (Intervalo: {TIEMPO_ENTRE_LECTURAS}s | Fuente: datos_simulacion_features.csv)")
    print("===========================================================\n")
    
    # 1. Cargar Datos Reales
    df_simulacion = cargar_datos_simulacion()
    if df_simulacion is None or df_simulacion.empty:
        print("[*] No hay datos para simular. Ejecuta primero el notebook de entrenamiento.")
        return

    # Convertimos a lista de diccionarios para acceso rápido
    # (Simulamos que llega un dato de un contador aleatorio cada vez)
    registros = df_simulacion.to_dict('records')
    print(f"[*] Conectado a red IoT. {len(registros)} lecturas disponibles para streaming.\n")

    try:
        while True:
            # 2. Elegir una lectura al azar del "futuro"
            lectura_actual = random.choice(registros)
            cliente_id = str(lectura_actual['POLISSA_SUBM']) # Asegurar string
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 3. ENVIAR AL CEREBRO (Ahora pasamos los datos, no solo el ID)
            # Esto activará el modelo LightGBM dentro del motor
            res = ejecutar_deteccion_simulada(cliente_id, datos_externos=lectura_actual)
            
            status = res.get('status', 'UNKNOWN')
            msg = res.get('message', '')
            
            # 4. Visualización en consola
            if status == 'ALERTA':
                icono = "🔴" if "Grave" in msg else "🟠"
                print(f"[{timestamp}] ID: {cliente_id} | {icono} {msg}")
            
            elif status == 'OK':
                print(f"[{timestamp}] ID: {cliente_id} | 🟢 {msg}")
            
            else:
                print(f"[{timestamp}] ID: {cliente_id} | ⚠️ {msg}")
            
            time.sleep(TIEMPO_ENTRE_LECTURAS)
            
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido.")

if __name__ == "__main__":
    main()