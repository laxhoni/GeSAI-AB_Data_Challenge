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

# --- 1. CONFIGURACIÓN ---
DB_NAME = 'gesai.db'
MODELOS_DIR = '../data/processed-data/'

# Umbrales de Negocio
UMBRAL_SEGURIDAD = 0.30
UMBRAL_ALERTA = 0.70
UMBRAL_CRITICO = 0.85
TENDENCIA_RAPIDA = 0.05
TENDENCIA_ESTRUCTURAL = 0.15

# Eliminamos Criptografía
faker = Faker('es_ES')

modelos_ia = {}
features_modelo = []

# --- 2. INICIALIZACIÓN ---
def inicializar_motor():
    global modelos_ia, features_modelo
    print("--- INICIALIZANDO MOTOR GeSAI ---")
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

def _conectar_bbdd():
    path = DB_NAME if os.path.exists(DB_NAME) else f"../{DB_NAME}"
    try:
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = 1")
        conn.row_factory = sqlite3.Row 
        return conn
    except: return None

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

def _obtener_historico_simulado(cliente_id):
    """Genera histórico visual para el PDF."""
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=24*30, freq='h')
    consumos = np.random.normal(loc=20, scale=5, size=len(fechas))
    return pd.DataFrame({'FECHA_HORA': fechas, 'CONSUMO_REAL': consumos})

# --- 4. FUNCIÓN DE DETECCIÓN (Acepta datos ordenados) ---
def ejecutar_deteccion_simulada(cliente_id: str, datos_externos: pd.Series = None) -> dict:
    """
    Procesa una lectura. 
    Si 'datos_externos' está presente (viene del backend ordenado), usa esos datos reales.
    Si no, usa aleatorios (fallback).
    """
    X_input = None
    origen_datos = "Simulado"
    
    # 1. Preparar Datos Reales del Backend
    if datos_externos is not None and modelos_ia:
        try:
            # Convertir la Serie (fila) a DataFrame
            fila = pd.DataFrame([datos_externos])
            
            # Filtrar solo las columnas que el modelo necesita (quitamos fechas y IDs)
            cols_validas = [c for c in features_modelo if c in fila.columns]
            X_input = fila[cols_validas].copy()
            
            # Limpieza de tipos obligatoria
            CAT = ['US_AIGUA_SUBM', 'TIPO_DIA']
            for c in X_input.columns:
                if c in CAT: X_input[c] = X_input[c].astype('category')
                else: X_input[c] = pd.to_numeric(X_input[c], errors='coerce').fillna(0.0)
            
            origen_datos = "Lectura Real IoT"
        except Exception as e:
            print(f"Error procesando datos externos: {e}")
            X_input = None
    
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

    # 4. BBDD
    conn = _conectar_bbdd()
    if not conn: return {'status': 'ERROR'}
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes WHERE cliente_id = ?", (str(cliente_id),))
        res = cur.fetchone()
        
        if not res:
            # Crear cliente dummy si llega un ID nuevo
            nom = faker.name()
            email = f"{nom.split()[0]}@test.com"
            cur.execute("INSERT INTO clientes VALUES (?, ?, ?, ?, ?)", (str(cliente_id), nom, "600", email, "Barcelona"))
            datos_cli = {'nombre': nom, 'email': email, 'direccion': "Barcelona"}
        else:
            datos_cli = dict(res)
            # Asegurar nulos
            if datos_cli['email'] == 'None' or datos_cli['email'] == '': datos_cli['email'] = None

        desc = f"{estado}. Prob: {p_hoy:.0%}. {detalle}"
        cur.execute("INSERT INTO incidencias (cliente_id, estado, verificacion, descripcion) VALUES (?, ?, ?, ?)",
                    (str(cliente_id), estado, 'PENDIENTE', desc))
        new_id = cur.lastrowid

        # Acciones
        tiene_email = (datos_cli['email'] is not None)
        msg_extra = ""
        if "Leve" not in estado:
            if not tiene_email:
                cur.execute("UPDATE incidencias SET verificacion = 'CARTA PENDIENTE' WHERE id = ?", (new_id,))
                msg_extra = "Carta Pendiente"
            else:
                token = f"tk_{new_id}_{int(time.time())}"
                link = f"http://127.0.0.1:8050/verificar/{token}"
                msg = f"Hola {datos_cli['nombre']}, alerta GeSAI: {estado}."
                cur.execute("INSERT INTO tokens_verificacion (token, incidencia_id) VALUES (?, ?)", (token, new_id))
                cur.execute("INSERT INTO notificaciones (cliente_id, mensaje, link) VALUES (?, ?, ?)", (str(cliente_id), msg, link))
                msg_extra = "Push Enviado"

        # Generar informe técnico siempre
        # historico = _obtener_historico_simulado(cliente_id)
        # datos_inc_pdf = {'estado': estado, 'descripcion': desc, 'prob_hoy': p_hoy}
        # generar_informe_tecnico_pdf(new_id, datos_cli, datos_inc_pdf, historico)

        #####

        conn.commit()
        return {'status': 'ALERTA', 'message': f"{estado} - {msg_extra}"}
    finally:
        conn.close()

# --- FUNCIONES LECTURA APP (Sin Cripto) ---
def verificar_credenciales(u, p):
    conn = _conectar_bbdd()
    try:
        cur = conn.cursor()
        # Login simple: Texto plano
        cur.execute("SELECT * FROM usuarios_empresa WHERE email = ?", (u,))
        row = cur.fetchone()
        if row and row['contrasena'] == p: 
            return {'success': True, 'rol': 'Empresa', 'nombre': row['nombre']}
    finally: conn.close()
    return {'success': False, 'message': 'Credenciales incorrectas'}

def get_lista_incidencias_activas(filtro="todas"):
    conn = _conectar_bbdd()
    try:
        sql = "SELECT i.*, c.nombre as cliente_nombre FROM incidencias i JOIN clientes c ON i.cliente_id = c.cliente_id"
        if filtro != "todas": sql += f" WHERE i.estado LIKE '%{filtro}%'"
        sql += " ORDER BY i.id DESC LIMIT 50"
        cur = conn.cursor()
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]
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
        # Intenta parsear probabilidad del texto
        import re
        match = re.search(r"Prob: (\d+)", inc['descripcion'])
        prob = float(match.group(1))/100 if match else 0.9
        datos_inc['prob_hoy'] = prob
        
        return {'success': True, 'datos_incidencia': datos_inc, 'datos_cliente': dict(cli) if cli else {}}
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
    conn = _conectar_bbdd()
    try:
        cur = conn.cursor()
        cur.execute("SELECT incidencia_id FROM tokens_verificacion WHERE token=?", (token,))
        row = cur.fetchone()
        if not row: return {'success': False, 'message': 'Token inválido'}
        cur.execute("UPDATE incidencias SET verificacion='VERIFICADO (Encuesta)' WHERE id=?", (row['incidencia_id'],))
        cur.execute("DELETE FROM tokens_verificacion WHERE token=?", (token,))
        conn.commit()
        return {'success': True, 'message': 'OK'}
    finally: conn.close()