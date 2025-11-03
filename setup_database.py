import sqlite3
import os

# --- Configuració ---
DB_NAME = 'gesai.db'

def crear_conexion():
    """Crea una connexió a la base de dades SQLite."""
    try:
        conn = sqlite3.connect(DB_NAME)
        print(f"Conexión a {DB_NAME} exitosa.")
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar con {DB_NAME}: {e}")
        return None

def crear_tablas(conn):
    """Crea les taules a la base de dades si no existeixen."""
    cursor = conn.cursor()
    
    # 1. Taula d'Usuaris (Canviada)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios_empresa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        contrasena TEXT NOT NULL,  -- Canviat de password_hash a contrasena
        nombre TEXT
    )''')
    print("Tabla 'usuarios_empresa' creada o ya existente.")

    # 2. Taula de Clients
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        cliente_id INTEGER PRIMARY KEY,
        nombre TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT
    )''')
    print("Tabla 'clientes' creada o ya existente.")

    # 3. Taula d'Incidències
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS incidencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        fecha_deteccion DATETIME DEFAULT CURRENT_TIMESTAMP,
        estado TEXT,
        verificacion TEXT,
        descripcion TEXT,
        FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id)
    )''')
    print("Tabla 'incidencias' creada o ya existente.")

    # 4. Taula de Notificacions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notificaciones (
        notificacion_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        mensaje TEXT,
        link TEXT,
        leida INTEGER DEFAULT 0,
        FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id)
    )''')
    print("Tabla 'notificaciones' creada o ya existente.")

    # 5. Taula de Tokens
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens_verificacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL UNIQUE,
        incidencia_id INTEGER NOT NULL,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (incidencia_id) REFERENCES incidencias (id)
    )''')
    print("Tabla 'tokens_verificacion' creada o ya existente.")

    # 6. Taula d'Enquestes (Respostes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS encuestas_respuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incidencia_id INTEGER NOT NULL,
        q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT, q6 TEXT,
        FOREIGN KEY (incidencia_id) REFERENCES incidencias (id)
    )''')
    print("Tabla 'encuestas_respuestas' creada o ya existente.")
    
    conn.commit()
    print("Todas las tablas han sido aseguradas.")

def insertar_datos_iniciales(conn):
    """Insereix dades fixes, com l'usuari de l'empresa."""
    cursor = conn.cursor()
    
    # Insertar usuari d'empresa amb contrasenya en text pla
    try:
        cursor.execute(
            "INSERT INTO usuarios_empresa (email, contrasena, nombre) VALUES (?, ?, ?)",
            ('empresa@gesai.com', '1234', 'Jhonatan Barcos') # '1234' en text pla
        )
        print("Usuario 'empresa@gesai.com' insertado con contraseña en texto plano.")
    except sqlite3.IntegrityError:
        print("El usuario 'empresa@gesai.com' ya existe.")
        
    # Aquí aniria la lògica per inserir clients amb Faker
    
    conn.commit()

# --- Funció Principal ---
def main():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Base de datos antigua '{DB_NAME}' eliminada.")
        
    conn = crear_conexion()
    
    if conn:
        crear_tablas(conn)
        insertar_datos_iniciales(conn)
        conn.close()
        print(f"Base de datos '{DB_NAME}' creada y poblada con datos iniciales.")
    else:
        print("Error: No se pudo crear la conexión a la base de datos.")

if __name__ == '__main__':
    main()