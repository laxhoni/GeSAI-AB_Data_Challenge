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
import sys
import math

# --- IMPORTACIÓN SEGURA DEL GESTOR CRIPTOGRÁFICO ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from crypto_manager import firmar_digitalmente
except ImportError:
    from src.crypto_manager import firmar_digitalmente

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CARTAS = os.path.join(BASE_DIR, "generated_reports", "regular_mails")
os.makedirs(RUTA_CARTAS, exist_ok=True)

# --- PALETA DE COLORES ---
COLOR_PRIMARIO = (0, 89, 157)
COLOR_SECUNDARIO = (100, 100, 100)
COLOR_TEXTO = (40, 40, 40)
COLOR_FONDO_HEADER = (245, 249, 255)
COLOR_ALERTA = (204, 51, 0)
COLOR_LINEA = (220, 220, 220)

sns.set_theme(style="ticks", rc={"axes.grid": True, "grid.linestyle": ":", "grid.color": "#e0e0e0"})
plt.rcParams.update({'font.size': 8, 'font.family': 'sans-serif', 'text.color': '#444444', 'axes.labelcolor': '#666666'})

class PDF_GesAI(FPDF):
    def __init__(self):
        super().__init__()
        self.logo_path = self._find_logo()
        # Margen inferior automático
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(18, 15, 18) 
        self.digital_signature = None 
        self.angle = 0

    def _find_logo(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        paths = [
            os.path.join(os.path.dirname(base_dir), 'assets', 'logo_2.png'),
            os.path.join(base_dir, 'assets', 'logo_2.png')
        ]
        for p in paths:
            if os.path.exists(p): return p
        return None

    def Rotate(self, angle, x=None, y=None):
        if x is None: x = self.x
        if y is None: y = self.y
        if self.angle != 0: self._out('Q')
        self.angle = angle
        if angle != 0:
            angle *= math.pi / 180
            c = math.cos(angle)
            s = math.sin(angle)
            cx = x * self.k
            cy = (self.h - y) * self.k
            self._out(f'q {c:.5F} {s:.5F} {-s:.5F} {c:.5F} {cx:.2F} {cy:.2F} cm 1 0 0 1 {-cx:.2F} {-cy:.2F} cm')

    def RotatedText(self, x, y, txt, angle):
        self.Rotate(angle, x, y)
        self.text(x, y, txt)
        self.Rotate(0)

    def header(self):
        self.set_fill_color(*COLOR_FONDO_HEADER)
        self.rect(0, 0, 210, 20, 'F')
        if self.logo_path:
            self.image(self.logo_path, 15, -11, 40)
        self.set_xy(130, 12)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*COLOR_SECUNDARIO)
        self.cell(0, 5, "Gestió Segura i Automatitzada d'Incidències", 0, 1, 'R')
        self.ln(8)

    def footer(self):
        # --- FIRMA LATERAL ---
        if self.digital_signature:
            self.set_font('Courier', '', 4)
            self.set_text_color(160, 160, 160)
            self.RotatedText(205, 290, "DIGITAL SIGNATURE (GeSAI PKI)", 90)
            
            sig = self.digital_signature
            chunk_size = 130
            chunks = [sig[i:i+chunk_size] for i in range(0, len(sig), chunk_size)]
            
            start_x = 203
            for i, chunk in enumerate(chunks):
                col_x = start_x - ((i + 1) * 2) 
                self.RotatedText(col_x, 290, chunk, 90)
        
        # --- PIE DE PÁGINA ---
        self.set_y(-12) 
        self.set_font('Helvetica', '', 6)
        self.set_text_color(180, 180, 180)
        self.cell(0, 4, f"Page {self.page_no()} | Confidencial | Generat per GeSAI v2.0", 0, 0, 'C')

    def section_title(self, title):
        self.ln(3)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*COLOR_PRIMARIO)
        self.cell(0, 6, title.upper(), 0, 1, 'L')
        self.set_draw_color(*COLOR_LINEA)
        self.set_line_width(0.2)
        self.line(self.get_x(), self.get_y(), 195, self.get_y())
        self.ln(3)

    def key_value_row(self, key, value, bold_value=False):
        self.set_font('Helvetica', '', 9) 
        self.set_text_color(100, 100, 100)
        self.cell(45, 5, key, 0, 0)
        self.set_font('Helvetica', 'B' if bold_value else '', 9)
        self.set_text_color(*COLOR_TEXTO)
        val_str = str(value) if pd.notna(value) else "-"
        self.cell(0, 5, val_str, 0, 1)

def _generar_grafica_consumo_compacta(df_historico, filename):
    fig, ax = plt.subplots(figsize=(8, 2.1)) 
    fechas = pd.to_datetime(df_historico['FECHA_HORA'])
    valores = df_historico['CONSUMO_REAL']
    ax.plot(fechas, valores, color='#00599D', linewidth=1.3)
    ax.fill_between(fechas, valores, color='#00599D', alpha=0.1)
    ax.set_ylabel('Litres', fontsize=7)
    ax.tick_params(axis='both', labelsize=7, color='#888888')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    sns.despine(left=True, bottom=False)
    ax.grid(axis='x', visible=False)
    plt.tight_layout(pad=0.8)
    plt.savefig(filename, dpi=150)
    plt.close()

# ==============================================================================
# 1. INFORME TÉCNICO
# ==============================================================================
def generar_informe_tecnico_pdf(incidencia_id, datos_cliente, datos_incidencia, historico_df=None):
    pdf = PDF_GesAI()
    fecha_hoy = time.strftime("%d/%m/%Y")
    
    fingerprint = f"DOC:INFORME|ID:{incidencia_id}|CLI:{datos_cliente.get('cliente_id')}|DATE:{fecha_hoy}|STATUS:{datos_incidencia.get('estado')}"
    try: pdf.digital_signature = firmar_digitalmente(fingerprint.encode('utf-8'))
    except: pdf.digital_signature = "ERROR_FIRMA"

    pdf.add_page()
    
    # Header Doc
    pdf.set_font('Helvetica', 'B', 14); pdf.set_text_color(40, 40, 40)
    pdf.cell(120, 8, "INFORME TÈCNIC D'INCIDÈNCIA", 0, 0)
    pdf.set_font('Helvetica', '', 8); pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"REF: #{incidencia_id} | {fecha_hoy}", 0, 1, 'R')

    # 1. Datos
    pdf.section_title("1. Dades del Punt de Subministrament")
    pdf.key_value_row("Titular:", datos_cliente.get('nombre', 'N/A'), True)
    pdf.key_value_row("Pòlissa:", datos_cliente.get('cliente_id', 'N/A'))
    pdf.key_value_row("Adreça:", datos_cliente.get('direccion', 'N/A'))
    pdf.key_value_row("Contacte:", f"{datos_cliente.get('telefono', '-')} / {datos_cliente.get('email', '-')}")

    # 2. Diagnóstico
    pdf.section_title("2. Diagnòstic del Sistema (IA)")
    estado = datos_incidencia.get('estado', 'PENDENT').upper()
    if "GRAVE" in estado: bg, txt = (255, 235, 235), COLOR_ALERTA
    elif "MODERADA" in estado: bg, txt = (255, 248, 225), (180, 100, 0)
    else: bg, txt = (235, 255, 235), (0, 120, 0)

    pdf.set_fill_color(*bg)
    pdf.rect(18, pdf.get_y(), 175, 12, 'F')
    pdf.set_xy(25, pdf.get_y() + 3)
    pdf.set_font('Helvetica', 'B', 10); pdf.set_text_color(80, 80, 80)
    pdf.cell(35, 6, "CLASSIFICACIÓ:", 0, 0)
    pdf.set_font('Helvetica', 'B', 11); pdf.set_text_color(*txt)
    pdf.cell(0, 6, estado, 0, 1)
    pdf.ln(5)
    
    pdf.key_value_row("Probabilitat:", f"{datos_incidencia.get('prob_hoy', 0):.2%}")
    pdf.key_value_row("Descripció:", datos_incidencia.get('descripcion', '-'))

    # 3. Análisis
    if historico_df is not None and not historico_df.empty:
        pdf.section_title("3. Anàlisi de Facturació")
        
        consumo = historico_df['CONSUMO_REAL'].sum()
        base = historico_df['CONSUMO_REAL'].median()
        df_exc = historico_df[historico_df['CONSUMO_REAL'] > (base * 1.1)]
        
        litros = 0; coste = 0; horas = 0
        if not df_exc.empty and ("GRAVE" in estado or "MODERADA" in estado):
            litros = (df_exc['CONSUMO_REAL'] - base).sum()
            horas = len(df_exc)
            coste = (litros / 1000) * 2.85
            
        y_start = pdf.get_y()
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(18, y_start, 175, 14, 'F')
        pdf.set_y(y_start + 3)
        
        pdf.set_x(18)
        pdf.set_font('Helvetica', 'B', 7); pdf.set_text_color(100, 100, 100)
        pdf.cell(44, 3, "CONSUM TOTAL", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11); pdf.set_text_color(0, 0, 0)
        pdf.cell(44, 5, f"{consumo/1000:.2f} m3", 0, 0, 'C')
        
        pdf.set_xy(62, y_start + 3)
        pdf.set_font('Helvetica', 'B', 7); pdf.set_text_color(100, 100, 100)
        pdf.cell(44, 3, "FUITA ESTIMADA", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11)
        if litros > 50: pdf.set_text_color(*COLOR_ALERTA); pdf.cell(44, 5, f"{litros:.0f} L", 0, 0, 'C')
        else: pdf.set_text_color(0, 150, 0); pdf.cell(44, 5, "0 L", 0, 0, 'C')

        pdf.set_xy(106, y_start + 3)
        pdf.set_font('Helvetica', 'B', 7); pdf.set_text_color(100, 100, 100)
        pdf.cell(44, 3, "IMPACTE ECON.", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11)
        if coste > 0.1: pdf.set_text_color(*COLOR_ALERTA); pdf.cell(44, 5, f"+{coste:.2f} EUR", 0, 0, 'C')
        else: pdf.set_text_color(0, 0, 0); pdf.cell(44, 5, "-", 0, 0, 'C')
            
        pdf.set_xy(150, y_start + 3)
        pdf.set_font('Helvetica', 'B', 7); pdf.set_text_color(100, 100, 100)
        pdf.cell(44, 3, "DURADA", 0, 2, 'C')
        pdf.set_font('Helvetica', 'B', 11); pdf.set_text_color(0, 0, 0)
        if horas > 0:
            dias = horas // 24; horas_rest = horas % 24
            texto_dur = f"{dias}d {horas_rest}h" if dias > 0 else f"{horas_rest}h"
            pdf.cell(44, 5, texto_dur, 0, 0, 'C')
        else: pdf.cell(44, 5, "0h", 0, 0, 'C')
        
        pdf.ln(8)

        chart_path = f"temp_chart_{incidencia_id}.png"
        try:
            _generar_grafica_consumo_compacta(historico_df, chart_path)
            pdf.image(chart_path, x=18, w=175, h=50) 
            pdf.ln(2)
            pdf.set_font('Helvetica', 'I', 7); pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 4, "Fig 1. Evolució horària del consum (Últims 30 dies).", 0, 1, 'C')
            os.remove(chart_path)
        except Exception as e: pdf.cell(0, 5, f"Error: {e}", 0, 1)
            
    # 4. Encuesta
    encuesta = datos_incidencia.get('encuesta_resultado')
    if encuesta:
        try:
            items = json.loads(encuesta)
            pdf.ln(3)
            pdf.section_title("4. Verificació Client (App Mòbil)")
            pdf.set_fill_color(250, 250, 250)
            pdf.set_font('Helvetica', 'B', 7); pdf.set_text_color(100, 100, 100)
            pdf.cell(150, 5, "PREGUNTA", 0, 0, 'L', True)
            pdf.cell(30, 5, "RESPOSTA", 0, 1, 'C', True)
            
            if isinstance(items, list):
                for x in items:
                    p = x.get('pregunta', '-')[:90]
                    r = str(x.get('respuesta', '-')).upper()
                    pdf.set_font('Helvetica', '', 7); pdf.set_text_color(40, 40, 40)
                    pdf.cell(150, 5, f"- {p}", 0, 0, 'L')
                    if r in ['SI', 'SÍ']: pdf.set_font('Helvetica', 'B', 7); pdf.set_text_color(*COLOR_ALERTA)
                    pdf.cell(30, 5, r, 0, 1, 'C')
        except: pass

    # Disclaimer al pie
    pdf.set_y(-25)
    pdf.set_font('Helvetica', '', 6); pdf.set_text_color(180, 180, 180)
    pdf.multi_cell(0, 3, "AVÍS LEGAL: Document informatiu basat en anàlisi predictiva. No substitueix inspecció física oficial.", 0, 'C')

    output_dir = '../generated_reports/technical_reports/'
    os.makedirs(output_dir, exist_ok=True)
    cliente_id = datos_cliente.get('cliente_id', 'Unknown')
    filename = os.path.join(output_dir, f"Informe_Tecnic_{cliente_id}_{incidencia_id}.pdf")
    pdf.output(filename)
    return filename

# ==============================================================================
# 2. CARTA POSTAL (COMPLETA Y RECUPERADA)
# ==============================================================================
def generar_carta_postal_pdf(incidencia_id, cliente):
    import os, time
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR = os.path.join(BASE_DIR, "generated_reports", "regular_mails")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cliente_id = cliente.get("cliente_id", "Unknown")
    filename = f"Carta_Incidencia_{cliente_id}_{incidencia_id}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf = PDF_GesAI()
    fecha = time.strftime("%d/%m/%Y")
    
    try:
        fprint = f"DOC:CARTA|ID:{incidencia_id}|CLI:{cliente_id}|DATE:{fecha}"
        pdf.digital_signature = firmar_digitalmente(fprint.encode('utf-8'))
    except: pass

    pdf.add_page()
    pdf.set_xy(110, 50); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(85, 5, f"{cliente.get('nombre','')}\n{cliente.get('direccion','')}\n", align="L"); pdf.ln(30)
    
    # TITULO CARTA
    pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(*COLOR_ALERTA)
    pdf.cell(0, 8, f"AVÍS IMPORTANT: ANOMALIA DE CONSUM (REF. #{incidencia_id})", ln=1); pdf.ln(5)
    
    # CUERPO RECUPERADO
    pdf.set_font("Helvetica", "", 10); pdf.set_text_color(40, 40, 40)
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
    
    # CALL TO ACTION
    pdf.set_draw_color(*COLOR_PRIMARIO); pdf.set_fill_color(250, 252, 255); pdf.set_line_width(0.3)
    y_start = pdf.get_y(); pdf.rect(15, y_start, 180, 20, style="DF")
    pdf.set_xy(20, y_start + 5); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(0, 5, "ACTUALITZI LES SEVES DADES PER REBRE AVISOS AL MÒBIL:", ln=1)
    pdf.set_x(20); pdf.set_font("Helvetica", "", 9); pdf.set_text_color(0, 0, 0)
    pdf.write(5, "Accedeixi a l'Àrea de Clients: "); pdf.set_font("Helvetica", "U", 9); pdf.set_text_color(0, 0, 255)
    pdf.write(5, "https://www.aiguesdebarcelona.cat/es/area-clientes", "https://www.aiguesdebarcelona.cat/es/area-clientes"); pdf.ln(20)

    # --- PIE DE PÁGINA DE CONTACTO (RECUPERADO) ---
    pdf.set_draw_color(200, 200, 200); pdf.line(20, pdf.get_y(), 190, pdf.get_y()); pdf.ln(5)
    pdf.set_text_color(80, 80, 80); pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, "CANALS D'ATENCIÓ AL CLIENT", ln=1)
    pdf.set_font("Helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(30, 5, "Avaries (24h):"); pdf.cell(60, 5, "900 700 720  /  935 218 218")
    pdf.cell(40, 5, "Des de l'estranger:"); pdf.cell(0, 5, "+34 935 219 777", ln=1)
    pdf.cell(30, 5, "Atenció Client:"); pdf.cell(60, 5, "900 710 710  /  935 219 777")
    pdf.cell(40, 5, "Web:"); pdf.set_text_color(0, 0, 255)
    pdf.cell(0, 5, "www.aiguesdebarcelona.cat", ln=1, link="https://www.aiguesdebarcelona.cat")
    # ----------------------------------------------

    pdf.output(filepath)
    return filepath