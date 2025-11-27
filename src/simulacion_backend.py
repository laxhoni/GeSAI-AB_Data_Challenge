# src/simulador_backend.py

import sys
import os
import time
import random
from datetime import datetime

# Parche de ruta para importar módulos hermanos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from motor_gesai import ejecutar_deteccion_simulada, _conectar_bbdd

# Configuración
TIEMPO_ENTRE_LECTURAS = 3  # Ajusta la velocidad según prefieras

def main():
    print("===========================================================")
    print("   🚀 GeSAI BACKEND: MONITORIZACIÓN EN TIEMPO REAL")
    print(f"   (Intervalo de lectura: {TIEMPO_ENTRE_LECTURAS}s)")
    print("===========================================================\n")
    
    conn = _conectar_bbdd()
    if not conn: return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT cliente_id FROM clientes")
        ids = [row['cliente_id'] for row in cursor.fetchall()]
    finally:
        conn.close()
    
    if not ids: 
        print("❌ Sin clientes. Ejecuta setup_database.py"); return
    
    print(f"📡 Monitorizando {len(ids)} contadores inteligentes activos.\n")

    try:
        while True:
            cliente = random.choice(ids)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Ejecutamos la lógica del cerebro
            res = ejecutar_deteccion_simulada(cliente)
            
            status = res.get('status', 'UNKNOWN')
            msg = res.get('message', '')
            
            # Imprimimos SIEMPRE, sea Alerta u OK
            if status == 'ALERTA':
                # Diferenciar visualmente si es Leve o Grave por el texto del mensaje
                icono = "🔴" if "Grave" in msg else "🟠" # Naranja si no es Grave
                print(f"[{timestamp}] ID: {cliente} | {icono} {msg}")
            
            elif status == 'OK':
                # Imprimimos en verde lo que antes ocultábamos
                print(f"[{timestamp}] ID: {cliente} | 🟢 {msg}")
            
            else:
                print(f"[{timestamp}] ID: {cliente} | ⚠️ {msg}")
            
            time.sleep(TIEMPO_ENTRE_LECTURAS)
            
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido.")

if __name__ == "__main__":
    main()