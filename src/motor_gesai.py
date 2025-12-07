# src/motor_gesai.py

import sqlite3
import os
import time
import random
import pandas as pd
import numpy as np
import joblib
from faker import Faker
from reports_manager import generar_carta_postal_pdf, generar_informe_tecnico_pdf
import json

#GESTOR DE CRIPTO
from crypto_manager import (
    verificar_password, 
    cifrar_pii, 
    descifrar_pii, 
    generar_token_seguro
)

#CONFIG
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR) #Raíz del proyecto
DB_PATH = os.path.join(BASE_DIR, 'gesai.db')
MODELOS_DIR = os.path.join(BASE_DIR, 'data', 'processed-data')

#Umbrales
UMBRAL_SEGURIDAD = 0.30
UMBRAL_ALERTA = 0.70
UMBRAL_CRITICO = 0.85
TENDENCIA_RAPIDA = 0.05
TENDENCIA_ESTRUCTURAL = 0.15


import warnings
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("ignore", category=InconsistentVersionWarning) #Silenciar warnings versiones sklearn

faker = Faker('es_ES')
modelos_ia = {}
features_modelo = []

def _conectar_bbdd():
    try:
        #Usamos la ruta DB_PATH
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = 1")
        conn.row_factory = sqlite3.Row 
        return conn
    except Exception as e:
        print(f"❌ Error conectando a BBDD: {e}")
        return None

#INICIALIZACIÓN
def inicializar_motor():
    global modelos_ia, features_modelo
    print("--- INICIALIZANDO MOTOR GeSAI (MODO SEGURO + ANTI-DUPLICADOS) ---")
    try:
        modelos_ia['HOY'] = joblib.load(os.path.join(MODELOS_DIR, 'lgbm_model_TARGET_HOY.joblib'))
        modelos_ia['MANANA'] = joblib.load(os.path.join(MODELOS_DIR, 'lgbm_model_TARGET_MANANA.joblib'))
        modelos_ia['7DIAS'] = joblib.load(os.path.join(MODELOS_DIR, 'lgbm_model_TARGET_7DIAS.joblib'))
        features_modelo = modelos_ia['HOY'].booster_.feature_name()
        print("✅ Modelos LightGBM cargados.")
    except Exception as e:
        print(f"⚠️ ERROR modelos: {e}. Fallback activo.")
        modelos_ia = None

inicializar_motor()

def _aplicar_reglas(p_hoy, p_manana, p_7dias):
    delta_corto = p_manana - p_hoy
    delta_largo = p_7dias - p_hoy
    
    if p_hoy < UMBRAL_SEGURIDAD: return "No Fuga", ""
    if p_hoy < UMBRAL_ALERTA:
        if delta_largo > TENDENCIA_ESTRUCTURAL: return "Fuga Leve (Tendencia)", f"Tendencia +{delta_largo:.1%}"
        return "No Fuga", "Riesgo bajo"
    if p_hoy < UMBRAL_CRITICO:
        if delta_corto > TENDENCIA_RAPIDA or delta_largo > TENDENCIA_ESTRUCTURAL: return "Fuga Grave (En Crecimiento)", "Crecimiento rápido"
        return "Fuga Moderada", "Estable"
    return "Fuga Grave", "Crítica"


#OBTENCIÓN DE HISTÓRICO REAL
def get_consumo_historico(cliente_id, es_fuga=False):
    """
    Recupera historial REAL.
    Usa random.seed para que la inyección de la fuga sea SIEMPRE IGUAL
    para el mismo cliente.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path_datos = os.path.join(base_dir, 'data', 'processed-data', 'datos_simulacion_features.csv')
    
    #SEMILLA CON EL ID DEL CLIENTE
    random.seed(str(cliente_id))
    
    try:
        if os.path.exists(path_datos):
            df = pd.read_csv(path_datos, usecols=['POLISSA_SUBM', 'FECHA_HORA_CRONO', 'CONSUMO_REAL'], dtype={'POLISSA_SUBM': str})
            
            #Filtrado poliza
            df_real = df[df['POLISSA_SUBM'] == str(cliente_id)].copy()
            
            if df_real.empty:
                #Sin datos
                return pd.DataFrame() 

            
            df_real['FECHA_HORA'] = pd.to_datetime(df_real['FECHA_HORA_CRONO'], errors='coerce')
            df_real = df_real.sort_values('FECHA_HORA')
            
            
            df_final = df_real.tail(720)[['FECHA_HORA', 'CONSUMO_REAL']].copy()
            
            if not df_final.empty:
                
                ultimo = df_final['FECHA_HORA'].max()
                df_final['FECHA_HORA'] += (pd.Timestamp.now() - ultimo)
                
                
                if es_fuga:
                    puntos = len(df_final)
                    duracion = min(random.randint(48, 120), puntos)
                    extra = np.linspace(10, 200, duracion)
                    df_final.iloc[-duracion:, 1] += extra

                return df_final

    except Exception as e:
        print(f"⚠️ Error CSV: {e}")

    return pd.DataFrame()

#DETECCIÓN SIMULADA
def ejecutar_deteccion_simulada(cliente_id: str, datos_externos: pd.Series = None) -> dict:
    X_input = None
    origen_datos = "Simulado"
    
    # 1. Preparar Datos
    if datos_externos is not None and modelos_ia:
        try:
            fila = pd.DataFrame([datos_externos])
            cols_validas = [c for c in features_modelo if c in fila.columns]
            X_input = fila[cols_validas].copy()
            CAT = ['US_AIGUA_SUBM', 'TIPO_DIA']
            for c in X_input.columns:
                if c in CAT: X_input[c] = X_input[c].astype('category')
                else: X_input[c] = pd.to_numeric(X_input[c], errors='coerce').fillna(0.0)
            origen_datos = "Lectura Real IoT"
        except: X_input = None
    
    # 2. Predicción
    if modelos_ia and X_input is not None:
        try:
            p_hoy = modelos_ia['HOY'].predict_proba(X_input, raw_score=False)[:, 1][0]
            p_man = modelos_ia['MANANA'].predict_proba(X_input, raw_score=False)[:, 1][0]
            p_7d = modelos_ia['7DIAS'].predict_proba(X_input, raw_score=False)[:, 1][0]
        except: p_hoy, p_man, p_7d = 0.1, 0.1, 0.1
    else:
        # Fallback aleatorio
        p_hoy = random.random()
        p_man, p_7d = p_hoy, p_hoy

    # 3. Clasificación
    estado, detalle = _aplicar_reglas(p_hoy, p_man, p_7d)
    
    if "No Fuga" in estado: 
        return {'status': 'OK', 'message': f'Lectura normal ({p_hoy:.1%})'}

    # 4. BBDD (Gestión Segura + Anti-Duplicados)
    conn = _conectar_bbdd()
    if not conn: return {'status': 'ERROR'}
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes WHERE cliente_id = ?", (str(cliente_id),))
        res = cur.fetchone()
        
        datos_cli = {}
        if not res:
            
            nom = faker.name()
            email = f"{nom.split()[0]}@test.com"
            
            ### SEGURIDAD: Ciframos antes de guardar ###
            cur.execute(
                "INSERT INTO clientes VALUES (?, ?, ?, ?, ?)", 
                (str(cliente_id), cifrar_pii(nom), cifrar_pii("600"), cifrar_pii(email), cifrar_pii("Barcelona"))
            )
            datos_cli = {'nombre': nom, 'email': email, 'direccion': "Barcelona"}
        else:
            #Cliente existente: Desciframos para uso interno
            datos_cli = dict(res)
            ### SEGURIDAD: Desciframos ###
            datos_cli['email'] = descifrar_pii(datos_cli['email'])
            datos_cli['nombre'] = descifrar_pii(datos_cli['nombre'])

        desc = f"{estado}. Prob: {p_hoy:.0%}. {detalle}"

        #Buscamos si ya existe una incidencia NO resuelta para este cliente
        cur.execute("SELECT id FROM incidencias WHERE cliente_id = ? AND verificacion != 'RESUELTA'", (str(cliente_id),))
        inc_existente = cur.fetchone()
        
        new_id = None
        msg_accion = ""
        
        if inc_existente:
            
            new_id = inc_existente['id']
            cur.execute("""
                UPDATE incidencias 
                SET estado = ?, descripcion = ?, fecha_deteccion = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (estado, desc, new_id))
            msg_accion = "(Actualizada)"
        else:
           
            cur.execute("INSERT INTO incidencias (cliente_id, estado, verificacion, descripcion) VALUES (?, ?, ?, ?)",
                        (str(cliente_id), estado, 'PENDIENTE', desc))
            new_id = cur.lastrowid
            msg_accion = "(Nueva)"

        
        #Solo enviamos si es nueva o si ha empeorado a Grave
        tiene_email = (datos_cli.get('email') is not None)
        msg_extra = ""
        
        if "Leve" not in estado:
            if not tiene_email:
                
                cur.execute("UPDATE incidencias SET verificacion = 'CARTA PENDIENTE' WHERE id = ?", (new_id,))
                msg_extra = "Carta Pendiente"
            else:
                token = generar_token_seguro() 
                link = f"http://127.0.0.1:8050/verificar/{token}"
                msg = f"Hola {datos_cli['nombre']}, alerta GeSAI: {estado}."
                
                cur.execute("DELETE FROM tokens_verificacion WHERE incidencia_id = ?", (new_id,))
                cur.execute("INSERT INTO tokens_verificacion (token, incidencia_id) VALUES (?, ?)", (token, new_id))
                cur.execute("INSERT INTO notificaciones (cliente_id, mensaje, link) VALUES (?, ?, ?)", (str(cliente_id), msg, link))
                msg_extra = "Push Enviado"

        conn.commit()
        return {'status': 'ALERTA', 'message': f"{estado} {msg_accion} - {msg_extra}"}
    finally:
        conn.close()

# --- FUNCIONES LECTURA APP (CON SEGURIDAD) ---

def verificar_credenciales(u, p):
    """Verifica hash en lugar de texto plano."""
    conn = _conectar_bbdd()
    try:
        cur = conn.cursor()
        # Usamos parámetros '?' para evitar inyección SQL
        cur.execute("SELECT * FROM usuarios_empresa WHERE email = ?", (u,))
        row = cur.fetchone()
        
        if row:
            # hash_guardado está en la columna 'contrasena'
            hash_guardado = row['contrasena']
            ### SEGURIDAD: Verificación Criptográfica ###
            if verificar_password(p, hash_guardado):
                return {'success': True, 'rol': 'Empresa', 'nombre': row['nombre']}
    finally: conn.close()
    return {'success': False, 'message': 'Credenciales incorrectas'}

def get_lista_incidencias_activas(filtro="todas"):
    conn = _conectar_bbdd()
    # PROTECCIÓN 1: Si no hay conexión
    if not conn: return []
    
    try:
        # FILTRAMOS SOLO LAS NO RESUELTAS (Importante para el dashboard)
        sql = """
            SELECT i.*, c.nombre as cliente_nombre 
            FROM incidencias i 
            JOIN clientes c ON i.cliente_id = c.cliente_id
            WHERE i.verificacion != 'RESUELTA'
        """
        params = []
        
        if filtro != "todas": 
            sql += " AND i.estado LIKE ?"
            params.append(f"%{filtro}%")
            
        sql += " ORDER BY i.fecha_deteccion DESC LIMIT 50"
        
        cur = conn.cursor()
        cur.execute(sql, params) # Pasamos params de forma segura
        rows = [dict(r) for r in cur.fetchall()]
        
        # ### SEGURIDAD: Descifrar nombres para la UI ###
        for r in rows:
            r['cliente_nombre'] = descifrar_pii(r['cliente_nombre'])
            
        return rows
        
    except Exception as e:
        print(f"⚠️ Error leyendo incidencias: {e}")
        return []
    finally: conn.close()

def get_detalles_incidencia(id):
    conn = _conectar_bbdd()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM incidencias WHERE id=?", (id,))
        inc = cur.fetchone()
        if not inc: return {'success': False}
        
        cur.execute("SELECT * FROM clientes WHERE cliente_id=?", (inc['cliente_id'],))
        cli = cur.fetchone()
        
        datos_inc = dict(inc)
        import re
        match = re.search(r"Prob: (\d+)", inc['descripcion'])
        prob = float(match.group(1))/100 if match else 0.9
        datos_inc['prob_hoy'] = prob
        
        # ### SEGURIDAD: Descifrar datos sensibles del cliente para el Modal/PDF ###
        datos_cli = {}
        if cli:
            datos_cli = dict(cli)
            datos_cli['nombre'] = descifrar_pii(datos_cli['nombre'])
            datos_cli['telefono'] = descifrar_pii(datos_cli['telefono'])
            datos_cli['email'] = descifrar_pii(datos_cli['email'])
            datos_cli['direccion'] = descifrar_pii(datos_cli['direccion'])
        
        return {'success': True, 'datos_incidencia': datos_inc, 'datos_cliente': datos_cli}
    finally: conn.close()

def get_notificaciones_pendientes_cliente(cid):
    conn = _conectar_bbdd()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM notificaciones WHERE cliente_id=? AND leida=0", (str(cid),))
        return [dict(r) for r in cur.fetchall()]
    finally: conn.close()

def marcar_notificacion_leida(nid):
    conn = _conectar_bbdd()
    try: conn.execute("UPDATE notificaciones SET leida=1 WHERE notificacion_id=?", (nid,)); conn.commit()
    finally: conn.close()

def validar_token_y_registrar(token, respuestas):
    """
    Valida token y guarda encuesta.
    """
    conn = _conectar_bbdd()
    if not conn: return {'success': False, 'message': 'Error de conexión'}

    try:
        cur = conn.cursor()
        # Verificar token
        cur.execute("SELECT incidencia_id FROM tokens_verificacion WHERE token=?", (token,))
        row = cur.fetchone()

        if not row: 
            return {'success': False, 'message': 'Token inválido o ya utilizado'}

        inc_id = row['incidencia_id']
        respuestas_json = json.dumps(respuestas, ensure_ascii=False)

        # Actualizar
        cur.execute("UPDATE incidencias SET verificacion='VERIFICADO (Encuesta)', encuesta_resultado = ? WHERE id=?", (respuestas_json, inc_id))
        
        # Borrar token usado (Seguridad)
        cur.execute("DELETE FROM tokens_verificacion WHERE token=?", (token,))

        conn.commit()
        return {'success': True, 'message': 'OK'}

    except Exception as e:
        print(f"Error en validar_token_y_registrar: {e}")
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()