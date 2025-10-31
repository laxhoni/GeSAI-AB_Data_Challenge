# src/motor_gesai.py

"""
Este es el "Cerebro" del proyecto (Motor GeSAI).
Contiene toda la lógica de negocio, acceso a BBDD y modelos de IA.
NO debe contener NADA de Dash (html, dcc, callbacks).
"""

# --- MOCKS DE BASE DE DATOS (El Equipo Core AI debe implementar esto) ---

# Mock de la tabla de usuarios
MOCK_USUARIOS_DB = {
    "empresa@gesai.com": {"contrasena": "1234", "rol": "Empresa", "nombre": "Jhonatan Barcos"}
    # No hay más usuarios "Cliente"
}

# Mock de la tabla de incidencias
MOCK_INCIDENCIAS_DB = [
    {'id': 101, 'cliente_id': 50, 'cliente_nombre': 'Oscar Sanz', 'fecha': '31/10/2025', 'estado': 'Grave', 'verificacion': 'PENDIENTE', 'descripcion': 'Anomalía detectada en patrón de consumo'},
    {'id': 102, 'cliente_id': 51, 'cliente_nombre': 'María García', 'fecha': '31/10/2025', 'estado': 'Moderada', 'verificacion': 'PENDIENTE', 'descripcion': 'Variación inusual en horario nocturno'},
]

# Mock de la tabla de notificaciones (para el simulador de móvil)
MOCK_NOTIFICACIONES_DB = []

# Mock de la tabla de tokens de verificación
MOCK_TOKENS_DB = {} # Ej: {"aB12cDe3fG4h": 105}


# --- CONTRATO 1: USUARIOS ---

def verificar_credenciales(usuario: str, contrasena: str) -> dict:
    """Verifica un usuario (solo empresa) y contraseña."""
    print(f"MOCK: verificando credenciales para usuario={usuario}")
    if usuario in MOCK_USUARIOS_DB and MOCK_USUARIOS_DB[usuario]["contrasena"] == contrasena:
        user_data = MOCK_USUARIOS_DB[usuario]
        return {'success': True, 'rol': user_data['rol'], 'nombre': user_data['nombre']}
    else:
        return {'success': False, 'message': 'Usuario o contraseña incorrectos'}

# --- CONTRATO 2: LÓGICA DE EMPRESA ---

def get_lista_incidencias_activas(tipo_filtro: str = "todas") -> list[dict]:
    """Obtiene una lista de todas las incidencias de la BBDD."""
    print(f"MOCK BBDD: get_lista_incidencias_activas(filtro={tipo_filtro})")
    
    if tipo_filtro == "todas":
        return MOCK_INCIDENCIAS_DB
    else:
        return [inc for inc in MOCK_INCIDENCIAS_DB if inc['estado'] == tipo_filtro]

def get_detalles_incidencia(incidencia_id: int) -> dict:
    """Obtiene toda la información detallada de una única incidencia."""
    print(f"MOCK BBDD: get_detalles_incidencia(id={incidencia_id})")
    
    # Simulación de búsqueda en BBDD
    for inc in MOCK_INCIDENCIAS_DB:
        if inc['id'] == incidencia_id:
            # (En la app real, aquí harías un JOIN con la tabla de clientes)
            mock_cliente_data = {
                101: {'nombre': 'Oscar Sanz', 'telefono': '600123456', 'email': 'cliente@gesai.com', 'direccion': 'Calle Ficticia 123, Barcelona'},
                102: {'nombre': 'María García', 'telefono': '600987654', 'email': 'maria@email.com', 'direccion': 'Avenida Ejemplo 45, L\'Hospitalet'},
                105: {'nombre': 'Cliente Nuevo', 'telefono': '600111222', 'email': 'nuevo@email.com', 'direccion': 'Plaza Simulada 1'}
            }
            return {
                'success': True,
                'datos_incidencia': inc,
                'datos_cliente': mock_cliente_data.get(inc['id'], {'nombre': 'Desconocido'})
            }
            
    return {'success': False, 'message': f'Incidencia con ID {incidencia_id} no encontrada.'}

def ejecutar_deteccion_lstm(cliente_id: int, cliente_nombre: str) -> dict:
    """
    Ejecuta el modelo de detección de LSTM para un cliente específico.
    Si detecta algo, crea una nueva incidencia Y UNA NOTIFICACIÓN PUSH.
    """
    print(f"MOCK IA: ejecutando detección para cliente_id={cliente_id}")
    
    # --- SIMULACIÓN DE DETECCIÓN ---
    # 1. Crear nueva incidencia en la BBDD
    nueva_incidencia_id = len(MOCK_INCIDENCIAS_DB) + 100
    nueva_incidencia = {
        'id': nueva_incidencia_id,
        'cliente_id': cliente_id,
        'cliente_nombre': cliente_nombre,
        'fecha': '31/10/2025',
        'estado': 'Grave',
        'verificacion': 'PENDIENTE',
        'descripcion': 'Detección simulada por IA'
    }
    MOCK_INCIDENCIAS_DB.append(nueva_incidencia)
    print(f"MOCK BBDD: Nueva incidencia creada: {nueva_incidencia}")

    # 2. Crear un token de verificación único
    token = f"token_para_incidencia_{nueva_incidencia_id}"
    MOCK_TOKENS_DB[token] = nueva_incidencia_id
    
    # 3. Crear el link y el mensaje
    link_verificacion = f"http://127.0.0.1:8050/verificar/{token}"
    mensaje_sms = f"Hola {cliente_nombre}, somos GeSAI. Hemos detectado una anomalía (ID: {nueva_incidencia_id}). Por favor, pulsa aquí para verificar: {link_verificacion}"

    # 4. ESCRIBIR EN LA BBDD DE NOTIFICACIONES (para el móvil)
    nueva_notificacion = {
        'notificacion_id': len(MOCK_NOTIFICACIONES_DB) + 1,
        'cliente_id': cliente_id,
        'mensaje': mensaje_sms,
        'link': link_verificacion,
        'leida': False
    }
    MOCK_NOTIFICACIONES_DB.append(nueva_notificacion)
    print(f"MOCK BBDD: Nueva notificación PUSH guardada: {nueva_notificacion}")
    
    return {'status': 'ALERTA', 'message': f'¡Detección! Incidencia #{nueva_incidencia_id} creada y notificación enviada.'}


# --- CONTRATO 3: LÓGICA PÚBLICA (Móvil y Verificación) ---

def get_notificaciones_pendientes_cliente(cliente_id: int) -> list[dict]:
    """
    Es llamada CADA 3 SEGUNDOS por el simulador de móvil.
    Busca en la BBDD si hay notificaciones no leídas para ese cliente.
    """
    print(f"MOCK BBDD: El móvil del cliente {cliente_id} está pidiendo notificaciones...")
    
    notificaciones_no_leidas = []
    for notif in MOCK_NOTIFICACIONES_DB:
        if notif['cliente_id'] == cliente_id and notif['leida'] == False:
            notificaciones_no_leidas.append(notif)
            
    return notificaciones_no_leidas

def marcar_notificacion_leida(notificacion_id: int):
    """
Recibe el ID de la notificación (no de la incidencia) y la marca como leída."""
    print(f"MOCK BBDD: Marcando notificación {notificacion_id} como leída.")
    for notif in MOCK_NOTIFICACIONES_DB:
        if notif['notificacion_id'] == notificacion_id:
            notif['leida'] = True
            break
    return True

def validar_token_y_registrar(token: str, respuestas_encuesta: dict) -> dict:
    """
    Valida un token de la URL y registra la encuesta completa del cliente.
    """
    print(f"MOCK BBDD: Validando token {token} con respuestas {respuestas_encuesta}")
    
    # 1. Validar el token
    if token not in MOCK_TOKENS_DB:
        return {'success': False, 'message': 'Token no válido o expirado.'}
        
    incidencia_id = MOCK_TOKENS_DB[token]
    
    # 2. Actualizar la BBDD de Incidencias
    encontrada = False
    for inc in MOCK_INCIDENCIAS_DB:
        if inc['id'] == incidencia_id:
            # En la BBDD real, guardarías las 6 respuestas.
            # Aquí, solo actualizamos el estado de verificación.
            inc['verificacion'] = f"VERIFICADO (Encuesta Recibida)"
            encontrada = True
            break
            
    if not encontrada:
        return {'success': False, 'message': 'Incidencia asociada no encontrada.'}
        
    # 3. Borrar el token
    del MOCK_TOKENS_DB[token]
    
    # Puedes ver las respuestas del servidor
    print(f"RESPUESTAS RECIBIDAS: {respuestas_encuesta}")
    
    return {'success': True, 'message': f'¡Gracias! Su encuesta ha sido registrada para la incidencia #{incidencia_id}'}