# src/app.py
import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
from flask import send_file
import os

# --- IMPORTS DE BACKEND ---
from motor_gesai import (
    verificar_credenciales,
    get_lista_incidencias_activas,
    get_detalles_incidencia,
    get_notificaciones_pendientes_cliente,
    marcar_notificacion_leida,
    validar_token_y_registrar
)
from reports_manager import generar_informe_tecnico_pdf, generar_carta_postal_pdf

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(current_dir, "assets")

# --- INICIALIZACIÓN DASH ---
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    # la fuente Inter también está importada en CSS; mantenemos el enlace por compatibilidad
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    assets_folder=assets_path,
    title="GeSAI Dashboard"
)


# ------------------------------------------------------------
# HELPERS / COMPONENTS (reutilizables)
# ------------------------------------------------------------
def kpi_card(titulo, valor, icono):
    return html.Div(className='kpi animated-fade', children=[
        html.Div([html.Div(titulo, className='kpi-label'), html.Div(str(valor), className='kpi-value')]),
        html.Div(icono, className='kpi-icon')
    ])


def incidencia_card(inc):
    st = str(inc.get('estado', '')).upper()
    ver = str(inc.get('verificacion', '')).upper()

    color = '#10B981'
    if 'GRAVE' in st:
        color = '#EF4444'
    elif 'MODERADA' in st:
        color = '#F59E0B'

    extra = ' 📮' if 'CARTA' in ver else ''

    if 'GRAVE' in st:
        badge_class = 'badge-grave'
    elif 'MODERADA' in st:
        badge_class = 'badge-moderada'

    return html.Div(
        className='incidencia animated-fade',
        id={'type': 'incidencia-card', 'index': inc['id']},
        n_clicks=0,
        children=[
            html.Div(className='incidencia-severity', style={'background': color}),
            html.Div(className='incidencia-body', children=[
                html.Div(className='incidencia-title-row', children=[
                    html.Div(f"#{inc['id']} • {inc.get('cliente_nombre','-')}", className='incidencia-title'),
                    html.Span(st + extra, className=f"incidencia-badge {badge_class}")
                ]),
                html.P(inc.get('descripcion', '-'), className='incidencia-desc'),
                html.Div(f"Estado: {inc.get('verificacion','')}", className='incidencia-meta')
            ])
        ]
    )

def _build_recommendations_layout(cliente_id):
    """Genera el layout de las recomendaciones de autodiagnóstico (Screen 2)."""
    
    style_content = {'padding': '20px', 'textAlign': 'left', 'backgroundColor': '#f9fafb'}
    style_list_item = {'marginBottom': '8px', 'color': '#374151', 'fontSize': '0.9rem'}
    style_warning = {
        'marginTop': '15px',
        'padding': '10px',
        'backgroundColor': '#fef3c7', 
        'color': '#92400E',
        'borderRadius': '6px',
        'borderLeft': '4px solid #F59E0B', 
        'fontWeight': '500',
        'fontSize': '0.85rem'
    }

    recommendations_content = html.Div(style=style_content, children=[
        html.H4('Recomendaciones de Autodiagnóstico', style={'color': 'var(--primary)', 'fontSize': '1.1rem', 'marginBottom': '15px'}),

        #Causas consumo anomalo
        html.Div(className='mb-4', children=[
            html.P(html.B('Si ha detectado un consumo de agua superior al habitual, puede ser por diferentes causas:'), style={'marginBottom': '10px', 'color': '#374151', 'fontWeight': 'bold'}),
            html.Ul(style={'listStyleType': 'disc', 'marginLeft': '20px'}, children=[
                html.Li('Cambio de hábitos de consumo, más personas en la vivienda, cambio de algún electrodoméstico, instalación de un aparato descalcificador de agua...', style=style_list_item),
                html.Li('Un escape de agua no detectado.', style=style_list_item),
                html.Li('Un uso fraudulento de su contador.', style=style_list_item),
            ])
        ]),

        #Comprobar si hay una fuga
        html.Div(children=[
            html.H5(html.B('Pasos para comprobar una fuga:'), style={'marginBottom': '10px', 'color': 'var(--primary)', 'fontSize': '1rem'}),
            html.Ol(style={'listStyleType': 'decimal', 'marginLeft': '20px'}, children=[
                html.Li('Localice su contador en la batería de contadores de su edificio, y asegúrese de que la llave de paso de su casa y las llaves del contador están abiertas.', style=style_list_item),
                html.Li('Asegúrese que los grifos de su casa están cerrados y que todos los electrodomésticos que funcionan con agua no están en funcionamiento.', style=style_list_item),
                html.Li('Tome la lectura actual del contador (o hágale una foto).', style=style_list_item),
                html.Li('**4 horas después**, vuelva a tomar la lectura. Si ha cambiado, seguramente tiene una fuga.', style=style_list_item),
            ]),
            html.Div(style=style_warning, children=[
                html.B('Aviso:'), ' Se recomienda realizar esta prueba por la noche, cuando el consumo es mínimo y la prueba es más fiable.'
            ])
        ])
    ])
    
    back_button = dcc.Link("Volver", href=f"/sim-movil/{cliente_id}", className='btn-block', style={'textDecoration': 'none', 'display': 'block', 'textAlign': 'center', 'marginTop':'20px', 'padding':'10px 20px'})
    
    return html.Div(className='card', children=[recommendations_content, back_button])

def build_verificacion_layout(token):
    """Construye la página de encuesta pública."""
    return html.Div(className='verification-page-container', children=[
        html.Div(className='verification-card', children=[
            _build_survey_layout(token)
        ])
    ])

def build_simulador_movil_layout(cliente_id, pathname):
    """
    Simulador móvil: Ruteo de pantallas (Notificaciones, Encuesta, Gracias, Recomendaciones).
    """
    contenido_pantalla = None
    titulo = "Notificaciones"

    if 'verificar' in pathname:
        token = pathname.split('/')[-1]
        contenido_pantalla = _build_survey_layout(token)
        titulo = "Encuesta"
    elif 'confirmacion' in pathname:
        contenido_pantalla = _build_confirmation_layout(cliente_id)
        titulo = "Éxito"
    elif 'recomendaciones' in pathname:
        contenido_pantalla = _build_recommendations_layout(cliente_id)
        titulo = "Recomendaciones"
    else:
        contenido_pantalla = html.Div(id='div-notificaciones-movil', children=[
            html.P("Sin notificaciones nuevas", className='small-muted')
        ])

    return html.Div(className='mobile-frame', children=[
        dcc.Store(id='store-cliente-id', data=cliente_id),
        #dcc.Interval(id='intervalo-notificaciones-movil', interval=3000, n_intervals=0),
        html.Div(className='mobile-screen', children=[
            html.Div(className='mobile-notch'),
            html.Div(className='mobile-header', children=[html.H5(titulo, className='mobile-header-title')]),
            html.Div(className='mobile-notifs', children=[contenido_pantalla]),
            html.Div(className='mobile-home-bar', style={'height':'12px','margin':'8px auto','width':'120px','borderRadius':'8px','background':'#000','opacity':0.15})
        ])
    ])

def _build_survey_layout(token):
    preguntas = [
        "1. ¿Ha notado un sonido de agua corriendo (siseo)?",
        "2. ¿Algún grifo o cisterna pierde agua?",
        "3. ¿El contador se mueve con todo cerrado?",
        "4. ¿Ha detectado humedades recientes?",
        "5. ¿Ha habido obras recientes?",
        "6. ¿Ha realizado usted, o en su hogar, alguna actividad que justifique un alto consumo en las últimas 48 horas?"
        "7. ¿El proceso de notificación de Aigües de Barcelona ha sido claro y satisfactorio?"
    ]
    opciones = [
        {'label': 'Sí', 'value': 'SI'},
        {'label': 'No', 'value': 'NO'},
        {'label': 'No lo sé', 'value': 'NO_SE'},
    ]

    return html.Div(children=[
        html.H5("Verificación de Incidencia", className='survey-title'),
        html.P("Responda para ayudar a nuestro diagnóstico.", className='survey-subtitle'),
        dcc.Store(id='store-token', data=token),

        *[
            html.Div(className='survey-question', children=[
                html.Label(preg, className='survey-question-label'),
                dbc.RadioItems(id={'type': 'survey-q', 'index': i+1}, options=opciones, value=None, className='survey-radio')
            ]) for i, preg in enumerate(preguntas)
        ],

        html.Button('Confirmar y Enviar', id='btn-submit-survey', n_clicks=0, className='btn-block btn-margin-top'),
        html.Div(id='survey-result', className='survey-result-container')
    ])

def _build_confirmation_layout(cliente_id):
    """
    Genera el layout de la pantalla de agradecimiento (Screen 1), 
    con el botón 'Siguiente' para ir a las recomendaciones.
    """
    link_destino = f"/sim-movil/{cliente_id}/recomendaciones"

    return html.Div(className='card', children=[
        html.Div(style={'textAlign': 'center', 'padding': '40px'}, children=[
            html.Div('✅', style={'fontSize': '50px', 'marginBottom': '20px'}),
            html.H3('Recibido', style={'color': 'var(--primary)'}),
            html.P('Gracias. Hemos registrado sus respuestas.', style={'color': 'var(--muted)'}),
            dcc.Link("Siguiente", href=link_destino, className='btn-block btn-primary', style={'textDecoration': 'none', 'display': 'inline-block', 'marginTop':'20px', 'width':'auto','padding':'10px 20px'})
        ])
    ])

##def _build_confirmation_layout(cliente_id):
    #return html.Div(className='card', children=[
        #html.Div(style={'textAlign': 'center', 'padding': '40px'}, children=[
            #html.Div('✅', style={'fontSize': '50px', 'marginBottom': '20px'}),
            #html.H3('Recibido', style={'color': 'var(--primary)'}),
            #html.P('Gracias. Hemos registrado sus respuestas.', style={'color': 'var(--muted)'}),
            #dcc.Link("Volver", href=f"/sim-movil/{cliente_id}", className='btn-block', style={'textDecoration': 'none', 'display': 'inline-block', 'marginTop':'20px', 'width':'auto','padding':'10px 20px'})
        #])
    #])  


# ------------------------------------------------------------
# LAYOUTS principales
# ------------------------------------------------------------
def build_login_layout():
    return html.Div(className="login-wrapper", children=[
        html.Div(className="login-card container-centered", children=[
            html.Div(className='login-brand', children=[
                html.Img(src=app.get_asset_url('logo_1.png'), className='logo-login'),
                html.Div(children=[
                    html.P("Portal de Gestión de Incidencias", className='app-subtitle'),
                    html.P("Aigües de Barcelona", className='small-muted', style={'marginTop': '4px', 'fontSize': '12px'})
                ])
            ]),

            html.Div(className="form-row", children=[
                html.Label('Usuario Corporativo', className='form-label'),
                dcc.Input(id='input-usuario', type='text', placeholder='empresa@gesai.com', className='form-input'),

                html.Label('Contraseña', className='form-label', style={'marginTop': '12px'}),
                dcc.Input(id='input-password', type='password', placeholder='••••••••', className='form-input'),

                html.Div(id='login-error', className='small-muted', style={'minHeight': '22px', 'marginTop': '8px'}),
                html.Button("Acceder al Sistema", id='btn-login', className='btn-primary'),
                html.Div("Credenciales Demo: empresa@gesai.com / 1234", className='login-footer-note')
            ])
        ])
    ])


def build_empresa_layout(session_data):
    nombre_usuario = session_data.get('nombre', 'Admin')

    header = html.Div(className='header container-centered', children=[
        html.Div(className='header-left', children=[
            html.Img(src=app.get_asset_url('logo_2.png'), className='logo-dashboard'),
            html.Div(children=[
                html.H3('Panel de Control', className='header-title'),
                html.Div('Visión general • GeSAI', className='header-sub')
            ])
        ]),

        html.Div(className='header-actions', children=[
            # Toggle dark mode as a button (más atractivo)
            html.Button('Modo Noche', id='dark-mode-toggle', n_clicks=0, className='btn-darkmode'),

            html.Div(className='user-pill', style={'backgroundColor': 'transparent', 'border': '1px solid currentColor'}, children=[html.Span('👤'), html.Span(nombre_usuario)]),
            html.Button('Salir', id={'type': 'btn-logout', 'index': 'empresa'}, className='btn-logout')
        ])
    ])

    body = html.Div(className='page-grid container-centered', children=[
        html.Div(className='left-column', children=[
            html.Div(className='card animated-card', children=[
                html.Div(className='kpi-grid', id='stats-container')
            ]),
            html.Div(className='card animated-card', children=[
                html.Div(className='filter-row', children=[
                    html.Span('Filtrar Estado:', className='filter-label'),
                    html.Button('Todas', id={'type': 'filtro-btn', 'index': 'todas'}, className='filter active', n_clicks=0),
                    html.Button('Grave', id={'type': 'filtro-btn', 'index': 'Grave'}, className='filter', n_clicks=0),
                    html.Button('Moderada', id={'type': 'filtro-btn', 'index': 'Moderada'}, className='filter', n_clicks=0),
                    html.Button('Carta', id={'type': 'filtro-btn', 'index': 'CARTA'}, className='filter', n_clicks=0)
                ])
            ])
        ]),

        html.Div(className='right-column', children=[
            html.Div(id='modal-detalles'),
            html.Div(className='card animated-card', children=[html.Div(id='incidencias-container')]),
            html.Div(id='dummy-download-output')  # placeholder for clientside outputs
        ])
    ])

    return html.Div([dcc.Interval(id='intervalo-refresco', interval=2000, n_intervals=0), header, body])


# ------------------------------------------------------------
# ROOT layout
# ------------------------------------------------------------
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session', data={'logged_in': False}),
    dcc.Store(id='store-filtro-activo', data='todas'),
    dcc.Store(id='store-token', data=None),
    dcc.Store(id='store-cliente-id', data=None),
    html.Div(id='page-content')
])


# ------------------------------------------------------------
# CALLBACKS
# ------------------------------------------------------------
@callback(
    [Output('session-store', 'data'),
     Output('login-error', 'children'),
     Output('url', 'pathname')],
    Input('btn-login', 'n_clicks'),
    [State('input-usuario', 'value'), State('input-password', 'value')],
    prevent_initial_call=True
)
def login(n, u, p):
    res = verificar_credenciales(u, p)
    if res.get('success'):
        return {'logged_in': True, 'rol': 'Empresa', 'nombre': res.get('nombre')}, None, '/dashboard'
    return no_update, html.Div(res.get('message')), no_update


@callback(
    [Output('session-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input({'type': 'btn-logout', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def logout(n):
    # si no hay clicks -> no_update
    if not any(n):
        return no_update, no_update
    return {'logged_in': False}, '/'


@callback(Output('page-content', 'children'), Input('url', 'pathname'), State('session-store', 'data'))
def display_page(pathname, session_data):
    pathname = pathname or '/'
    parts = pathname.strip('/').split('/')
    
    # 1. RUTAS PÚBLICAS (Móvil y Verificación) - Tienen prioridad
    if len(parts) >= 2 and parts[0] == 'sim-movil':
        # Aceptamos ID numérico o texto (póliza)
        cliente_id = parts[1]
        return build_simulador_movil_layout(cliente_id, pathname)
        
    if len(parts) == 2 and parts[0] == 'verificar':
        return build_verificacion_layout(parts[1]) # Token

    # 2. RUTAS PRIVADAS (Empresa) - Requieren Login
    if session_data and session_data.get('logged_in'):
        if pathname in ['/', '/dashboard']:
            return build_empresa_layout(session_data)
        # Si intenta ir al login estando logueado, a casa
        if pathname == '/login':
            return dcc.Location(pathname='/', id='redirect-home')
            
    # 3. DEFAULT (Login)
    return build_login_layout()


@callback(
    [Output('stats-container', 'children'),
     Output('incidencias-container', 'children')],
    [Input('intervalo-refresco', 'n_intervals'),
     Input('store-filtro-activo', 'data')]
)
def refresh_dashboard(n, filtro):
    filtro = (filtro or 'todas').upper()
    todas = get_lista_incidencias_activas('todas') or []

    def match(i):
        estado = str(i.get('estado', '')).upper()
        ver = str(i.get('verificacion', '')).upper()
        if filtro == 'TODAS':
            return True
        if filtro == 'CARTA':
            return 'CARTA' in ver
        return filtro in estado

    incidencias = [i for i in todas if match(i)]

    total = len(todas)
    graves = sum('GRAVE' in str(i.get('estado', '')).upper() for i in todas)
    moderadas = sum('MODERADA' in str(i.get('estado', '')).upper() for i in todas)
    cartas = sum('CARTA' in str(i.get('verificacion', '')).upper() for i in todas)

    stats = html.Div(className='kpi-grid', children=[
        kpi_card('Incidencias Activas', total, '📊'),
        kpi_card('Fugas Graves', graves, '🚨'),
        kpi_card('Fugas Moderadas', moderadas, '⚠️'),
        kpi_card('Cartas por Enviar', cartas, '📮')
    ])

    if not incidencias:
        cards = html.Div("No hay incidencias recientes.", className='list-empty')
    else:
        cards = html.Div([incidencia_card(inc) for inc in incidencias])

    return stats, cards


@callback(
    Output('store-filtro-activo', 'data'),
    Output({'type': 'filtro-btn', 'index': ALL}, 'className'),
    Input({'type': 'filtro-btn', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_filter(n):
    # si no hay botones en el layout → no ejecutar
    if n is None or len(n) == 0:
        raise PreventUpdate

    # opciones fijas (orden fijo)
    options = ['todas', 'Grave', 'Moderada', 'CARTA']
    triggered = ctx.triggered_id

    if not triggered:
        raise PreventUpdate

    fid = triggered.get('index') if isinstance(triggered, dict) else None
    store_value = fid.lower() if isinstance(fid, str) else PreventUpdate
    cls = ['filter active' if o == fid else 'filter' for o in options]

    return store_value, cls


@callback(
    Output('modal-detalles', 'children'),
    [Input({'type': 'incidencia-card', 'index': ALL}, 'n_clicks'),
     Input({'type': 'btn-close-details', 'index': ALL}, 'n_clicks'),
     Input({'type': 'btn-download-report', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)


def handle_details(n_card, n_close, n_down):
    tid = ctx.triggered_id
    if not tid:
        return no_update

    # CERRAR
    if isinstance(tid, dict) and tid.get('type') == 'btn-close-details':
        return None

    # ⚠️ IMPORTANTE:
    # Eliminamos completamente la lógica antigua que generaba informes desde el callback.
    # Ya no existe "btn-download-report". Todo ahora es descarga por ruta Flask.

    # ABRIR DETALLES
    if isinstance(tid, dict) and tid.get('type') == 'incidencia-card':
        if not any(n_card):
            return no_update

        data = get_detalles_incidencia(tid.get('index'))
        if not data.get('success'):
            return no_update

        inc, cli = data['datos_incidencia'], data['datos_cliente']

        # --- BOTONES DINÁMICOS ---
        botones = []

        tiene_contacto = cli.get("email") or cli.get("telefono")

        if tiene_contacto:
            botones.append(
                html.A(
                    "Descargar Informe Técnico",
                    href=f"/download/informe/{inc['id']}",
                    target="_blank",
                    rel="noopener noreferrer",
                    className="btn-block",
                    style={"textDecoration": "none", "marginTop": "12px"}
                )
        )

        else:
        # Cliente SIN contacto → sólo carta postal
            botones.append(
                html.A(
                    "Generar Carta Postal",
                    href=f"/download/carta/{inc['id']}",
                    target="_blank",
                    rel="noopener noreferrer",
                    className="btn-block",
                    style={"textDecoration": "none", "marginTop": "12px"}
                )
        )

        # --- RETURN PANEL DETALLES ---
        return html.Div(
            className='details-panel animated-slide-up',
            children=[
                html.Button(
                    '✕',
                    id={'type': 'btn-close-details', 'index': inc['id']},
                    className='btn-close'
                ),
                html.H3(f"Incidencia #{inc['id']}", className='details-title'),
                dbc.Row([
                    dbc.Col([
                        html.H5("Detalles"),
                        html.P(f"Estado: {inc.get('estado','')}"),
                        html.P(f"Probabilidad: {inc.get('prob_hoy', 'N/A')}")
                    ], md=6),
                    dbc.Col([
                        html.H5("Cliente"),
                        html.P(cli.get('nombre','-')),
                        html.P(cli.get('direccion','-'))
                    ], md=6),
                ]),
                *botones  # ← aquí añadimos todos los botones dinámicos
            ]
        )

    return no_update


@callback(
    Output('div-notificaciones-movil', 'children'),
    Input('intervalo-notificaciones-movil', 'n_intervals'),
    State('store-cliente-id', 'data'),
    State('url', 'pathname')
)
def mobile_poll(n, cid, path):
    if not path or not cid:
        return no_update
    # Excluir 'verificar', 'confirmacion' Y 'recomendaciones'
    if 'verificar' in path or 'confirmacion' in path or 'recomendaciones' in path:
        return no_update
    
    notifs = get_notificaciones_pendientes_cliente(cid)
    
    # 1. Si no hay notificaciones, devolvemos no_update. 
    # La inicialización del 'Sin notificaciones nuevas' se maneja en build_simulador_movil_layout.
    if not notifs:
        # Si ya estábamos mostrando 'Sin notificaciones', no hacemos nada para evitar el callback loop.
        return no_update 
    
    cards = []
    for notif in notifs:
        link = f"/sim-movil/{cid}/verificar/{notif['link'].split('/')[-1]}"
        cards.append(html.Div(className='mobile-notif', children=[
            html.Div(className='app-title', children=[html.Span('💧'), html.Span('GeSAI App')]),
            html.Div(className='title', children='Alerta de Fuga'),
            html.Div(className='body', children=notif['mensaje']),
            dcc.Link('Verificar', href=link, className='mobile-btn')
        ]))
        marcar_notificacion_leida(notif['notificacion_id'])
    
    return cards


@callback(
    [Output('survey-result', 'children'), Output('url', 'pathname', allow_duplicate=True)],
    Input('btn-submit-survey', 'n_clicks'),
    [State('store-token', 'data'), State({'type': 'survey-q', 'index': ALL}, 'value'), State('url', 'pathname')],
    prevent_initial_call=True
)
def submit_survey(n, token, resps, path):
    if not token or any(r is None for r in resps):
        return html.P("Complete todo", className='survey-result-error'), no_update
    validar_token_y_registrar(token, {})
    if path:
        parts = path.split('/')
        if len(parts) >= 3:
            return no_update, f"/{parts[1]}/{parts[2]}/confirmacion"
    return no_update, no_update


# CLIENTSIDE: toggle dark mode (más rápido, sin roundtrip)
app.clientside_callback(
    """
    function(n_clicks) {
        try {
            const body = document.body;
            if(!body) return '';
            // toggle
            if(n_clicks % 2 === 1) {
                body.classList.add('dark-mode');
            } else {
                body.classList.remove('dark-mode');
            }
        } catch(e) { console.warn(e); }
        return '';
    }
    """,
    Output('dummy-download-output', 'children'),
    Input('dark-mode-toggle', 'n_clicks')
)

# -------- SERVIR PDF DE INFORME TÉCNICO --------
@app.server.route('/download/informe/<int:id>')
def download_informe(id):
    # Obtenim dades incidència
    data = get_detalles_incidencia(id)
    if not data.get("success"):
        return "No existe", 404

    inc = data["datos_incidencia"]
    cli = data["datos_cliente"]

    # Crear histórico dummy (como hacías en el callback)
    hist = pd.DataFrame({
        "FECHA_HORA": pd.date_range(start="2024-01-01", periods=24, freq="h"),
        "CONSUMO_REAL": [10]*20 + [80,90,100,110]
    })

    # Generar PDF
    filename = generar_informe_tecnico_pdf(id, cli, inc, hist)

    # Enviar fichero al navegador
    return send_file(filename, as_attachment=False)

@app.server.route('/download/carta/<int:id>')
def download_carta(id):
    data = get_detalles_incidencia(id)
    if not data.get("success"):
        return "No existe", 404

    cli = data["datos_cliente"]
    filename = generar_carta_postal_pdf(id, cli)
    return send_file(filename, as_attachment=False)



# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
