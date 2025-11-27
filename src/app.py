# src/app.py
import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import os

# Importamos solo funciones de LECTURA y UTILIDAD (El cerebro IA está en el backend)
from motor_gesai import (
    verificar_credenciales,
    get_lista_incidencias_activas,
    get_detalles_incidencia,
    get_notificaciones_pendientes_cliente,
    marcar_notificacion_leida,
    validar_token_y_registrar
)
from reports_manager import generar_informe_tecnico_pdf

# --- CONFIGURACIÓN DE RUTAS ---
# Calculamos la ruta absoluta a la carpeta 'assets' (que está un nivel por encima de src)
current_dir = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(current_dir, 'assets')

# Inicialización
external_stylesheets = [
    dbc.themes.BOOTSTRAP, 
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
]

app = dash.Dash(
    __name__, 
    external_stylesheets=external_stylesheets, 
    suppress_callback_exceptions=True, 
    assets_folder=assets_path 
)
app.title = "GeSAI Dashboard"


# --- VISTAS ---

def build_login_layout():
    """Página de Login Limpia."""
    return html.Div(className='login-container', children=[
        html.Div(className='login-card', children=[
            html.Div(className='logo-container', children=[
                html.Img(src=app.get_asset_url('logo_1.png'), className='logo-login'),
                html.P('Portal de Gestión de Incidencias', className='app-subtitle'),
            ]),
            html.Div([
                html.Label('Usuario Corporativo', className='form-label'),
                dcc.Input(id='input-usuario', type='text', placeholder='empresa@gesai.com', className='form-input'),
            ]),
            html.Div([
                html.Label('Contraseña', className='form-label'),
                dcc.Input(id='input-password', type='password', placeholder='••••••••', className='form-input'),
            ]),
            html.Div(id='login-error', className='login-error-message'),
            html.Button('Acceder al Sistema', id='btn-login', n_clicks=0, className='btn-primary-custom btn-full-width'),
            html.Div([
                html.Div(className='login-divider'),
                html.P('Credenciales Demo: empresa@gesai.com / 1234', className='login-test-info'),
            ]),
        ]),
    ])


def build_empresa_layout(session_data):
    nombre_usuario = session_data.get('nombre', 'Admin')
    return html.Div([
        # Intervalo de refresco automático (2 segundos)
        dcc.Interval(id='intervalo-refresco', interval=2000, n_intervals=0),
        
        # Header
        html.Div(className='header-dashboard', children=[
            html.Div(className='layout-flex-center', children=[
                html.Img(src=app.get_asset_url('logo_2.png'), className='logo-dashboard'),
                html.H3('Panel de Control', className='dashboard-title'),
            ]),
            html.Div(className='layout-flex-center', children=[
                html.Div(className='user-info-badge', children=[
                    html.Span('👤 ', style={'marginRight': '5px'}), 
                    html.Span(nombre_usuario)
                ]),
                html.Button('Salir', id={'type': 'btn-logout', 'index': 'empresa'}, n_clicks=0, className='btn-logout')
            ]),
        ]),
        
        # Contenido Principal
        html.Div(className='main-content-container', children=[
            
            # 1. Stats Cards
            html.Div(id='stats-container', className='stats-container-spacing'),
            
            # 2. Barra de Herramientas (Filtros)
            html.Div(className='search-box', children=[
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}, children=[
                    html.Div(className='layout-flex-center', children=[
                        html.Span('Filtrar Estado:', className='filter-label'),
                        html.Button('Todas', id={'type': 'filtro-btn', 'index': 'todas'}, n_clicks=0, className='filter-btn filter-btn-active'),
                        html.Button('Grave', id={'type': 'filtro-btn', 'index': 'Grave'}, n_clicks=0, className='filter-btn'),
                        html.Button('Moderada', id={'type': 'filtro-btn', 'index': 'Moderada'}, n_clicks=0, className='filter-btn'),
                        html.Button('Requiere Carta', id={'type': 'filtro-btn', 'index': 'CARTA'}, n_clicks=0, className='filter-btn', style={'color': '#0072BC', 'borderColor': '#0072BC'}),
                    ]),
                ]),
            ]),
            
            dcc.Store(id='store-filtro-activo', data='todas'),
            
            # 3. Área de Detalles (Popup)
            html.Div(id='modal-detalles'),
            
            # 4. Lista de Incidencias
            html.Div(id='incidencias-container'),
            html.Div(id='dummy-download-output')
        ]),
    ])

def _build_survey_layout(token):
    """Función helper que construye la encuesta."""
    preguntas = [
        "1. ¿Ha notado un sonido de agua corriendo (siseo)?",
        "2. ¿Algún grifo o cisterna pierde agua?",
        "3. ¿El contador se mueve con todo cerrado?",
        "4. ¿Ha detectado humedades recientes?",
        "5. ¿Ha habido obras recientes?",
        "6. ¿Considera su consumo normal?"
    ]
    opciones = [
        {'label': 'Sí', 'value': 'SI'},
        {'label': 'No', 'value': 'NO'},
        {'label': 'No lo sé', 'value': 'NO_SE'},
    ]
    
    return html.Div([
        html.H5("Verificación de Incidencia", className='survey-title'),
        html.P("Responda para ayudar a nuestro diagnóstico.", className='survey-subtitle'),
        dcc.Store(id='store-token', data=token),
        
        *[html.Div([
            html.Label(preg, className='survey-question-label'),
            dbc.RadioItems(
                id={'type': 'survey-q', 'index': i+1},
                options=opciones,
                value=None,
                className='survey-radio-group'
            )
        ]) for i, preg in enumerate(preguntas)],
        
        html.Button('Confirmar y Enviar', id='btn-submit-survey', n_clicks=0, className='btn-primary-custom btn-full-width btn-margin-top'),
        html.Div(id='survey-result', className='survey-result-container')
    ])

def _build_confirmation_layout(cliente_id):
    return html.Div([
        html.Div(className='survey-confirmation-card', style={'textAlign': 'center', 'padding': '40px'}, children=[
            html.Div('✅', style={'fontSize': '50px', 'marginBottom': '20px'}),
            html.H3('Recibido', style={'color': '#0072BC'}),
            html.P('Gracias. Hemos registrado sus respuestas.', style={'color': '#555'}),
            dcc.Link("Volver", href=f"/sim-movil/{cliente_id}", className='btn-primary-custom', style={'textDecoration': 'none', 'marginTop': '30px', 'display': 'inline-block'})
        ])
    ])

def build_simulador_movil_layout(cliente_id, pathname):
    contenido_pantalla = None
    titulo = "Notificaciones"
    
    if 'verificar' in pathname:
        token = pathname.split('/')[-1]
        contenido_pantalla = _build_survey_layout(token)
        titulo = "Encuesta"
    elif 'confirmacion' in pathname:
        contenido_pantalla = _build_confirmation_layout(cliente_id)
        titulo = "Éxito"
    else:
        contenido_pantalla = html.Div(id='div-notificaciones-movil', children=[
            html.P("Sin notificaciones nuevas", className='mobile-waiting-text')
        ])
        
    return html.Div(className='mobile-frame', children=[
        dcc.Store(id='store-cliente-id', data=cliente_id),
        dcc.Interval(id='intervalo-notificaciones-movil', interval=3000, n_intervals=0),
        
        html.Div(className='mobile-screen', children=[
            html.Div(className='mobile-island'),
            html.Div(className='mobile-header', children=[html.H5(titulo, className='mobile-header-title')]),
            html.Div(className='mobile-notifications-area', children=[contenido_pantalla]),
            html.Div(className='mobile-home-bar')
        ])
    ])

# --- ROUTER ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session', data={'logged_in': False}),
    # Stores globales para evitar errores de callback
    dcc.Store(id='store-filtro-activo', data='todas'),
    html.Div(id='page-content')
])

# --- CALLBACKS ---

@callback(Output('page-content', 'children'), Input('url', 'pathname'), State('session-store', 'data'))
def display_page(pathname, session_data):
    parts = pathname.strip('/').split('/')
    
    if len(parts) >= 2 and parts[0] == 'sim-movil':
            cliente_id = parts[1] # Mantenemos como texto (póliza)
            return build_simulador_movil_layout(cliente_id, pathname)
                
    if session_data and session_data.get('logged_in'):
        if pathname == '/' or pathname == '/dashboard':
            return build_empresa_layout(session_data)
        if pathname == '/login':
            return dcc.Location(pathname='/', id='redirect-to-home')
    
    return build_login_layout()

@callback(
    [Output('session-store', 'data'), Output('login-error', 'children'), Output('url', 'pathname')],
    Input('btn-login', 'n_clicks'), [State('input-usuario', 'value'), State('input-password', 'value')],
    prevent_initial_call=True
)
def login(n, u, p):
    res = verificar_credenciales(u, p)
    if res['success']: return {'logged_in': True, 'rol': 'Empresa', 'nombre': res['nombre']}, None, '/'
    return no_update, html.Div(res['message']), no_update

@callback([Output('session-store', 'data', allow_duplicate=True), Output('url', 'pathname', allow_duplicate=True)], Input({'type': 'btn-logout', 'index': ALL}, 'n_clicks'), prevent_initial_call=True)
def logout(n): return {'logged_in': False}, '/'

@callback([Output('stats-container', 'children'), Output('incidencias-container', 'children')], [Input('intervalo-refresco', 'n_intervals'), Input('store-filtro-activo', 'data')])
def refresh_dashboard(n, filtro):
    filtro = filtro or 'todas'
    if filtro == 'CARTA':
        todas = get_lista_incidencias_activas("todas")
        incidencias = [i for i in todas if 'CARTA' in str(i.get('verificacion', '')).upper()]
    else:
        incidencias = get_lista_incidencias_activas(filtro)
    
    # Stats
    todas = get_lista_incidencias_activas("todas")
    total = len(todas)
    graves = len([i for i in todas if 'Grave' in i.get('estado','')])
    cartas = len([i for i in todas if 'CARTA' in str(i.get('verificacion', '')).upper()])
    
    stats = dbc.Row([
        dbc.Col(html.Div([html.Div([html.P('Total Activas', className='stat-label'), html.P(str(total), className='stat-number total')], className='stat-info-flex'), html.Div('📊', className='stat-icon')], className='stat-card'), width=4),
        dbc.Col(html.Div([html.Div([html.P('Fugas Graves', className='stat-label'), html.P(str(graves), className='stat-number grave')], className='stat-info-flex'), html.Div('🚨', className='stat-icon')], className='stat-card'), width=4),
        dbc.Col(html.Div([html.Div([html.P('Cartas Enviadas', className='stat-label'), html.P(str(cartas), className='stat-number moderada')], className='stat-info-flex'), html.Div('📮', className='stat-icon')], className='stat-card'), width=4),
    ])

    # Cards
    cards = []
    if not incidencias:
        cards = html.P("Esperando incidencias...", className='empty-list-message')
    else:
        for inc in incidencias:
            st = inc.get('estado', '')
            badge = 'badge-grave' if 'Grave' in st else ('badge-moderada' if 'Moderada' in st else 'badge-leve')
            extra = " 📮" if 'CARTA' in str(inc.get('verificacion', '')) else ""
            
            cards.append(html.Div([
                dbc.Row([
                    dbc.Col(html.H5(f"#{inc['id']} • {inc['cliente_nombre']}"), width=8),
                    dbc.Col(html.Span(f"{st}{extra}", className=badge), width=4, className='text-align-right'),
                ]),
                html.P(inc['descripcion'], className='incidencia-description'),
                html.Small(f"Estado: {inc['verificacion']}", className='incidencia-verification-status'),
            ], id={'type': 'incidencia-card', 'index': inc['id']}, className='incidencia-card', n_clicks=0))
            
    return stats, html.Div(cards)

# --- CORRECCIÓN DEL CALLBACK DE FILTROS (Evita el error de lista) ---
@callback(
    Output('store-filtro-activo', 'data'),
    Output({'type': 'filtro-btn', 'index': ALL}, 'className'),
    Input({'type': 'filtro-btn', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_filter(n_clicks):
    triggered = ctx.triggered_id
    
    # Si no hay trigger válido o clicks, devolvemos lista de no_update para evitar error
    if not triggered or not any(n_clicks):
        return no_update, [no_update] * len(n_clicks)

    # Obtener ID del filtro pulsado
    fid = triggered.get('index') if isinstance(triggered, dict) else 'todas'
    
    # Generar lista de clases CORRECTA (coincidiendo con CSS)
    # El orden de 'ids' debe coincidir con el orden de creación de botones en el layout
    ids = ['todas', 'Grave', 'Moderada', 'CARTA']
    
    # Generamos la lista de clases dinámicamente
    classnames = []
    for i in ids:
        if i == fid:
            classnames.append('filter-btn filter-btn-active')
        else:
            classnames.append('filter-btn')
            
    return fid, classnames
# --------------------------------------------------------------------

@callback(Output('modal-detalles', 'children'), [Input({'type': 'incidencia-card', 'index': ALL}, 'n_clicks'), Input({'type': 'btn-close-details', 'index': ALL}, 'n_clicks'), Input({'type': 'btn-download-report', 'index': ALL}, 'n_clicks')], prevent_initial_call=True)
def handle_details(n_card, n_close, n_down):
    tid = ctx.triggered_id
    if not tid or (isinstance(tid, dict) and tid.get('type') == 'btn-close-details'): return None
    
    if isinstance(tid, dict) and tid.get('type') == 'btn-download-report':
        inc_id = tid['index']
        data = get_detalles_incidencia(inc_id)
        if data.get('success'):
            try:
                hist = pd.DataFrame({'FECHA_HORA': pd.date_range(start='2024-01-01', periods=24, freq='h'), 'CONSUMO_REAL': [10]*20 + [80, 90, 100, 110]})
                generar_informe_tecnico_pdf(inc_id, data['datos_cliente'], data['datos_incidencia'], hist)
            except: pass
        return no_update

    if isinstance(tid, dict) and tid.get('type') == 'incidencia-card':
        if not any(n_card): return no_update
        data = get_detalles_incidencia(tid.get('index'))
        if not data.get('success'): return no_update
        inc, cli = data['datos_incidencia'], data['datos_cliente']
        
        return html.Div([
            html.Button("✕", id={'type': 'btn-close-details', 'index': inc['id']}, className='btn-close-details'),
            html.H3(f"Incidencia #{inc['id']}", style={'color': '#0072BC', 'marginTop': '0'}),
            dbc.Row([
                dbc.Col([html.H5("Detalles"), html.P(f"Estado: {inc['estado']}"), html.P(f"Verificación: {inc['verificacion']}")], md=6),
                dbc.Col([html.H5("Cliente"), html.P(f"{cli.get('nombre')}"), html.P(f"{cli.get('direccion')}")], md=6)
            ]),
            html.Button('Descargar Informe Técnico', id={'type': 'btn-download-report', 'index': inc['id']}, className='btn-primary-custom btn-full-width btn-margin-top')
        ], className='search-box search-box-highlight', style={'position': 'sticky', 'top': '20px', 'zIndex': 10})

@callback(Output('div-notificaciones-movil', 'children'), Input('intervalo-notificaciones-movil', 'n_intervals'), State('store-cliente-id', 'data'), State('url', 'pathname'))
def mobile_poll(n, cid, path):
    if 'verificar' in path or 'confirmacion' in path: return no_update
    notifs = get_notificaciones_pendientes_cliente(cid)
    if not notifs: return no_update
    cards = []
    for notif in notifs:
        link = f"/sim-movil/{cid}/verificar/{notif['link'].split('/')[-1]}"
        cards.append(html.Div([
            html.Div([html.Span('💧'), html.Span('GeSAI App')], className='notification-app-title'),
            html.Span("Alerta de Fuga", className='notification-title'),
            html.P(notif['mensaje'], className='notification-body'),
            dcc.Link("Verificar", href=link, className='notification-link')
        ], className='notification-card'))
        marcar_notificacion_leida(notif['notificacion_id'])
    return cards

@callback([Output('survey-result', 'children'), Output('url', 'pathname', allow_duplicate=True)], Input('btn-submit-survey', 'n_clicks'), [State('store-token', 'data'), State({'type': 'survey-q', 'index': ALL}, 'value'), State('url', 'pathname')], prevent_initial_call=True)
def submit_survey(n, token, resps, path):
    if not token or any(r is None for r in resps): return html.P("Complete todo", className='survey-result-error'), no_update
    validar_token_y_registrar(token, {})
    return no_update, "/".join(path.split('/')[:3]) + "/confirmacion"

if __name__ == '__main__':
    app.run(debug=True)