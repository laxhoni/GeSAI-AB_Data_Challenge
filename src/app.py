# src/app.py

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
import time

# --- 1. IMPORTAR EL "CEREBRO" ---
from motor_gesai import (
    verificar_credenciales,
    get_lista_incidencias_activas,
    get_detalles_incidencia,
    ejecutar_deteccion_lstm,
    get_notificaciones_pendientes_cliente,
    marcar_notificacion_leida,
    validar_token_y_registrar
)

# --- 2. INICIALIZACIÓN DE LA APP ---
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
]
app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets, 
                suppress_callback_exceptions=True,
                assets_folder='assets') # <-- Assegura't que apunta a la teva carpeta 'assets'
app.title = "GesAI"


# --- 3. DEFINICIÓN DE LAYOUTS (Vistas) ---

def build_login_layout():
    """Construye el layout de la página de Inicio de Sesión (Solo Empresa)."""
    return html.Div([
        html.Div([
            html.Div(className='logo-container', children=[
                html.Img(src=app.get_asset_url('logo_1.png'), className='logo-login'),
                html.P('Portal de Gestión de Incidencias', className='app-subtitle'),
            ]),
            html.Div([
                html.Label('Usuario / Email', className='form-label'),
                dcc.Input(id='input-usuario', type='text', placeholder='empresa@gesai.com', className='form-input'),
            ]),
            html.Div([
                html.Label('Contraseña', className='form-label'),
                dcc.Input(id='input-password', type='password', placeholder='••••••••', className='form-input'),
            ]),
            html.Div(id='login-error', className='login-error-message'),
            html.Button('Iniciar Sesión', id='btn-login', n_clicks=0, className='btn-primary-custom btn-full-width'),
            html.Div([
                html.Hr(className='login-divider'),
                html.P('Cuenta de prueba: empresa@gesai.com / 1234', className='login-test-info'),
            ]),
        ], className='login-card'),
    ], className='login-container')


def build_empresa_layout(session_data):
    """Construye el layout del Dashboard de Empresa."""
    nombre_usuario = session_data.get('nombre', 'Usuario')
    return html.Div([
        dcc.Interval(id='intervalo-actualizacion-empresa', interval=5*1000, n_intervals=0),
        
        html.Div(className='header-dashboard', children=[
            html.Div(className='layout-flex-center', children=[
                html.Img(src=app.get_asset_url('logo_2.png'), className='logo-dashboard'),
                html.Div([
                    html.H3('Panel de Gestión de Incidencias', className='dashboard-title'),
                ]),
            ]),
            
            html.Div(className='layout-flex-center', children=[
                html.Div(className='user-info-badge', children=[
                    html.Span('🏢 ', className='user-info-icon'),
                    html.Span(nombre_usuario, className='user-info-name'),
                ]),
                html.Button('Cerrar Sesión', id={'type': 'btn-logout', 'index': 'empresa'}, n_clicks=0, className='btn-logout'),
            ]),
        ]),
        
        html.Div(className='main-content-container', children=[
            html.Div(id='stats-container', className='stats-container-spacing'),
            
            html.Div(className='search-box', children=[
                html.H5("Panel de Simulación de Detección"),
                html.P("Simula una detección de IA para un cliente y envía una notificación a su móvil simulado."),
                dbc.Row([
                    dbc.Col(dcc.Input(id='sim-cliente-id', type='number', placeholder='ID Cliente (ej. 50)', className='form-input-full')),
                    dbc.Col(dcc.Input(id='sim-cliente-nombre', type='text', placeholder='Nombre Cliente (ej. Oscar Sanz)', className='form-input-full')),
                    dbc.Col(html.Button('Ejecutar Detección', id='btn-ejecutar-sim', className='btn-primary-custom')),
                ]),
                html.Div(id='sim-resultado', className='sim-result-spacing')
            ]),
            
            html.Div(className='search-box', children=[
                html.Div(className='search-bar-container', children=[
                    dcc.Input(id='input-busqueda-id', type='number', placeholder='Buscar por ID de incidencia...', className='search-input-flex'),
                    html.Button('🔍 Buscar', id='btn-buscar', n_clicks=0, className='btn-primary-custom'),
                ]),
                html.Div(className='layout-flex-center', children=[
                    html.Span('Filtrar por estado:', className='filter-label'),
                    html.Button('Todas', id={'type': 'filtro-btn', 'index': 'todas'}, n_clicks=0, className='filter-btn filter-btn-active'),
                    html.Button('Grave', id={'type': 'filtro-btn', 'index': 'Grave'}, n_clicks=0, className='filter-btn'),
                    html.Button('Moderada', id={'type': 'filtro-btn', 'index': 'Moderada'}, n_clicks=0, className='filter-btn'),
                    html.Button('Leve', id={'type': 'filtro-btn', 'index': 'Leve'}, n_clicks=0, className='filter-btn'),
                ]),
            ]),
            
            dcc.Store(id='store-filtro-activo', data='todas'),
            html.Div(id='modal-detalles'),
            html.Div(id='incidencias-container'),
        ]),
    ])
    
def _build_survey_layout(token):
    """Función helper que construye la encuesta (para móvil o página pública)."""
    preguntas = [
        "1. ¿Ha notado un sonido de agua corriendo (siseo) cerca del contador?",
        "2. ¿Algún grifo o cisterna ha estado perdiendo agua?",
        "3. ¿El contador de agua sigue moviéndose aunque todos los grifos están cerrados?",
        "4. ¿Ha detectado manchas de humedad inesperadas en paredes o suelo?",
        "5. ¿Ha habido obras recientes en su domicilio o comunidad?",
        "6. ¿Considera que su consumo este mes ha sido normal?"
    ]
    
    opciones = [
        {'label': 'Sí', 'value': 'SI'},
        {'label': 'No', 'value': 'NO'},
        {'label': 'Puede Ser / No lo sé', 'value': 'NO_SE'},
    ]
    
    return html.Div([
        html.H5("Encuesta de Verificación", className='survey-title'),
        html.P(f"Por favor, responda a estas preguntas sobre su incidencia.", className='survey-subtitle'),
        dcc.Store(id='store-token', data=token),
        
        *[html.Div([
            html.Label(preg, className='survey-question-label'),
            dcc.RadioItems(
                id={'type': 'survey-q', 'index': i+1},
                options=opciones,
                value=None,
                className='survey-radio-group'
            )
        ]) for i, preg in enumerate(preguntas)],
        
        html.Button('Enviar Encuesta', id='btn-submit-survey', n_clicks=0, className='btn-primary-custom btn-full-width btn-margin-top'),
        html.Div(id='survey-result', className='survey-result-container')
    ])


def build_simulador_movil_layout(cliente_id, pathname):
    """
    Construye el layout que SIMULA un teléfono móvil realista.
    """
    contenido_pantalla = None
    
    if 'verificar' in pathname:
        token = pathname.split('/')[-1]
        contenido_pantalla = _build_survey_layout(token)
    else:
        contenido_pantalla = html.Div(id='div-notificaciones-movil', children=[
            html.P("Esperando notificaciones...", className='mobile-waiting-text')
        ])
        
    return html.Div(className='mobile-frame', children=[
        dcc.Store(id='store-cliente-id', data=cliente_id),
        dcc.Interval(id='intervalo-notificaciones-movil', interval=3*1000, n_intervals=0),
        
        html.Div(className='mobile-screen', children=[
            html.Div(className='mobile-island'),
            html.Div(className='mobile-header', children=[
                html.H5("Encuesta" if 'verificar' in pathname else "Notificaciones", 
                        className='mobile-header-title')
            ]),
            
            html.Div(className='mobile-notifications-area', children=[
                contenido_pantalla
            ]),
            
            html.Div(className='mobile-home-bar')
        ])
    ])

def build_verificacion_layout(token):
    """Construye la página de encuesta de verificación (pública)."""
    return html.Div(className='verification-page-container', children=[
        html.Div(className='verification-card', children=[
            _build_survey_layout(token) # Reutilizamos el layout de la encuesta
        ])
    ])


# --- 4. LAYOUT PRINCIPAL (Router) ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session', data={'logged_in': False}),
    html.Div(id='page-content')
])


# --- 5. CALLBACKS ---

# Callback 1: Router principal
@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def display_page(pathname, session_data):
    
    parts = pathname.strip('/').split('/')
    
    if parts[0] == 'sim-movil' and len(parts) >= 2:
        try:
            cliente_id = int(parts[1])
            return build_simulador_movil_layout(cliente_id, pathname)
        except:
            return html.H2("ID de cliente no válido.", className='error-message-centered')
            
    if parts[0] == 'verificar' and len(parts) == 2:
        token = parts[1]
        return build_verificacion_layout(token)

    if session_data and session_data.get('logged_in'):
        if pathname == '/' or pathname == '/dashboard':
            if session_data['rol'] == 'Empresa':
                return build_empresa_layout(session_data)
        if pathname == '/login':
            return dcc.Location(pathname='/', id='redirect-to-home')
    
    return build_login_layout()

# Callback 2: Lógica de Inicio de Sesión
@callback(
    [Output('session-store', 'data'),
     Output('login-error', 'children'),
     Output('url', 'pathname')],
    Input('btn-login', 'n_clicks'),
    [State('input-usuario', 'value'),
     State('input-password', 'value')],
    prevent_initial_call=True
)
def login(n_clicks, usuario, password):
    if not usuario or not password:
        return no_update, html.Div('Por favor, complete todos los campos.'), no_update
    
    resultado = verificar_credenciales(usuario, password)
    
    if resultado['success']:
        session_data = {'logged_in': True, 'rol': resultado['rol'], 'nombre': resultado['nombre']}
        return session_data, None, '/'
    else:
        return no_update, html.Div(resultado['message']), no_update

# Callback 3: Lógica de Cerrar Sesión (Logout)
@callback(
    [Output('session-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input({'type': 'btn-logout', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def logout(n_clicks_lista):
    if any(n > 0 for n in n_clicks_lista if n is not None):
        return {'logged_in': False}, '/'
    return no_update, no_update


# --- Callbacks del Dashboard EMPRESA ---

# Callback 4: Estadísticas Empresa
@callback(
    Output('stats-container', 'children'),
    Input('intervalo-actualizacion-empresa', 'n_intervals')
)
def update_stats(n_intervals):
    incidencias = get_lista_incidencias_activas("todas")
    total = len(incidencias)
    graves = len([i for i in incidencias if i['estado'] == 'Grave'])
    moderadas = len([i for i in incidencias if i['estado'] == 'Moderada'])
    leves = len([i for i in incidencias if i['estado'] == 'Leve'])
    
    #
    # --- AQUEST ÉS EL BLOC CORREGIT ---
    #
    # L'error era que 'md=3' estava FORA dels parèntesis de 'dbc.Col'
    #
    return dbc.Row([
        dbc.Col(html.Div([html.Div([html.P('Total Activas', className='stat-label'), html.P(str(total), className='stat-number total')], className='stat-info-flex'), html.Div('📊', className='stat-icon')], className='stat-card-content'), className='stat-card', md=3),
        dbc.Col(html.Div([html.Div([html.P('Graves', className='stat-label'), html.P(str(graves), className='stat-number grave')], className='stat-info-flex'), html.Div('🚨', className='stat-icon')], className='stat-card-content'), className='stat-card', md=3),
        dbc.Col(html.Div([html.Div([html.P('Moderadas', className='stat-label'), html.P(str(moderadas), className='stat-number moderada')], className='stat-info-flex'), html.Div('⚠️', className='stat-icon')], className='stat-card-content'), className='stat-card', md=3),
        dbc.Col(html.Div([html.Div([html.P('Leves', className='stat-label'), html.P(str(leves), className='stat-number leve')], className='stat-info-flex'), html.Div('✓', className='stat-icon')], className='stat-card-content'), className='stat-card', md=3),
    ])
    # --- FI DEL BLOC CORREGIT ---

# Callback 5: Manejar botones de filtro (Empresa)
@callback(
    Output('store-filtro-activo', 'data'),
    Output({'type': 'filtro-btn', 'index': ALL}, 'className'),
    Input({'type': 'filtro-btn', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_active_filter(n_clicks):
    filtro_id = ctx.triggered_id['index']
    classnames = ['filter-btn' if index != filtro_id else 'filter-btn filter-btn-active' for index in ['todas', 'Grave', 'Moderada', 'Leve']]
    return filtro_id, classnames

# Callback 6: Actualizar lista de incidencias (Empresa)
@callback(
    Output('incidencias-container', 'children'),
    [Input('store-filtro-activo', 'data'),
     Input('intervalo-actualizacion-empresa', 'n_intervals')]
)
def update_incidencias_list(filtro_activo, n_intervalos):
    incidencias = get_lista_incidencias_activas(filtro_activo)
    if not incidencias:
        return html.P("No hay incidencias para el filtro seleccionado.", className='empty-list-message')
    
    cards = []
    for inc in incidencias:
        badge_class = {'Grave': 'badge-grave', 'Moderada': 'badge-moderada', 'Leve': 'badge-leve'}.get(inc['estado'], '')
        cards.append(html.Div([
            dbc.Row([
                dbc.Col(html.H5(f"ID #{inc['id']} - {inc['cliente_nombre']}"), width=8),
                dbc.Col(html.Span(inc['estado'], className=badge_class), width=4, className='text-align-right'),
            ]),
            html.P(inc['descripcion'], className='incidencia-description'),
            html.Small(f"Verificación: {inc['verificacion']}", className='incidencia-verification-status'),
        ], id={'type': 'incidencia-card', 'index': inc['id']}, className='incidencia-card', n_clicks=0))
    return html.Div(cards)


# Callback 7: Buscar, Clicar en Tarjeta O CERRAR (Empresa)
@callback(
    Output('modal-detalles', 'children'),
    [Input('btn-buscar', 'n_clicks'),
     Input({'type': 'incidencia-card', 'index': ALL}, 'n_clicks'),
     Input({'type': 'btn-close-details', 'index': ALL}, 'n_clicks')],
    State('input-busqueda-id', 'value'),
    prevent_initial_call=True
)
def show_incidencia_details(n_clicks_buscar, n_clicks_tarjetas, n_clicks_cerrar, input_id_busqueda):
    
    triggered_id = ctx.triggered_id
    incidencia_id = None
    
    if not triggered_id: 
        return no_update

    if isinstance(triggered_id, dict) and triggered_id.get('type') == 'btn-close-details':
        return None 

    if triggered_id == 'btn-buscar':
        if not input_id_busqueda:
            return html.Div("Por favor, introduce un ID.", className='modal-error-message')
        incidencia_id = int(input_id_busqueda)
        
    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'incidencia-card':
        if any(n > 0 for n in n_clicks_tarjetas if n is not None):
             incidencia_id = int(triggered_id['index'])
        else:
             return no_update
    
    if not incidencia_id: 
        return no_update
        
    detalles = get_detalles_incidencia(int(incidencia_id))
    
    if not detalles['success']:
        return html.Div(detalles['message'], className='modal-error-message')
    
    inc = detalles['datos_incidencia']
    cli = detalles['datos_cliente']
    
    return html.Div([
        html.Button("X", 
                    id={'type': 'btn-close-details', 'index': inc['id']}, 
                    className='btn-close-details'
        ),
        
        html.H3(f"Detalles de Incidencia #{inc['id']}"),
        dbc.Row([
            dbc.Col(md=6, children=[
                html.H5("Datos de la Incidencia"),
                html.Div([html.Span("Estado:", className='info-label'), html.Span(inc['estado'], className='info-value')], className='info-row'),
                html.Div([html.Span("Fecha:", className='info-label'), html.Span(inc['fecha'], className='info-value')], className='info-row'),
                html.Div([html.Span("Verificación Cliente:", className='info-label'), html.Span(inc['verificacion'], className='info-value')], className='info-row'),
            ]),
            dbc.Col(md=6, children=[
                html.H5(f"Datos del Cliente (Nombre: {cli['nombre']})"),
                html.Div([html.Span("Teléfono:", className='info-label'), html.Span(cli['telefono'], className='info-value')], className='info-row'),
                html.Div([html.Span("Email:", className='info-label'), html.Span(cli['email'], className='info-value')], className='info-row'),
                html.Div([html.Span("Dirección:", className='info-label'), html.Span(cli['direccion'], className='info-value')], className='info-row'),
            ]),
        ]),
        html.Button('Imprimir Informe (PDF)', id='btn-imprimir', className='btn-primary-custom btn-margin-top'),
    ], className='search-box search-box-highlight', style={'marginTop': '20px'})


# Callback 8: Ejecutar Simulación de Detección (Empresa)
@callback(
    Output('sim-resultado', 'children'),
    Input('btn-ejecutar-sim', 'n_clicks'),
    [State('sim-cliente-id', 'value'),
     State('sim-cliente-nombre', 'value')],
    prevent_initial_call=True
)
def ejecutar_simulacion(n_clicks, cliente_id, cliente_nombre):
    if not cliente_id or not cliente_nombre:
        return html.P("Por favor, introduce un ID y un Nombre de cliente.", className='sim-result-error')
    
    resultado = ejecutar_deteccion_lstm(int(cliente_id), cliente_nombre)
    
    return html.P(resultado['message'], className='sim-result-success')


# --- Callbacks Públicos (Móvil y Verificación) ---

# Callback 9: Actualizar el Móvil Simulado (Poller)
@callback(
    Output('div-notificaciones-movil', 'children'),
    Input('intervalo-notificaciones-movil', 'n_intervals'),
    State('store-cliente-id', 'data'),
    State('div-notificaciones-movil', 'children'),
    State('url', 'pathname') 
)
def check_for_notifications(n, cliente_id, notificaciones_actuales, pathname):
    
    if 'verificar' in pathname:
        return no_update

    notificaciones_nuevas = get_notificaciones_pendientes_cliente(cliente_id)
    
    if not notificaciones_nuevas:
        if n == 0:
             return html.P("Esperando notificaciones...", className='mobile-waiting-text')
        else:
            return no_update
        
    cards_nuevas = []
    for notif in notificaciones_nuevas:
        token = notif['link'].split('/')[-1]
        link_interno = f"/sim-movil/{cliente_id}/verificar/{token}"

        cards_nuevas.append(html.Div([
            html.Div(className='notification-app-title', children=[html.Span('🛡️'), html.Span('GesAI')]),
            html.Span("¡Nueva Alerta de Incidencia!", className='notification-title'),
            html.P(f"ID #{notif['notificacion_id']}: Se ha detectado una anomalía. Pulsa para verificar.", className='notification-body'),
            
            dcc.Link("Verificar Ahora", 
                     href=link_interno, 
                     className='notification-link')
                     
        ], className='notification-card'))
        
        marcar_notificacion_leida(notif['notificacion_id'])

    if isinstance(notificaciones_actuales, list):
        return cards_nuevas + notificaciones_actuales
    else:
        return cards_nuevas

# Callback 10: Enviar Encuesta (Cliente/Público)
@callback(
    Output('survey-result', 'children'),
    Input('btn-submit-survey', 'n_clicks'),
    [State('store-token', 'data'),
     State({'type': 'survey-q', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def handle_survey_submission(n_clicks, token, respuestas_lista):
    
    if not token:
        return html.P("Error: Token no encontrado.", className='survey-result-error')
    
    if any(r is None for r in respuestas_lista):
        return html.P("Por favor, responda a todas las 6 preguntas.", className='survey-result-error')
        
    respuestas_encuesta = {f"pregunta_{i+1}": resp for i, resp in enumerate(respuestas_lista)}
    
    resultado = validar_token_y_registrar(token, respuestas_encuesta)
    
    if resultado['success']:
        return html.P(resultado['message'], className='survey-result-success')
    else:
        return html.P(resultado['message'], className='survey-result-error-inline')


# --- 6. EJECUTAR LA APLICACIÓN ---
if __name__ == '__main__':
    app.run(debug=True)