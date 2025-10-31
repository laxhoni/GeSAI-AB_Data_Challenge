
### USERS
# Verificar Credenciales de Usuario
def verificar_credenciales(usuario: str, contrasena: str) -> dict:
    """
    Verifica un usuario y contraseña contra la BBDD.
    
    Args:
        usuario (str): El nombre de usuario (o email).
        contrasena (str): La contraseña en texto plano.
    
    Returns:
        dict: Un diccionario con el resultado.
              Ejemplo: {'success': True, 'rol': 'Empresa', 'nombre': 'Jhonatan Barcos'}
              o {'success': False, 'message': 'Credenciales incorrectas'}
    """
    # --- MOCK (implementación falsa) ---
    print(f"MOCK: verificando credenciales para usuario={usuario}")
    
    # Base de datos falsa de usuarios
    USUARIOS_BBDD = {
        "empresa@gesai.com": {"contrasena": "1234", "rol": "Empresa", "nombre": "Jhonatan (Empresa)"},
        "cliente@gesai.com": {"contrasena": "abcd", "rol": "Cliente", "nombre": "Oscar (Cliente)", "incidencia_id_activa": 101}
    }
    
    if usuario in USUARIOS_BBDD and USUARIOS_BBDD[usuario]["contrasena"] == contrasena:
        # ¡Éxito! Devolvemos los datos del usuario.
        user_data = USUARIOS_BBDD[usuario]
        return {
            'success': True,
            'rol': user_data['rol'],
            'nombre': user_data['nombre'],
            'datos_extra': {'incidencia_id': user_data.get('incidencia_id_activa')} if user_data.get('rol') == 'Cliente' else {}
        }
    else:
        # Fracaso
        return {'success': False, 'message': 'Usuario o contraseña incorrectos'}





### EMPRESA: Motor Gesai
def get_lista_incidencias_activas(tipo_filtro: str = "todas") -> list[dict]:
    """
    Obtiene una lista de todas las incidencias que requieren atención.
    (MOCK ACTUAL - Reemplazar con consulta a BBDD real)
    """
    print(f"MOCK: get_lista_incidencias_activas(filtro={tipo_filtro})")
    
    # --- *** INICIO DE LA CORRECCIÓN *** ---
    # Faltaba el campo 'cliente_nombre' en tus datos
    todas_las_incidencias = [
        {'id': 101, 'cliente_id': 50, 'cliente_nombre': 'Oscar Sanz', 'fecha': '31/10/2025', 'estado': 'Grave', 'descripcion': 'Anomalía detectada en patrón de consumo'},
        {'id': 102, 'cliente_id': 51, 'cliente_nombre': 'María García', 'fecha': '31/10/2025', 'estado': 'Moderada', 'descripcion': 'Variación inusual en horario nocturno'},
        {'id': 103, 'cliente_id': 52, 'cliente_nombre': 'Carlos Ruiz', 'fecha': '30/10/2025', 'estado': 'Grave', 'descripcion': 'Pico de consumo anómalo detectado'},
        {'id': 104, 'cliente_id': 53, 'cliente_nombre': 'Ana López', 'fecha': '30/10/2025', 'estado': 'Leve', 'descripcion': 'Desviación menor en consumo habitual'}
    ]
    # --- *** FIN DE LA CORRECCIÓN *** ---
    
    if tipo_filtro == "todas":
        return todas_las_incidencias
    else:
        return [inc for inc in todas_las_incidencias if inc['estado'] == tipo_filtro]

# Get Detalles de una Incidencia
def get_detalles_incidencia(incidencia_id: int) -> dict:
    """
    Obtiene toda la información detallada de una única incidencia.
    
    Args:
        incidencia_id (int): El ID de la incidencia a buscar.
    
    Returns:
        dict: Un diccionario con toda la info.
              Ejemplo: {'success': True,
                        'datos_incidencia': {'id': 101, 'estado': 'Grave', ...},
                        'datos_cliente': {'nombre': 'Oscar Sanz', 'telefono': '600123456'},
                        'ruta_informe_pdf': 'generated_reports/incidencia_101.pdf'}
              o {'success': False, 'message': 'Incidencia no encontrada'}
    """
    # --- MOCK (implementación falsa) ---
    print(f"MOCK: get_detalles_incidencia(id={incidencia_id})")
    if incidencia_id == 101:
        # Simula que genera el PDF
        ruta_falsa_pdf = "generated_reports/incidencia_101_MOCK.pdf"
        
        return {
            'success': True,
            'datos_incidencia': {'id': 101, 'fecha': '31/10/2025', 'estado': 'Grave', 'verificacion': 'PENDIENTE'},
            'datos_cliente': {'nombre': 'Oscar Sanz', 'telefono': '600123456'},
            'ruta_informe_pdf': ruta_falsa_pdf
        }
    else:
        return {'success': False, 'message': 'Incidencia no encontrada'}
    
    
    ### CLIENTE
    # Registrar Verificación del Cliente
def registrar_verificacion_cliente(incidencia_id: int, respuesta: str) -> dict:
    """
    Registra la respuesta de verificación del cliente en la BBDD.
    
    Args:
        incidencia_id (int): El ID de la incidencia que se está verificando.
        respuesta (str): "SI" o "NO", según la selección del cliente.
    
    Returns:
        dict: Un diccionario indicando el resultado.
              Ejemplo: {'success': True, 'message': 'Respuesta registrada correctamente'}
    """
    # --- MOCK (implementación falsa) ---
    print(f"MOCK: registrar_verificacion_cliente(id={incidencia_id}, respuesta='{respuesta}')")
    
    # 1. Simula la escritura en BBDD
    # 2. Simula la actualización del informe (llamando a get_detalles_incidencia)
    
    return {'success': True, 'message': f'Respuesta "{respuesta}" registrada (MOCK)'}


### MODELO
# --- CONTRATO 4 ---
def ejecutar_deteccion_lstm(cliente_id: int) -> dict:
    """
    Ejecuta el modelo de detección de LSTM para un cliente específico.
    Si detecta algo, crea una nueva incidencia en la BBDD.
    
    Args:
        cliente_id (int): El ID del cliente a analizar.
    
    Returns:
        dict: Un diccionario con el resultado.
              Ejemplo: {'status': 'ALERTA', 'incidencia_id': 103, 'message': '...'}
              o {'status': 'OK', 'message': 'No se detectaron anomalías'}
    """
    # --- MOCK (implementación falsa) ---
    print(f"MOCK: ejecutar_deteccion_lstm(cliente_id={cliente_id})")
    
    # Simula una detección
    if cliente_id % 2 == 0: # Simula que detecta en clientes pares
        return {'status': 'ALERTA', 'incidencia_id': 103, 'message': 'Anomalía Grave detectada (MOCK)'}
    else:
        return {'status': 'OK', 'message': 'No se detectaron anomalías (MOCK)'}
