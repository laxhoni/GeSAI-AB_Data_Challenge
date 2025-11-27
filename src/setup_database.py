import sqlite3
import os
import pandas as pd
from faker import Faker

# --- Configuración ---
DB_NAME = 'gesai.db'
# Ruta relativa desde la raíz del proyecto
PATH_DATOS_REALES = '../data/processed-data/datos_simulacion_features.csv' 
NUM_CLIENTES_SIMULACION = 50

faker = Faker('es_ES')

def crear_conexion():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA foreign_keys = 1")
        print(f"✅ Conexión a {DB_NAME} exitosa.")
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error al conectar: {e}")
        return None

def crear_tablas(conn):
    cursor = conn.cursor()
    
    # 1. Usuarios (CAMBIO: Contraseña en texto plano para evitar error de bcrypt)
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
        verificacion TEXT,
        descripcion TEXT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL UNIQUE,
        incidencia_id INTEGER NOT NULL,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (incidencia_id) REFERENCES incidencias (id)
    )''')

    # 6. Encuestas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS encuestas_respuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incidencia_id INTEGER NOT NULL,
        q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT, q6 TEXT,
        FOREIGN KEY (incidencia_id) REFERENCES incidencias (id)
    )''')
    
    conn.commit()
    print("✅ Tablas creadas correctamente (Modo Texto Plano).")

def insertar_datos_iniciales(conn):
    cursor = conn.cursor()
    
    # 1. Insertar Usuario Admin (SIN HASH)
    try:
        cursor.execute(
            "INSERT INTO usuarios_empresa (email, contrasena, nombre) VALUES (?, ?, ?)",
            ('empresa@gesai.com', '1234', 'Jhonatan Barcos')
        )
        print("👤 Usuario admin creado (Pass: 1234).")
    except sqlite3.IntegrityError:
        print("ℹ️ El usuario admin ya existe.")

    # 2. Insertar Clientes REALES
    print(f"🔄 Buscando datos reales en '{PATH_DATOS_REALES}'...")
    ids_reales = []
    
    if os.path.exists(PATH_DATOS_REALES):
        try:
            df = pd.read_csv(PATH_DATOS_REALES, usecols=['POLISSA_SUBM'])
            ids_reales = df['POLISSA_SUBM'].unique().tolist()
            # Muestreo si hay muchos
            if len(ids_reales) > NUM_CLIENTES_SIMULACION:
                import random
                ids_reales = random.sample(ids_reales, NUM_CLIENTES_SIMULACION)
            print(f"📍 IDs reales cargados: {len(ids_reales)}")
        except Exception as e:
            print(f"⚠️ Error leyendo CSV: {e}. Usando IDs sintéticos.")
    else:
        print(f"⚠️ Archivo no encontrado. Usando IDs sintéticos.")

    if not ids_reales:
        ids_reales = [str(50 + i) for i in range(NUM_CLIENTES_SIMULACION)]

    count = 0
    for c_id in ids_reales:
        nombre = faker.name()
        # 30% sin contacto digital
        sin_contacto = (count % 3 == 0)
        email = None if sin_contacto else f"{nombre.split()[0].lower()}@mail.com"
        telefono = None if sin_contacto else faker.phone_number()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO clientes (cliente_id, nombre, telefono, email, direccion) VALUES (?, ?, ?, ?, ?)",
                (str(c_id), nombre, telefono, email, faker.address())
            )
            count += 1
        except: pass
            
    print(f"✅ {count} clientes listos en BBDD.")
    conn.commit()

def main():
    # Borrar DB para aplicar el cambio de columna password_hash -> contrasena
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print(f"🗑️ BBDD antigua eliminada.")
        except:
            print("⚠️ Cierra la app para poder borrar la BBDD.")
            return

    conn = crear_conexion()
    if conn:
        crear_tablas(conn)
        insertar_datos_iniciales(conn)
        conn.close()
        print(f"\n🚀 INSTALACIÓN COMPLETADA (Sin Criptografía).")

if __name__ == '__main__':
    main()