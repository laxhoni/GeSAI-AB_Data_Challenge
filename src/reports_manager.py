

# src/reports_manager.py

from fpdf import FPDF
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import time
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CARTAS = os.path.join(BASE_DIR, "generated_reports", "regular_mails")
os.makedirs(RUTA_CARTAS, exist_ok=True)

# --- PALETA DE COLORES CORPORATIVA (Elegante) ---
COLOR_PRIMARIO = (0, 89, 157)       # Azul Aigües Profundo
COLOR_SECUNDARIO = (100, 100, 100)  # Gris Medio
COLOR_TEXTO = (40, 40, 40)          # Gris Casi Negro
COLOR_FONDO_HEADER = (245, 249, 255) # Azul muy muy pálido (Casi blanco)
COLOR_ALERTA = (204, 51, 0)         # Rojo Ladrillo (Menos agresivo)
COLOR_LINEA = (220, 220, 220)       # Gris claro para separadores

# Configuración de Gráficas (Estilo Minimalista)
sns.set_theme(style="ticks", rc={"axes.grid": True, "grid.linestyle": ":", "grid.color": "#e0e0e0"})
plt.rcParams.update({'font.size': 8, 'font.family': 'sans-serif', 'text.color': '#444444', 'axes.labelcolor': '#666666'})

class PDF_GesAI(FPDF):
    def __init__(self):
        super().__init__()
        self.logo_path = self._find_logo()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20) # Márgenes generosos (2cm) para aspecto profesional

    def _find_logo(self):
        """Busca el logo 'logo_2.png'."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        paths = [
            os.path.join(os.path.dirname(base_dir), 'assets', 'logo_2.png'),
            os.path.join(base_dir, 'assets', 'logo_2.png')
        ]
        for p in paths:
            if os.path.exists(p): return p
        return None

    def header(self):
        # 1. Fondo sutil cabecera
        self.set_fill_color(*COLOR_FONDO_HEADER)
        self.rect(0, 0, 210, 20, 'F')
        
        # 2. Logo (Alineado a la izquierda con margen)
        if self.logo_path:
            self.image(self.logo_path, 18, -12, 45) # Logo más contenido
        
        # 3. Separador Vertical
        #self.set_draw_color(200, 200, 200)
        #self.set_line_width(0.2)
        #self.line(70, 12, 70, 28)

        # 4. Título Sistema (A la derecha del logo)
        #self.set_xy(75, 14)
        #self.set_font('Helvetica', 'B', 12)
        #self.set_text_color(*COLOR_PRIMARIO)
        #self.cell(0, 5, 'GeSAI System', 0, 1, 'L')
        
        self.set_xy(140, 12)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*COLOR_SECUNDARIO)
        self.cell(0, 5, "Gestió Segura i Automatitzada d'Incidències", 0, 1, 'L')
        
        # 5. Línea base cabecera
        #self.set_draw_color(*COLOR_PRIMARIO)
        #self.set_line_width(0.5)
        #self.line(0, 40, 210, 40)
        self.ln(10) # Espacio limpio después del header

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 4, "Aigües de Barcelona | Document Confidencial generat per GeSAI", 0, 1, 'C')
        self.cell(0, 4, f'Pàgina {self.page_no()}', 0, 0, 'R')

    def section_title(self, title):
        """Títulos de sección limpios y modernos."""
        self.ln(5)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*COLOR_PRIMARIO)
        self.cell(0, 8, title.upper(), 0, 1, 'L')
        # Línea fina debajo del título
        self.set_draw_color(*COLOR_LINEA)
        self.set_line_width(0.2)
        self.line(self.get_x(), self.get_y(), 190, self.get_y())
        self.ln(4)

    def key_value_row(self, key, value, bold_value=False):
        """Fila de datos alineada."""
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(45, 6, key, 0, 0) # Ancho fijo para la etiqueta
        
        self.set_font('Helvetica', 'B' if bold_value else '', 9)
        self.set_text_color(*COLOR_TEXTO)
        # Truncar si es muy largo para no romper diseño
        val_str = str(value) if pd.notna(value) else "-"
        self.cell(0, 6, val_str, 0, 1)

# --- GRÁFICA PROFESIONAL ---
def _generar_grafica_consumo_compacta(df_historico, filename):
    # Relación de aspecto panorámica (muy ancha, poco alta)
    fig, ax = plt.subplots(figsize=(8, 2.2)) 
    
    fechas = pd.to_datetime(df_historico['FECHA_HORA'])
    valores = df_historico['CONSUMO_REAL']
    
    # Línea suave
    ax.plot(fechas, valores, color='#00599D', linewidth=1.2, label='Consum (L)')
    ax.fill_between(fechas, valores, color='#00599D', alpha=0.08)
    
    # Estilo limpio
    ax.set_ylabel('Litres', fontsize=7)
    ax.tick_params(axis='both', labelsize=6, color='#888888')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    
    # Quitar bordes (Spines)
    sns.despine(left=True, bottom=False)
    ax.grid(axis='x', visible=False) # Solo grid horizontal
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()

# ==============================================================================
# 1. INFORME TÉCNICO (ESTILO EJECUTIVO)
# ==============================================================================
def generar_informe_tecnico_pdf(incidencia_id, datos_cliente, datos_incidencia, historico_df=None):
    pdf = PDF_GesAI()
    pdf.add_page()
    fecha_hoy = time.strftime("%d/%m/%Y")
    
    # --- Bloque de Título del Documento ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(120, 8, "INFORME TÈCNIC D'INCIDÈNCIA", 0, 0)
    
    # Metadatos a la derecha
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"REF: #{incidencia_id} | DATA: {fecha_hoy}", 0, 1, 'R')
    #pdf.ln(5)

    # --- 1. INFORMACIÓN DEL CLIENTE ---
    pdf.section_title("1. Dades del Punt de Subministrament")
    pdf.key_value_row("Titular del Contracte:", datos_cliente.get('nombre', 'N/A'), True)
    pdf.key_value_row("ID Pòlissa:", datos_cliente.get('cliente_id', 'N/A'))
    pdf.key_value_row("Adreça:", datos_cliente.get('direccion', 'N/A'))
    pdf.key_value_row("Contacte:", f"{datos_cliente.get('telefono', '-')}  /  {datos_cliente.get('email', '-')}")

    # --- 2. DIAGNÓSTICO INTELIGENTE ---
    pdf.section_title("2. Diagnòstic del Sistema (IA)")
    
    # Panel de Estado (Caja coloreada sutil)
    estado = datos_incidencia.get('estado', 'PENDENT').upper()
    
    # Color de fondo según estado
    if "GRAVE" in estado: 
        bg_color = (255, 235, 235) # Rojo muy claro
        txt_color = COLOR_ALERTA
    elif "MODERADA" in estado:
        bg_color = (255, 248, 225) # Naranja claro
        txt_color = (180, 100, 0)
    else:
        bg_color = (235, 255, 235) # Verde claro
        txt_color = (0, 120, 0)

    pdf.set_fill_color(*bg_color)
    pdf.rect(20, pdf.get_y(), 170, 12, 'F')
    
    pdf.set_xy(25, pdf.get_y() + 3)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(40, 6, "CLASSIFICACIÓ:", 0, 0)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(*txt_color)
    pdf.cell(0, 6, estado, 0, 1)
    
    pdf.ln(4)
    
    # Detalles técnicos
    pdf.key_value_row("Probabilitat de Fuga:", f"{datos_incidencia.get('prob_hoy', 0):.2%} (Model Predictiu)")
    pdf.key_value_row("Descripció Tècnica:", datos_incidencia.get('descripcion', '-'))

# --- 3. ANÁLISIS DE CONSUMO Y PÉRDIDAS (ACTUALIZADO) ---
    if historico_df is not None and not historico_df.empty:
        pdf.section_title("3. Anàlisi de Facturació i Pèrdues")
        
        # A) CÁLCULOS AVANZADOS
        consumo_total = historico_df['CONSUMO_REAL'].sum()
        
        # Heurística: Consideramos "Consumo Base" a la mediana.
        # Todo lo que supere la base x 1.1 (10% margen) es "exceso" atribuible a la fuga/anomalía.
        base_h = historico_df['CONSUMO_REAL'].median()
        df_exceso = historico_df[historico_df['CONSUMO_REAL'] > (base_h * 1.1)]
        
        litros_perdidos = 0
        coste_estimado = 0
        horas_fuga = 0
        
        # Calculamos pérdidas si el estado es Grave o Moderada
        estado_norm = datos_incidencia.get('estado','').upper()
        if not df_exceso.empty and (("GRAVE" in estado_norm) or ("MODERADA" in estado_norm)):
            litros_perdidos = (df_exceso['CONSUMO_REAL'] - base_h).sum()
            horas_fuga = len(df_exceso)
            # Precio aprox agua (Tramo alto + Canon): ~2.85 EUR/m3
            coste_estimado = (litros_perdidos / 1000) * 2.85
            
        fecha_ini = historico_df['FECHA_HORA'].min().strftime("%d/%m")
        fecha_fin = historico_df['FECHA_HORA'].max().strftime("%d/%m")
        
        # B) DIBUJAR TABLA DE KPIs
        y_start = pdf.get_y()
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(15, y_start, 180, 18, 'F') # Fondo gris
        
        pdf.set_y(y_start + 4)
        
        # Columna 1: Total Periodo
        pdf.set_x(15)
        pdf.set_font('Helvetica', 'B', 8); pdf.set_text_color(100, 100, 100)
        pdf.cell(45, 4, f"CONSUM ({fecha_ini}-{fecha_fin})", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11); pdf.set_text_color(0, 0, 0)
        pdf.cell(45, 5, f"{consumo_total/1000:.2f} m3", 0, 0, 'C')
        
        # Columna 2: Fuga Estimada (Litros)
        pdf.set_xy(60, y_start + 4)
        pdf.set_font('Helvetica', 'B', 8); pdf.set_text_color(100, 100, 100)
        pdf.cell(45, 4, "FUITA ESTIMADA", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11)
        if litros_perdidos > 50:
            pdf.set_text_color(*COLOR_ALERTA)
            pdf.cell(45, 5, f"{litros_perdidos:.0f} L", 0, 0, 'C')
        else:
            pdf.set_text_color(0, 150, 0) # Verde
            pdf.cell(45, 5, "0 L", 0, 0, 'C')

        # Columna 3: Impacto Económico (EUR)
        pdf.set_xy(105, y_start + 4)
        pdf.set_font('Helvetica', 'B', 8); pdf.set_text_color(100, 100, 100)
        pdf.cell(45, 4, "IMPACTE ECONÒMIC", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11)
        if coste_estimado > 0.1:
            pdf.set_text_color(*COLOR_ALERTA)
            # USAMOS 'EUR' PARA EVITAR ERROR DE ENCODING
            pdf.cell(45, 5, f"+{coste_estimado:.2f} EUR", 0, 0, 'C')
        else:
            pdf.set_text_color(0, 0, 0)
            pdf.cell(45, 5, "-", 0, 0, 'C')
            
        # Columna 4: Duración (Horas)
        pdf.set_xy(150, y_start + 4)
        pdf.set_font('Helvetica', 'B', 8); pdf.set_text_color(100, 100, 100)
        pdf.cell(45, 4, "DURADA DETECTADA", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11); pdf.set_text_color(0, 0, 0)
        if horas_fuga > 0:
            dias = horas_fuga // 24
            horas_rest = horas_fuga % 24
            texto_dur = f"{dias}d {horas_rest}h" if dias > 0 else f"{horas_rest}h"
            pdf.cell(45, 5, texto_dur, 0, 0, 'C')
        else:
            pdf.cell(45, 5, "0h", 0, 0, 'C')
        
        pdf.ln(7) # Salir de la caja

        # C) Generar Gráfica
        chart_path = f"temp_chart_{incidencia_id}.png"
        try:
            _generar_grafica_consumo_compacta(historico_df, chart_path)
            # Insertar imagen centrada
            pdf.image(chart_path, x=15, w=180)
            pdf.ln(1)
            # Pie de foto
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, "Fig 1. Evolució horària del consum (30 dies). La zona ombrejada indica el consum acumulat.", 0, 1, 'C')
            os.remove(chart_path)
        except Exception as e:
            pdf.cell(0, 5, f"Error generant gràfica: {e}", 0, 1)
            
    # --- 4. Doble verificación del cliente ---
    encuesta_raw = datos_incidencia.get('encuesta_resultado')
    
    if encuesta_raw:
        try:
            # 1. Parsear el JSON guardado en BBDD
            respuestas = json.loads(encuesta_raw)
            
            # Si es una lista o dict, aseguramos formato.
            # Asumiremos que desde app.py enviamos una lista de dicts: [{'pregunta': '...', 'respuesta': 'SI'}]
            # O un dict simple. Adaptamos la visualización:
            
            pdf.ln(4) # Espacio antes de la nueva sección
            pdf.section_title("4. Doble verificació del client (App Mòbil)")
            
            # Fondo gris suave para las respuestas
            pdf.set_fill_color(250, 250, 250)
            
            # Encabezados de tabla
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(140, 6, "PREGUNTA REALITZADA", 0, 0, 'L', True)
            pdf.cell(30, 6, "RESPOSTA", 0, 1, 'C', True)
            
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(40, 40, 40)
            
            # Iterar respuestas. 
            # NOTA: Ajustar según cómo enviemos los datos desde app.py. 
            # Aquí asumo que 'respuestas' es una lista de objetos o dict con claves numericas.
            # Para mayor robustez, vamos a asumir que es una lista de textos.
            
            if isinstance(respuestas, list):
                for item in respuestas:
                    preg = item.get('pregunta', '-')[:75] + "..." if len(item.get('pregunta','')) > 75 else item.get('pregunta', '-')
                    resp = str(item.get('respuesta', '-')).upper()
                    
                    # Colorear respuesta si es SI (Alerta)
                    pdf.set_text_color(40, 40, 40)
                    if resp in ['SI', 'SÍ']:
                        pdf.set_text_color(*COLOR_ALERTA) # Rojo para los SI
                        pdf.set_font('Helvetica', 'B', 8)
                    else:
                        pdf.set_font('Helvetica', '', 8)

                    pdf.cell(140, 6, f"-> {preg}", 0, 0, 'L')
                    pdf.cell(30, 6, resp, 0, 1, 'C')
                    
            pdf.ln(5)
            
        except Exception as e:
            print(f"Error parseando encuesta para PDF: {e}")         
            
    # Guardar
    output_dir = '../generated_reports/technical_reports/'
    os.makedirs(output_dir, exist_ok=True)
    cliente_id = datos_cliente.get('cliente_id', 'Unknown')
    filename = os.path.join(output_dir, f"Informe_Tecnic_{cliente_id}_{incidencia_id}.pdf")
    pdf.output(filename)
    print(f"✅ Informe Profesional generado: {filename}")
    return filename

# ==============================================================================
# 2. CARTA POSTAL CLIENTE (ESTILO FORMAL)
def generar_carta_postal_pdf(incidencia_id, cliente):
    import os
    import time

    # --- 1. Preparació de rutes ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR = os.path.join(BASE_DIR, "generated_reports", "regular_mails")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cliente_id = cliente.get("cliente_id", "Unknown")
    filename = f"Carta_Incidencia_{cliente_id}_{incidencia_id}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # --- 2. Crear PDF amb la classe ORIGINAL (amb logo i header) ---
    pdf = PDF_GesAI()
    pdf.add_page()   # <-- aquí automàticament es pinta header + logo
    fecha = time.strftime("%d/%m/%Y")

    # -------------------------------
    #   BLOQUE DIRECCIÓ (FINESTRA)
    # -------------------------------
    pdf.set_xy(110, 50)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(0, 0, 0)

    nombre = cliente.get("nombre", "Estimado Cliente")
    direccion = cliente.get("direccion", "Adreça Desconeguda")

    pdf.multi_cell(85, 5, f"{nombre}\n{direccion}\n", align="L")
    pdf.ln(30)

    # -------------------------------
    #     ASSUMPTE (ROJO ALERTA)
    # -------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_ALERTA)
    pdf.cell(0, 8, f"AVÍS IMPORTANT: ANOMALIA DE CONSUM (REF. #{incidencia_id})", ln=1)
    pdf.ln(5)

    # -------------------------------
    #      COS DE LA CARTA
    # -------------------------------
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)

    cuerpo = (
        f"Benvolgut/da client/a,\n\n"
        f"Ens posem en contacte amb vostè per informar-lo que els nostres sistemes de monitoratge intel·ligent (GeSAI) "
        f"han detectat un patró de consum d'aigua atípic al seu punt de subministrament en data {fecha}.\n\n"
        f"Li enviem aquesta notificació per correu postal ja que no disposem de les seves dades de contacte digital "
        f"(telèfon mòbil o correu electrònic) actualitzades a la nostra base de dades.\n\n"
        f"Li recomanem que revisi la seva instal·lació interior el més aviat possible per descartar possibles fuites "
        f"i evitar càrrecs addicionals a la seva factura."
    )
    pdf.multi_cell(0, 5, cuerpo)
    pdf.ln(10)

    # -------------------------------
    #   CALL TO ACTION (RECUADRO)
    # -------------------------------
    pdf.set_draw_color(*COLOR_PRIMARIO)
    pdf.set_fill_color(250, 252, 255)
    pdf.set_line_width(0.3)

    y_start = pdf.get_y()
    pdf.rect(15, y_start, 180, 20, style="DF")

    pdf.set_xy(20, y_start + 5)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(0, 5, "ACTUALITZI LES SEVES DADES PER REBRE AVISOS AL MÒBIL:", ln=1)

    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.write(5, "Accedeixi a l'Àrea de Clients: ")

    pdf.set_font("Helvetica", "U", 9)
    pdf.set_text_color(0, 0, 255)
    pdf.write(
        5,
        "https://www.aiguesdebarcelona.cat/es/area-clientes",
        "https://www.aiguesdebarcelona.cat/es/area-clientes",
    )
    pdf.ln(20)

    # -------------------------------
    #            FOOTER
    # -------------------------------
    pdf.set_draw_color(200, 200, 200)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    pdf.set_text_color(80, 80, 80)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "CANALS D'ATENCIÓ AL CLIENT", ln=1)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)

    pdf.cell(30, 5, "Avaries (24h):")
    pdf.cell(60, 5, "900 700 720  /  935 218 218")
    pdf.cell(40, 5, "Des de l'estranger:")
    pdf.cell(0, 5, "+34 935 219 777", ln=1)

    pdf.cell(30, 5, "Atenció Client:")
    pdf.cell(60, 5, "900 710 710  /  935 219 777")
    pdf.cell(40, 5, "Web:")
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0, 5, "www.aiguesdebarcelona.cat", ln=1, link="https://www.aiguesdebarcelona.cat")

    # -------------------------------
    #          GUARDAR
    # -------------------------------
    pdf.output(filepath)
    print(f"📬 Carta generada: {filepath}")

    return filepath