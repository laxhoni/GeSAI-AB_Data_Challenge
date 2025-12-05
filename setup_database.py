import sqlite3
import os
import sys
import pandas as pd
from faker import Faker
import random
import time

# --- TRUCO: Importar módulos de la carpeta src desde la raíz ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
# Al importar, si no existen las claves, se generan y salen los mensajes.
# Si ya existen, no sale nada.
from crypto_manager import hashear_password, cifrar_pii
# -------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'gesai.db')
PATH_DATOS_REALES = os.path.join(BASE_DIR, 'data', 'processed-data', 'datos_simulacion_features.csv') 
NUM_CLIENTES_SIMULACION = 50

faker = Faker('es_ES')

def crear_conexion():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = 1")
        print(f"✅ Conexión establecida en: {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error al conectar: {e}")
        return None

def crear_tablas(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios_empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, contrasena TEXT, nombre TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (cliente_id TEXT PRIMARY KEY, nombre TEXT, telefono TEXT, email TEXT, direccion TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS incidencias (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT, fecha_deteccion DATETIME DEFAULT CURRENT_TIMESTAMP, estado TEXT, verificacion TEXT, descripcion TEXT, encuesta_resultado TEXT, FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notificaciones (notificacion_id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT, mensaje TEXT, link TEXT, leida INTEGER DEFAULT 0, FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tokens_verificacion (id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE, incidencia_id INTEGER, fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (incidencia_id) REFERENCES incidencias (id))''')
    conn.commit()
    print("✅ Tablas listas.")

def insertar_datos_iniciales(conn):
    cursor = conn.cursor()
    
    # 1. ADMIN
    try:
        password_seguro = hashear_password('1234') 
        cursor.execute(
            "INSERT INTO usuarios_empresa (email, contrasena, nombre) VALUES (?, ?, ?)",
            ('empresa@gesai.com', password_seguro, 'Admin GeSAI')
        )
        print("👤 Usuario admin creado.")
    except sqlite3.IntegrityError:
        pass

    # 2. CLIENTES (CON LÓGICA DE CARTA)
    print(f"🔄 Generando {NUM_CLIENTES_SIMULACION} clientes (Mix Digital/Postal)...")
    ids_reales = []
    
    # Intentar cargar IDs reales del CSV para que coincidan con la simulación
    if os.path.exists(PATH_DATOS_REALES):
        try:
            df = pd.read_csv(PATH_DATOS_REALES, usecols=['POLISSA_SUBM'])
            unique = df['POLISSA_SUBM'].unique().tolist()
            # Cogemos una muestra
            if len(unique) >= NUM_CLIENTES_SIMULACION:
                ids_reales = random.sample(unique, NUM_CLIENTES_SIMULACION)
            else:
                ids_reales = unique
        except: pass
    
    # Rellenar con sintéticos si faltan
    while len(ids_reales) < NUM_CLIENTES_SIMULACION:
        ids_reales.append(str(1000 + len(ids_reales)))

    count = 0
    clientes_carta = 0
    
    for i, c_id in enumerate(ids_reales):
        # LÓGICA: 1 de cada 3 (índices 0, 3, 6...) NO tiene contacto digital
        es_digital = (i % 3 != 0) 

        raw_nombre = faker.name()
        raw_addr = faker.address()
        
        # Si es digital, generamos telf/email. Si no, None.
        raw_telf = faker.phone_number() if es_digital else None
        raw_email = f"{raw_nombre.split()[0].lower()}@mail.com" if es_digital else None
        
        # Contadores para el log
        if not es_digital: clientes_carta += 1

        # Cifrado (cifrar_pii devuelve None si recibe None, así que es seguro)
        enc_nombre = cifrar_pii(raw_nombre)
        enc_addr = cifrar_pii(raw_addr)
        enc_telf = cifrar_pii(raw_telf)
        enc_email = cifrar_pii(raw_email)
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO clientes (cliente_id, nombre, telefono, email, direccion) VALUES (?, ?, ?, ?, ?)",
                (str(c_id), enc_nombre, enc_telf, enc_email, enc_addr)
            )
            count += 1
        except: pass
            
    conn.commit()
    print(f"✅ {count} clientes insertados.")
    print(f"   📊 {count - clientes_carta} Digitales (App)")
    print(f"   📮 {clientes_carta} Analógicos (Solo Carta Postal)")

if __name__ == '__main__':
    print("--- INICIANDO RESET DE BASE DE DATOS ---")
    
    # Intento de borrado robusto
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("🗑️ BBDD antigua eliminada correctamente.")
        except PermissionError:
            print("❌ ERROR FATAL: No se puede borrar 'gesai.db'.")
            print("⚠️ CIERRA la app, el simulador o cualquier visor SQL y vuelve a intentarlo.")
            sys.exit(1) # Paramos el script aquí
        except Exception as e:
            print(f"❌ Error borrando archivo: {e}")
            sys.exit(1)
    
    conn = crear_conexion()
    if conn:
        crear_tablas(conn)
        insertar_datos_iniciales(conn)
        conn.close()
        print("\n🚀 INSTALACIÓN COMPLETADA EXITOSAMENTE.")