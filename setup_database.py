import sqlite3
import os
import sys
import pandas as pd
from faker import Faker
import random
import time
import getpass # Para ocultar la contraseña al escribirla

# --- IMPORTACIONES ---
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
# Importamos la nueva función de validación
from crypto_manager import hashear_password, cifrar_pii, validar_fortaleza_password
# ---------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'gesai.db')
PATH_DATOS_REALES = os.path.join(BASE_DIR, 'data', 'processed-data', 'datos_simulacion_features.csv') 
NUM_CLIENTES_SIMULACION = 100

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

def solicitar_password_admin():
    """Bucle infinito hasta que el usuario ponga una password segura."""
    print("\n🔐 CONFIGURACIÓN DE SEGURIDAD")
    print("Por política de seguridad, debe establecer una contraseña ROBUSTA para el Admin.")
    print("Requisitos: 12+ caracteres, Mayús, Minús, Número y Símbolo.")
    
    while True:
        # getpass oculta lo que escribes (como en Linux/Login real)
        try:
            p1 = getpass.getpass(">>> Introduzca nueva contraseña Admin: ")
        except:
            # Fallback por si getpass falla en algunas consolas de IDE
            p1 = input(">>> Introduzca nueva contraseña Admin: ")
            
        es_valida, mensaje = validar_fortaleza_password(p1)
        
        if not es_valida:
            print(f"❌ DÉBIL: {mensaje}")
            continue
            
        try:
            p2 = getpass.getpass(">>> Repita la contraseña: ")
        except:
            p2 = input(">>> Repita la contraseña: ")
            
        if p1 != p2:
            print("❌ Las contraseñas no coinciden. Inténtelo de nuevo.")
            continue
            
        print("✅ Contraseña aceptada y hasheada.")
        return p1

def insertar_datos_iniciales(conn):
    cursor = conn.cursor()
    
    # 1. ADMIN (INTERACTIVO)
    try:
        # Pedimos la password segura al usuario
        pass_texto_plano = solicitar_password_admin()
        
        password_seguro = hashear_password(pass_texto_plano) 
        cursor.execute(
            "INSERT INTO usuarios_empresa (email, contrasena, nombre) VALUES (?, ?, ?)",
            ('empresa@gesai.com', password_seguro, 'Admin GeSAI')
        )
        print("👤 Usuario 'empresa@gesai.com' creado correctamente.")
    except sqlite3.IntegrityError:
        pass

    # 2. CLIENTES
    print(f"\n🔄 Generando {NUM_CLIENTES_SIMULACION} clientes (Mix Digital/Postal)...")
    ids_reales = []
    
    if os.path.exists(PATH_DATOS_REALES):
        try:
            df = pd.read_csv(PATH_DATOS_REALES, usecols=['POLISSA_SUBM'])
            unique = df['POLISSA_SUBM'].unique().tolist()
            if len(unique) >= NUM_CLIENTES_SIMULACION:
                ids_reales = random.sample(unique, NUM_CLIENTES_SIMULACION)
            else:
                ids_reales = unique
        except: pass
    
    while len(ids_reales) < NUM_CLIENTES_SIMULACION:
        ids_reales.append(str(1000 + len(ids_reales)))

    count = 0
    clientes_carta = 0
    
    for i, c_id in enumerate(ids_reales):
        es_digital = (i % 4 != 0) 
        raw_nombre = faker.name()
        raw_addr = faker.address()
        raw_telf = faker.phone_number() if es_digital else None
        raw_email = f"{raw_nombre.split()[0].lower()}@mail.com" if es_digital else None
        
        if not es_digital: clientes_carta += 1

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
    print(f"   📊 {count - clientes_carta} Digitales")
    print(f"   📮 {clientes_carta} Analógicos")

if __name__ == '__main__':
    print("--- INICIANDO RESET DE BASE DE DATOS ---")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("🗑️ BBDD antigua eliminada correctamente.")
        except PermissionError:
            print("❌ ERROR: Cierra la app/simulador antes de regenerar la BBDD.")
            sys.exit(1)
    
    conn = crear_conexion()
    if conn:
        crear_tablas(conn)
        insertar_datos_iniciales(conn)
        conn.close()
        print("\n🚀 INSTALACIÓN COMPLETADA EXITOSAMENTE.")