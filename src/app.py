# src/app.py

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc

# --- 1. IMPORTAR EL "CEREBRO" ---
# Importamos las funciones de lógica de negocio desde nuestro otro archivo
from motor_gesai import (
    verificar_credenciales,
    get_lista_incidencias_activas,
    get_detalles_incidencia,
    registrar_verificacion_cliente
)

# --- 2. INICIALIZACIÓN DE LA APP Y CSS ---

# Importar fuentes externas y el tema de Bootstrap
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
]

# *** LA LÍNEA CRÍTICA ***
# Inicializa la app y suprime los errores de callbacks
app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets, 
                suppress_callback_exceptions=True) # <-- ESTO ES LO MÁS IMPORTANTE

app.title = "GesAI"


# --- 3. DEFINICIÓN DE LAYOUTS (Vistas) ---
# Separamos cada "página" en una función para mantener el código limpio.

def build_login_layout():
    """Construye el layout de la página de Inicio de Sesión."""
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div('🛡️', style={'fontSize': '40px', 'color': 'white'}),
                ], className='logo-icon'),
                html.H1('GesAI', className='app-title'),
                html.P('Sistema de Gestión de Incidencias', className='app-subtitle'),
            ], className='logo-container'),
            
            html.Div([
                html.Label('Usuario / Email', style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block', 'color': '#374151'}),
                dcc.Input(
                    id='input-usuario',
                    type='text',
                    placeholder='usuario@gesai.com',
                    style={'width': '100%', 'padding': '12px 16px', 'borderRadius': '10px', 'border': '1px solid #d1d5db', 'fontSize': '14px', 'marginBottom': '20px'}
                ),
            ]),
            
            html.Div([
                html.Label('Contraseña', style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block', 'color': '#374151'}),
                dcc.Input(
                    id='input-password', # ID corregido
                    type='password',
                    placeholder='••••••••',
                    style={'width': '100%', 'padding': '12px 16px', 'borderRadius': '10px', 'border': '1px solid #d1d5db', 'fontSize': '14px', 'marginBottom': '20px'}
                ),
            ]),
            
            html.Div(id='login-error', style={'marginBottom': '15px'}),
            
            html.Button(
                'Iniciar Sesión',
                id='btn-login',
                n_clicks=0,
                className='btn-primary-custom',
                style={'width': '100%', 'fontSize': '15px'}
            ),
            
            html.Div([
                html.Hr(style={'margin': '30px 0', 'borderColor': '#e5e7eb'}),
                html.P('Cuentas de prueba:', style={'fontSize': '12px', 'color': '#6b7280', 'textAlign': 'center', 'marginBottom': '10px'}),
                html.P('👔 Empresa: empresa@gesai.com / 1234', style={'fontSize': '12px', 'color': '#6b7280', 'marginBottom': '5px'}),
                html.P('👤 Cliente: cliente@gesai.com / abcd', style={'fontSize': '12px', 'color': '#6b7280'}),
            ]),
        ], className='login-card'),
    ], className='login-container')

def build_empresa_layout(session_data):
    """Construye el layout del Dashboard de Empresa."""
    nombre_usuario = session_data.get('nombre', 'Usuario')
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Div([
                    html.Div('🛡️', style={'fontSize': '24px', 'color': 'white'}),
                ], style={'width': '45px', 'height': '45px', 'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'borderRadius': '10px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginRight': '15px'}),
                html.Div([
                    html.H3('GesAI Dashboard', style={'margin': '0', 'fontSize': '20px', 'fontWeight': '700'}),
                    html.P('Panel de Control Empresarial', style={'margin': '0', 'fontSize': '13px', 'color': '#6b7280'}),
                ]),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            
            html.Div([
                html.Div([
                    html.Span('🏢 ', style={'marginRight': '8px'}),
                    html.Span(nombre_usuario, style={'fontWeight': '600', 'color': '#374151'}),
                ], style={'padding': '10px 20px', 'background': '#eff6ff', 'borderRadius': '10px', 'marginRight': '15px'}),
                html.Button('Cerrar Sesión', 
            id={'type': 'btn-logout', 'index': 'empresa'}, n_clicks=0, style={'padding': '10px 20px', 'background': '#fee2e2', 'color': '#dc2626', 'border': 'none', 'borderRadius': '10px', 'fontWeight': '600', 'cursor': 'pointer'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, className='header-dashboard'),
        
        # Contenido del Dashboard
        html.Div([
            html.Div(id='stats-container', style={'marginBottom': '30px'}),
            
            html.Div([
                html.Div([
                    dcc.Input(id='input-busqueda-id', type='number', placeholder='Buscar por ID de incidencia...', style={'flex': '1', 'padding': '12px 16px', 'borderRadius': '10px', 'border': '1px solid #d1d5db', 'marginRight': '10px'}),
                    html.Button('🔍 Buscar', id='btn-buscar', n_clicks=0, className='btn-primary-custom'),
                ], style={'display': 'flex', 'marginBottom': '20px'}),
                
                html.Div([
                    html.Span('Filtrar por estado:', style={'marginRight': '15px', 'fontWeight': '600', 'color': '#374151'}),
                    html.Button('Todas', id={'type': 'filtro-btn', 'index': 'todas'}, n_clicks=0, className='filter-btn filter-btn-active'),
                    html.Button('Grave', id={'type': 'filtro-btn', 'index': 'Grave'}, n_clicks=0, className='filter-btn'),
                    html.Button('Moderada', id={'type': 'filtro-btn', 'index': 'Moderada'}, n_clicks=0, className='filter-btn'),
                    html.Button('Leve', id={'type': 'filtro-btn', 'index': 'Leve'}, n_clicks=0, className='filter-btn'),
                ], style={'display': 'flex', 'alignItems': 'center'}),
            ], className='search-box'),
            
            dcc.Store(id='store-filtro-activo', data='todas'),
            html.Div(id='modal-detalles'),
            html.Div(id='incidencias-container'),
            
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '40px 20px'}),
    ])

def build_cliente_layout(session_data):
    """Construye el layout del Portal de Cliente."""
    nombre_usuario = session_data.get('nombre', 'Cliente')
    incidencia_id = session_data.get('datos_extra', {}).get('incidencia_id')
    detalles = get_detalles_incidencia(incidencia_id) if incidencia_id else None
    
    # Header común
    header = html.Div([
        html.Div([
            html.Div('🛡️', style={'fontSize': '24px', 'color': 'white'}),
            html.H3('GesAI - Portal del Cliente', style={'margin': '0 0 0 15px', 'fontSize': '20px', 'fontWeight': '700', 'color': 'white'}),
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Button('Cerrar Sesión', id={'type': 'btn-logout', 'index': 'cliente'}, n_clicks=0, style={'padding': '10px 20px', 'background': 'white', 'color': '#667eea', 'border': 'none', 'borderRadius': '10px', 'fontWeight': '600', 'cursor': 'pointer'}),
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'padding': '20px 40px'})

    # Contenido si NO hay incidencia
    if not detalles or not detalles['success']:
        return html.Div([
            header,
            html.Div([
                html.H2('Todo en orden', style={'textAlign': 'center', 'marginTop': '50px', 'color': '#374151'}),
                html.P(f'¡Hola, {nombre_usuario}! No tienes ninguna incidencia activa en este momento.', style={'textAlign': 'center', 'fontSize': '18px', 'color': '#6b7280'}),
            ], style={'maxWidth': '800px', 'margin': '50px auto', 'padding': '20px'})
        ])

    # Contenido si SÍ hay incidencia
    inc = detalles['datos_incidencia']
    return html.Div([
        header,
        html.Div([
            html.Div([
                html.H2('⚠️ Verificación de Incidencia Requerida', style={'color': 'white', 'marginBottom': '15px', 'fontSize': '28px'}),
                html.P('Se ha detectado una posible anomalía en su consumo. Por favor, verifique la información.', style={'color': 'rgba(255,255,255,0.9)', 'fontSize': '16px', 'marginBottom': '30px'}),
                
                html.Div([
                    html.Div([
                        html.Span('ID Incidencia:', className='info-label', style={'color': 'rgba(255,255,255,0.8)'}),
                        html.Span(f"#{inc['id']}", style={'color': 'white', 'fontWeight': '700', 'fontSize': '18px'}),
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '15px'}),
                    html.Div([
                        html.Span('Fecha de Detección:', className='info-label', style={'color': 'rgba(255,255,255,0.8)'}),
                        html.Span(inc['fecha'], style={'color': 'white', 'fontWeight': '600'}),
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '15px'}),
                    html.Div([
                        html.Span('Estado:', className='info-label', style={'color': 'rgba(255,255,255,0.8)'}),
                        html.Span(inc['estado'], style={'color': 'white', 'fontWeight': '600'}),
                    ]),
                ], style={'background': 'rgba(255,255,255,0.1)', 'padding': '25px', 'borderRadius': '12px', 'marginBottom': '30px'}),
                
                html.H3('¿Reconoce esta actividad como suya?', style={'color': 'white', 'marginBottom': '20px', 'fontSize': '20px'}),
                
                html.Div([
                    html.Button('✅ SÍ, es mi actividad', id='btn-verificar-si', n_clicks=0, style={'flex': '1', 'padding': '15px', 'background': '#10b981', 'color': 'white', 'border': 'none', 'borderRadius': '10px', 'fontSize': '16px', 'fontWeight': '600', 'cursor': 'pointer', 'marginRight': '15px'}),
                    html.Button('❌ NO, no reconozco esta actividad', id='btn-verificar-no', n_clicks=0, style={'flex': '1', 'padding': '15px', 'background': '#ef4444', 'color': 'white', 'border': 'none', 'borderRadius': '10px', 'fontSize': '16px', 'fontWeight': '600', 'cursor': 'pointer'}),
                ], style={'display': 'flex', 'gap': '15px'}),
                
                html.Div(id='verification-result', style={'marginTop': '20px'}),
                
                html.Div([
                    html.Hr(style={'borderColor': 'rgba(255,255,255,0.2)', 'margin': '30px 0'}),
                    html.P('📞 ¿Necesita más información?', style={'color': 'white', 'fontSize': '16px', 'marginBottom': '10px'}),
                    html.Button('Contactar con Soporte', id='btn-contacto', style={'padding': '12px 24px', 'background': 'white', 'color': '#667eea', 'border': 'none', 'borderRadius': '10px', 'fontWeight': '600', 'cursor': 'pointer'}),
                ]),
            ], className='verification-card'),
        ], style={'maxWidth': '800px', 'margin': '50px auto', 'padding': '20px'}),
        
        dcc.Store(id='store-incidencia-id', data=incidencia_id),
    ])


# --- 4. LAYOUT PRINCIPAL (Router) ---
# Este es el único layout que la app carga al inicio.
app.layout = html.Div([
    # dcc.Location detecta la URL
    dcc.Location(id='url', refresh=False),
    # dcc.Store guarda la sesión del usuario
    dcc.Store(id='session-store', storage_type='session', data={'logged_in': False}),
    # El contenedor donde se dibujarán las "páginas"
    html.Div(id='page-content')
])


# --- 5. CALLBACKS ---

# Callback 1: Router principal
# Decide qué página mostrar basado en la URL y la Sesión
@callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'),
     Input('session-store', 'data')]
)
def display_page(pathname, session_data):
    if not session_data or not session_data.get('logged_in'):
        # Si no está logueado, siempre mostrar login
        return build_login_layout()
    else:
        # Si está logueado
        if session_data['rol'] == 'Empresa':
            return build_empresa_layout(session_data)
        elif session_data['rol'] == 'Cliente':
            return build_cliente_layout(session_data)
        
    # Por defecto, si algo falla, mostrar login
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
        return no_update, html.Div('Por favor, complete todos los campos.', style={'color': 'red'}), no_update
    
    # Llama al motor importado
    resultado = verificar_credenciales(usuario, password)
    
    if resultado['success']:
        session_data = {
            'logged_in': True,
            'rol': resultado['rol'],
            'nombre': resultado['nombre'],
            'datos_extra': resultado.get('datos_extra', {})
        }
        # Guardar sesión y redirigir a la URL base
        return session_data, None, '/'
    else:
        # No guardar sesión, mostrar error, no redirigir
        return no_update, html.Div(resultado['message'], style={'color': 'red'}), no_update

# Callback 3: Lógica de Cerrar Sesión (Logout)
@callback(
    [Output('session-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    # --- *** INICIO DE LA CORRECCIÓN *** ---
    # Escucha a CUALQUIER botón cuyo ID coincida con el "tipo"
    [Input({'type': 'btn-logout', 'index': ALL}, 'n_clicks')],
    # --- *** FIN DE LA CORRECCIÓN *** ---
    prevent_initial_call=True
)
def logout(n_clicks_lista):
    
    # n_clicks_lista será una lista, ej. [1, 0] o [None, 1]
    # Comprobamos si alguno de los botones fue pulsado
    
    if any(n > 0 for n in n_clicks_lista if n is not None):
        # Si se ha hecho clic en CUALQUIERA de los botones de logout,
        # borrar la sesión y redirigir
        return {'logged_in': False}, '/'
    
    # Si no, no hacer nada
    return no_update, no_update

# --- Callbacks del Dashboard EMPRESA ---

# Callback 4: Estadísticas Empresa
@callback(
    Output('stats-container', 'children'),
    Input('session-store', 'data') # Se activa solo una vez al cargar el layout
)
def update_stats(session_data):
    if not session_data.get('logged_in') or session_data.get('rol') != 'Empresa':
        return None # No dibujar nada si no es empresa
        
    incidencias = get_lista_incidencias_activas("todas")
    total = len(incidencias)
    graves = len([i for i in incidencias if i['estado'] == 'Grave'])
    moderadas = len([i for i in incidencias if i['estado'] == 'Moderada'])
    leves = len([i for i in incidencias if i['estado'] == 'Leve'])
    
    return dbc.Row([
        dbc.Col(html.Div([html.Div([html.P('Total Activas', className='stat-label'), html.P(str(total), className='stat-number', style={'color': '#3b82f6'})], style={'flex': '1'}), html.Div('📊', style={'fontSize': '40px'})], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, className='stat-card'), md=3),
        dbc.Col(html.Div([html.Div([html.P('Graves', className='stat-label'), html.P(str(graves), className='stat-number', style={'color': '#dc2626'})], style={'flex': '1'}), html.Div('🚨', style={'fontSize': '40px'})], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, className='stat-card'), md=3),
        dbc.Col(html.Div([html.Div([html.P('Moderadas', className='stat-label'), html.P(str(moderadas), className='stat-number', style={'color': '#d97706'})], style={'flex': '1'}), html.Div('⚠️', style={'fontSize': '40px'})], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, className='stat-card'), md=3),
        dbc.Col(html.Div([html.Div([html.P('Leves', className='stat-label'), html.P(str(leves), className='stat-number', style={'color': '#059669'})], style={'flex': '1'}), html.Div('✓', style={'fontSize': '40px'})], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, className='stat-card'), md=3),
    ])

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
    Input('store-filtro-activo', 'data')
)
def update_incidencias_list(filtro_activo):
    incidencias = get_lista_incidencias_activas(filtro_activo)
    if not incidencias:
        return html.P("No hay incidencias para el filtro seleccionado.", style={'textAlign': 'center', 'marginTop': '30px', 'color': '#6b7280'})
    
    cards = []
    for inc in incidencias:
        badge_class = {'Grave': 'badge-grave', 'Moderada': 'badge-moderada', 'Leve': 'badge-leve'}.get(inc['estado'], '')
        
        # --- *** INICIO DEL CAMBIO *** ---
        # Añadimos un ID dinámico y n_clicks a cada tarjeta.
        # Esto las convierte en "botones" clicables.
        card = html.Div([
            dbc.Row([
                dbc.Col(html.H5(f"ID #{inc['id']} - {inc['cliente_nombre']}"), width=8),
                dbc.Col(html.Span(inc['estado'], className=badge_class), width=4, style={'textAlign': 'right'}),
            ]),
            html.P(inc['descripcion'], style={'color': '#374151', 'margin': '10px 0'}),
            html.Small(f"Detectada: {inc['fecha']}", style={'color': '#6b7280'}),
        ], 
        id={'type': 'incidencia-card', 'index': inc['id']}, # <-- ID DINÁMICO
        className='incidencia-card',
        n_clicks=0 # <-- HACE CLICABLE
        )
        # --- *** FIN DEL CAMBIO *** ---
        cards.append(card)
        
    return html.Div(cards)

# Callback 7: Buscar por ID O hacer clic en tarjeta (Empresa)
@callback(
    Output('modal-detalles', 'children'),
    [Input('btn-buscar', 'n_clicks'),
     Input({'type': 'incidencia-card', 'index': ALL}, 'n_clicks')], # <-- NUEVO INPUT
    State('input-busqueda-id', 'value'),
    prevent_initial_call=True
)
def show_incidencia_details(n_clicks_buscar, n_clicks_tarjetas, input_id_busqueda):
    
    # --- *** INICIO DE LA NUEVA LÓGICA *** ---
    triggered_id = ctx.triggered_id
    incidencia_id = None
    
    if not triggered_id:
        return no_update # No hacer nada si no hay trigger

    # Comprobar si se pulsó el botón "Buscar"
    if triggered_id == 'btn-buscar':
        if not input_id_busqueda:
            return html.Div("Por favor, introduce un ID.", style={'color': 'red', 'marginTop': '10px'})
        incidencia_id = int(input_id_busqueda)
        
    # Comprobar si se pulsó una de las tarjetas
    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'incidencia-card':
        # Comprobar si esta tarjeta tiene clics (n_clicks_tarjetas es una lista)
        for i, n in enumerate(n_clicks_tarjetas):
            if n > 0:
                incidencia_id = int(triggered_id['index'])
                break # Encontramos la tarjeta clicada
    
    if not incidencia_id:
        # Esto pasa si se hace clic en una tarjeta y luego en otra (se resetea n_clicks)
        # No es un error, simplemente no actualizamos la vista
        return no_update 
    # --- *** FIN DE LA NUEVA LÓGICA *** ---

    detalles = get_detalles_incidencia(int(incidencia_id))
    
    if not detalles['success']:
        return html.Div(detalles['message'], style={'color': 'red', 'marginTop': '10px'})
    
    # Si se encuentra, mostrar la tarjeta de detalles
    inc = detalles['datos_incidencia']
    cli = detalles['datos_cliente']
    
    # El layout de detalles es el mismo, ahora se muestra con CUALQUIERA de las dos acciones
    return html.Div([
        html.H3(f"Detalles de Incidencia #{inc['id']}"),
        dbc.Row([
            dbc.Col([
                html.H5("Datos de la Incidencia"),
                html.Div([html.Span("Estado:", className='info-label'), html.Span(inc['estado'], className='info-value')], className='info-row'),
                html.Div([html.Span("Fecha:", className='info-label'), html.Span(inc['fecha'], className='info-value')], className='info-row'),
                html.Div([html.Span("Verificación Cliente:", className='info-label'), html.Span(inc['verificacion'], className='info-value')], className='info-row'),
                html.Div([html.Span("Confianza Modelo:", className='info-label'), html.Span(inc['confianza_modelo'], className='info-value')], className='info-row'),
            ], md=6),
            dbc.Col([
                html.H5(f"Datos del Cliente (Nombre: {cli['nombre']})"),
                html.Div([html.Span("Teléfono:", className='info-label'), html.Span(cli['telefono'], className='info-value')], className='info-row'),
                html.Div([html.Span("Email:", className='info-label'), html.Span(cli['email'], className='info-value')], className='info-row'),
                html.Div([html.Span("Dirección:", className='info-label'), html.Span(cli['direccion'], className='info-value')], className='info-row'),
            ], md=6),
        ]),
        html.Button('Imprimir Informe (PDF)', id='btn-imprimir', className='btn-primary-custom', style={'marginTop': '20px'}),
        html.Button('Contactar Cliente', id='btn-contactar', style={'marginLeft': '10px', 'padding': '10px 20px', 'background': '#fee2e2', 'color': '#dc2626', 'border': 'none', 'borderRadius': '10px', 'fontWeight': '600', 'cursor': 'pointer'}),
    ], className='search-box', style={'marginTop': '20px', 'borderLeft': '5px solid #667eea'})
# --- Callbacks del Dashboard CLIENTE ---

# Callback 8: Verificación del Cliente
@callback(
    Output('verification-result', 'children'),
    [Input('btn-verificar-si', 'n_clicks'),
     Input('btn-verificar-no', 'n_clicks')],
    State('store-incidencia-id', 'data'),
    prevent_initial_call=True
)
def handle_verification(n_si, n_no, incidencia_id):
    triggered_id = ctx.triggered_id
    if not incidencia_id:
        return html.P("Error: No se ha podido encontrar el ID de la incidencia.", style={'color': '#ef4444'})
        
    respuesta = "SI" if triggered_id == 'btn-verificar-si' else "NO"
    
    resultado = registrar_verificacion_cliente(incidencia_id, respuesta)
    
    if resultado['success']:
        return html.P(resultado['message'], style={'color': 'white', 'background': 'rgba(255,255,255,0.2)', 'padding': '10px', 'borderRadius': '8px'})
    else:
        return html.P("Error al registrar la respuesta.", style={'color': '#ef4444'})


# --- 6. EJECUTAR LA APLICACIÓN ---
if __name__ == '__main__':
    app.run(debug=True)