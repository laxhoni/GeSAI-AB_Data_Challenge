# src/reports_manager.py

from fpdf import FPDF
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import time

# --- CONFIGURACIÓN DE ESTILO ---
COLOR_CABECERA_FONDO = (240, 248, 255) # Azul muy muy claro (AliceBlue)
COLOR_TEXTO_TITULO = (0, 114, 188)     # Azul Corporativo
COLOR_TEXTO_CUERPO = (50, 50, 50)      # Gris Oscuro
COLOR_ALERTA = (200, 0, 0)             # Rojo

# Configuración de Gráficas (Limpia)
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 8, 'font.family': 'sans-serif'})

class PDF_GesAI(FPDF):
    def __init__(self):
        super().__init__()
        self.logo_path = self._find_logo()
        self.set_auto_page_break(auto=True, margin=15)

    def _find_logo(self):
        """Busca el logo 'logo_2.png' resolviendo rutas absolutas."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Intento 1: ../assets/logo_2.png
        logo_path = os.path.join(os.path.dirname(base_dir), 'assets', 'logo_2.png')
        if os.path.exists(logo_path): return logo_path
        # Intento 2: src/assets/logo_2.png
        logo_path = os.path.join(base_dir, 'assets', 'logo_2.png')
        if os.path.exists(logo_path): return logo_path
        return None

    def header(self):
        # 1. Fondo Cabecera (Azul Muy Claro)
        self.set_fill_color(*COLOR_CABECERA_FONDO)
        self.rect(0, 0, 210, 35, 'F') 
        
        # 2. Logo (Izquierda)
        if self.logo_path:
            self.image(self.logo_path, 10, 6, 45) # Logo visible y claro
        
        # 3. Texto Cabecera (Derecha - Sin repetir GeSAI)
        self.set_xy(0, 12)
        self.set_font('Arial', '', 10)
        self.set_text_color(80, 80, 80) # Gris suave
        self.cell(195, 6, "Gestió Segura i Automatitzada d'Incidències", 0, 1, 'R')
        
        # 4. Línea sutil inferior
        self.set_draw_color(*COLOR_TEXTO_TITULO)
        self.set_line_width(0.3)
        self.line(0, 35, 210, 35)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pàgina {self.page_no()} | Document generat automàticament per GeSAI - Aigües de Barcelona', 0, 0, 'C')

    def section_title(self, title):
        self.ln(2)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLOR_TEXTO_TITULO)
        self.cell(0, 8, title.upper(), 'B', 1, 'L')
        self.ln(3)

    def info_row(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(50, 50, 50)
        self.cell(45, 5, f"{label}:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, str(value), 0, 1)

# --- FUNCIÓN GRÁFICA (Solo Consumo) ---
def _generar_grafica_consumo(df_historico, filename):
    """Genera gráfica lineal compacta."""
    plt.figure(figsize=(8, 3)) # Más bajita para que quepa en 1 pág
    
    fechas = pd.to_datetime(df_historico['FECHA_HORA'])
    valores = df_historico['CONSUMO_REAL']
    
    plt.plot(fechas, valores, color='#0072BC', linewidth=1.5, label='Consum (L)')
    plt.fill_between(fechas, valores, color='#0072BC', alpha=0.1)
    
    plt.title('Registre Horari de Consum', fontsize=9, fontweight='bold', pad=10)
    plt.ylabel('Litres', fontsize=8)
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    plt.xticks(fontsize=7)
    plt.yticks(fontsize=7)
    
    # Limpieza visual
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=100)
    plt.close()

# ==============================================================================
# 1. INFORME TÉCNICO (1 PÁGINA ESTRICTA)
# ==============================================================================
def generar_informe_tecnico_pdf(incidencia_id, datos_cliente, datos_incidencia, historico_df=None):
    pdf = PDF_GesAI()
    pdf.add_page()
    fecha_hoy = time.strftime("%d/%m/%Y")
    
    # --- Título ---
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLOR_TEXTO_TITULO)
    pdf.cell(0, 8, f"INFORME TÈCNIC D'INCIDÈNCIA #{incidencia_id}", 0, 1, 'C')
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Data d'emissió: {fecha_hoy}", 0, 1, 'C')
    pdf.ln(3)

    # --- 1. Datos Cliente ---
    pdf.section_title("1. DADES DEL PUNT DE SUBMINISTRAMENT")
    pdf.info_row("Titular", datos_cliente.get('nombre', 'N/A'))
    pdf.info_row("Pòlissa", datos_cliente.get('cliente_id', 'N/A'))
    pdf.info_row("Adreça", datos_cliente.get('direccion', 'N/A'))
    pdf.info_row("Contacte", f"{datos_cliente.get('telefono', '-')} | {datos_cliente.get('email', '-')}")

    # --- 2. Diagnóstico IA (Minimalista) ---
    pdf.section_title("2. DIAGNÒSTIC DEL SISTEMA")
    
    # Estado
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(45, 5, "Classificació:", 0, 0)
    pdf.set_text_color(*COLOR_ALERTA)
    pdf.cell(0, 5, datos_incidencia.get('estado', 'Pendent').upper(), 0, 1)
    
    # Descripción
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, f"Detall: {datos_incidencia.get('descripcion', '-')}")
    
    # Probabilidad (SOLO NÚMERO)
    prob = datos_incidencia.get('prob_hoy', 0)
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(45, 5, "Probabilitat Fuga:", 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f"{prob:.2%} (Calculada avui)", 0, 1)
    pdf.ln(2)

    # --- 3. Evidencia Consumo ---
    if historico_df is not None and not historico_df.empty:
        pdf.section_title("3. ANÀLISI DE CONSUM")
        
        # Datos resumen en una línea
        consumo_total = historico_df['CONSUMO_REAL'].sum()
        promedio = historico_df['CONSUMO_REAL'].mean()
        periodo = f"{historico_df['FECHA_HORA'].min().strftime('%d/%m')} - {historico_df['FECHA_HORA'].max().strftime('%d/%m')}"
        
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 5, f"Període: {periodo}  |  Consum Total: {consumo_total:.2f} L  |  Mitjana: {promedio:.2f} L/h", 0, 1)
        pdf.ln(2)
        
        # Gráfica Compacta
        chart_consumo = f"temp_chart_{incidencia_id}.png"
        try:
            _generar_grafica_consumo(historico_df, chart_consumo)
            # Imagen ajustada para que quepa
            pdf.image(chart_consumo, x=15, w=180) 
            os.remove(chart_consumo)
        except Exception as e:
            pdf.cell(0, 5, f"Error gràfica: {e}", 0, 1)
            
    output_dir = '../generated_reports/technical_reports/'
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"Informe_Tecnic_{incidencia_id}.pdf")
    pdf.output(filename)
    print(f"✅ Informe Técnico generado (1 Pág): {filename}")
    return filename

# ==============================================================================
# 2. CARTA POSTAL (CLIENTE) - CABECERA CORREGIDA
# ==============================================================================
def generar_carta_postal_pdf(incidencia_id, cliente):
    pdf = PDF_GesAI()
    pdf.add_page()
    fecha = time.strftime("%d/%m/%Y")
    
    # La cabecera con logo se pone sola (heredada de PDF_GesAI.header)
    pdf.ln(5)
    
    # Destinatario
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, "PER A:", 0, 1)
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    
    nombre = cliente.get('nombre', 'Client')
    direccion = cliente.get('direccion', 'Adreça Desconeguda')
    
    pdf.set_fill_color(245, 245, 245) 
    pdf.multi_cell(85, 5, f"{nombre}\n{direccion}", 0, 'L', True)
    
    pdf.ln(30)
    
    # Asunto
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(*COLOR_ALERTA)
    pdf.cell(0, 8, f"AVÍS IMPORTANT: ANOMALIA DE CONSUM (PÒLISSA: {cliente.get('cliente_id', 'N/A')})", 0, 1, 'L')
    pdf.set_draw_color(*COLOR_ALERTA)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Cuerpo
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    cuerpo = (
        f"Apreciat/da client/a,\n\n"
        f"En data {fecha}, els nostres sistemes han detectat un consum inusual al seu comptador (Ref. #{incidencia_id}).\n\n"
        f"Li enviem aquesta notificació postal perquè no disposem de les seves dades de contacte digital. "
        f"Li preguem que revisi la seva instal·lació."
    )
    pdf.multi_cell(0, 5, cuerpo)
    pdf.ln(10)
    
    # Caja Acción
    pdf.set_fill_color(235, 245, 255)
    pdf.set_draw_color(*COLOR_TEXTO_TITULO)
    pdf.rect(15, pdf.get_y(), 180, 25, 'DF')
    
    pdf.set_xy(20, pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(*COLOR_TEXTO_TITULO)
    pdf.cell(0, 5, "ACTUALITZI LES SEVES DADES:", 0, 1)
    
    pdf.set_x(20)
    pdf.set_font('Arial', 'U', 10)
    pdf.set_text_color(0, 0, 255)
    pdf.write(5, "https://www.aiguesdebarcelona.cat/es/area-clientes", "https://www.aiguesdebarcelona.cat/es/area-clientes")
    pdf.ln(15)
    
    # Contacto
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 6, "CANALS D'ATENCIÓ:", 0, 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(40, 5, "Avaries (24h):", 0, 0); pdf.cell(0, 5, "900 700 720", 0, 1)
    pdf.cell(40, 5, "Atenció Client:", 0, 0); pdf.cell(0, 5, "900 710 710", 0, 1)
    pdf.cell(40, 5, "Més info:", 0, 0)
    pdf.set_text_color(0, 0, 255); pdf.set_font('Arial', 'U', 9)
    pdf.write(5, "www.aiguesdebarcelona.cat/es/contacto", "https://www.aiguesdebarcelona.cat/es/contacto")
    
    output_dir = '../generated_reports/regular_mails/'
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"Carta_Incidencia_{incidencia_id}.pdf")
    pdf.output(filename)
    print(f"✅ Carta generada: {filename}")
    return filename