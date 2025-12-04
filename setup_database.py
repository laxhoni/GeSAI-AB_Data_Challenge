import sqlite3
import os
import pandas as pd
from faker import Faker
import random

# --- CONFIGURACIÓN DE RUTA ABSOLUTA (CRÍTICO) ---
# Calculamos la ruta absoluta al directorio donde está ESTE archivo (setup_database.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'gesai.db')

# Ruta al CSV (Asumiendo que data/ está en la raíz)
PATH_DATOS_REALES = os.path.join(BASE_DIR, 'data', 'processed-data', 'datos_simulacion_features.csv') 
NUM_CLIENTES_SIMULACION = 50

faker = Faker('es_ES')

def crear_conexion():
    try:
        # Usamos DB_PATH (absoluta) en lugar de 'gesai.db'
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = 1")
        print(f"✅ Conexión establecida en: {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error al conectar: {e}")
        return None

def crear_tablas(conn):
    cursor = conn.cursor()
    
    # 1. Usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios_empresa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        contrasena TEXT NOT NULL, 
        nombre TEXT
    )''')

    # 2. Clientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        cliente_id TEXT PRIMARY KEY,
        nombre TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT
    )''')

    # 3. Incidencias
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS incidencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id TEXT NOT NULL,
        fecha_deteccion DATETIME DEFAULT CURRENT_TIMESTAMP,
        estado TEXT,
        verificacion TEXT DEFAULT 'PENDIENTE',
        descripcion TEXT,
        encuesta_resultado TEXT, 
        FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id)
    )''')

    # 4. Notificaciones
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notificaciones (
        notificacion_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id TEXT NOT NULL,
        mensaje TEXT,
        link TEXT,
        leida INTEGER DEFAULT 0,
        FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id)
    )''')

    # 5. Tokens
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens_verificacion (
        token TEXT PRIMARY KEY,
        incidencia_id INTEGER NOT NULL,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (incidencia_id) REFERENCES incidencias (id)
    )''')
    
    conn.commit()
    print("✅ Tablas creadas/verificadas correctamente.")

def insertar_datos_iniciales(conn):
    cursor = conn.cursor()
    
    # 1. Insertar Usuario Admin
    try:
        cursor.execute(
            "INSERT INTO usuarios_empresa (email, contrasena, nombre) VALUES (?, ?, ?)",
            ('empresa@gesai.com', '1234', 'Admin GeSAI')
        )
        print("👤 Usuario admin creado.")
    except sqlite3.IntegrityError:
        pass # Ya existe

    # 2. Insertar Clientes REALES
    print(f"🔄 Buscando datos reales en: {PATH_DATOS_REALES}")
    ids_reales = []
    
    if os.path.exists(PATH_DATOS_REALES):
        try:
            # Leemos solo la columna necesaria
            df = pd.read_csv(PATH_DATOS_REALES, usecols=['POLISSA_SUBM'])
            ids_unicos = df['POLISSA_SUBM'].unique().tolist()
            
            # Cogemos una muestra si hay muchos
            if len(ids_unicos) > NUM_CLIENTES_SIMULACION:
                ids_reales = random.sample(ids_unicos, NUM_CLIENTES_SIMULACION)
            else:
                ids_reales = ids_unicos
                
            print(f"📍 IDs reales cargados: {len(ids_reales)}")
        except Exception as e:
            print(f"⚠️ Error leyendo CSV: {e}. Usando IDs sintéticos.")
    else:
        print(f"⚠️ Archivo CSV no encontrado en {PATH_DATOS_REALES}")

    # Si falló la carga, usamos sintéticos
    if not ids_reales:
        ids_reales = [str(1000 + i) for i in range(NUM_CLIENTES_SIMULACION)]

    count = 0
    for c_id in ids_reales:
        nombre = faker.name()
        # Simulamos que 1 de cada 3 no tiene datos digitales (para probar cartas)
        es_digital = (count % 3 != 0) 
        
        email = f"{nombre.split()[0].lower()}@mail.com" if es_digital else None
        telefono = faker.phone_number() if es_digital else None
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO clientes (cliente_id, nombre, telefono, email, direccion) VALUES (?, ?, ?, ?, ?)",
                (str(c_id), nombre, telefono, email, faker.address())
            )
            count += 1
        except: pass
            
    print(f"✅ {count} clientes insertados en BBDD.")
    conn.commit()

def main():
    print("--- INICIANDO SETUP DE BASE DE DATOS ---")
    
    # Limpieza previa (Opcional: Descomenta si quieres borrar la BBDD antigua siempre)
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"🗑️ Base de datos antigua eliminada: {DB_PATH}")
        except PermissionError:
            print("⚠️ No se pudo borrar la base de datos (archivo en uso). Cierra la app e intenta de nuevo.")
            return

    conn = crear_conexion()
    if conn:
        crear_tablas(conn)
        insertar_datos_iniciales(conn)
        conn.close()
        print("\n🚀 INSTALACIÓN COMPLETADA EXITOSAMENTE.")
        print(f"📂 Base de datos ubicada en: {DB_PATH}")

if __name__ == '__main__':
    main()