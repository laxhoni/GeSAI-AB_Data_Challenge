# src/reports_manager.py

from fpdf import FPDF
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import time

# --- CONFIGURACIÓN DE ESTILO ---
COLOR_PRIMARIO = (0, 114, 188)    # Azul Aigües (Texto Títulos)
COLOR_SECUNDARIO = (80, 80, 80)   # Gris oscuro (Subtítulos)
COLOR_FONDO_HEADER = (240, 248, 255) # Azul MUY clarito (AliceBlue) para el fondo
COLOR_ALERTA = (200, 0, 0)        # Rojo para avisos

# Configuración de Gráficas
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 9, 'font.family': 'sans-serif'})

class PDF_GesAI(FPDF):
    def __init__(self):
        super().__init__()
        self.logo_path = self._find_logo()
        self.set_auto_page_break(auto=True, margin=20)

    def _find_logo(self):
        """Busca el logo 'logo_2.png' resolviendo rutas absolutas."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Opción 1: Estructura estándar de proyecto (../assets/)
        project_root = os.path.dirname(base_dir)
        logo_path = os.path.join(project_root, 'assets', 'logo_2.png')
        if os.path.exists(logo_path):
            return logo_path
            
        # Opción 2: Carpeta assets dentro de src (src/assets/)
        logo_fallback = os.path.join(base_dir, 'assets', 'logo_2.png')
        if os.path.exists(logo_fallback):
            return logo_fallback
            
        return None

    def header(self):
        # --- CABECERA PROFESIONAL (Fondo Claro) ---
        
        # 1. Fondo Azul Muy Clarito (Cubre toda la cabecera)
        self.set_fill_color(*COLOR_FONDO_HEADER)
        self.rect(0, 0, 210, 35, 'F') # Ancho A4, Alto 35mm
        
        # 2. Logo (Esquina Izquierda)
        if self.logo_path:
            # Ajustado: x=10, y=6, ancho=45
            self.image(self.logo_path, 10, 6, 45) 
        
        # 3. Título Corporativo (Alineado a la Derecha)
        self.set_font('Arial', 'B', 20)
        self.set_text_color(*COLOR_PRIMARIO) # Texto Azul sobre fondo claro
        self.set_xy(60, 10)
        self.cell(0, 10, 'GeSAI', 0, 1, 'R')
        
        # 4. Subtítulo
        self.set_font('Arial', '', 10)
        self.set_text_color(*COLOR_SECUNDARIO) # Gris oscuro
        self.set_xy(60, 18)
        self.cell(0, 6, "Gestió Segura i Automatitzada d'Incidències", 0, 1, 'R')
        
        # 5. Línea sutil inferior
        self.set_draw_color(*COLOR_PRIMARIO)
        self.set_line_width(0.5)
        self.line(0, 35, 210, 35)
        
        self.ln(15) # Espacio antes de empezar el contenido

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pàgina {self.page_no()} | GeSAI - Aigües de Barcelona', 0, 0, 'C')

    def section_title(self, title):
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*COLOR_PRIMARIO)
        self.set_draw_color(*COLOR_PRIMARIO)
        self.set_line_width(1)
        self.cell(0, 8, title.upper(), 'B', 1, 'L')
        self.ln(3)

    def info_box(self, label, value):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(50, 50, 50)
        self.cell(55, 7, f"{label}:", 0, 0)
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        val_str = str(value) if pd.notna(value) else "No disponible"
        self.cell(0, 7, val_str, 0, 1)

# --- FUNCIONES DE GRÁFICAS ---

def _generar_grafica_consumo(df_historico, filename):
    """Genera gráfica lineal de consumo real."""
    plt.figure(figsize=(10, 4))
    
    fechas = pd.to_datetime(df_historico['FECHA_HORA'])
    valores = df_historico['CONSUMO_REAL']
    
    plt.plot(fechas, valores, color='#0072BC', linewidth=2, label='Consum Real')
    plt.fill_between(fechas, valores, color='#0072BC', alpha=0.1)
    
    plt.title('Evidència de Consum (Telelectura)', fontsize=11, fontweight='bold', pad=15)
    plt.ylabel('Consum (Litres)', fontsize=9)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %Hh'))
    plt.xticks(rotation=15)
    
    # Estilo limpio (sin bordes superiores/derechos)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=120)
    plt.close()

# ==============================================================================
# 1. INFORME TÉCNICO (EMPRESA)
# ==============================================================================
def generar_informe_tecnico_pdf(incidencia_id, datos_cliente, datos_incidencia, historico_df=None):
    pdf = PDF_GesAI()
    pdf.add_page()
    fecha_hoy = time.strftime("%d/%m/%Y")
    
    # Título
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(0, 10, f"INFORME TÈCNIC D'INCIDÈNCIA #{incidencia_id}", 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Data d'emissió: {fecha_hoy}", 0, 1, 'C')
    pdf.ln(5)

    # 1. Datos Cliente
    pdf.section_title("1. DADES DEL CLIENT I PUNT DE SUBMINISTRAMENT")
    pdf.info_box("Titular", datos_cliente.get('nombre', 'N/A'))
    pdf.info_box("Pòlissa", datos_cliente.get('cliente_id', 'N/A')) 
    pdf.info_box("Adreça", datos_cliente.get('direccion', 'N/A'))
    pdf.info_box("Contacte", f"{datos_cliente.get('telefono', '-')} | {datos_cliente.get('email', '-')}")

    # 2. Análisis IA
    pdf.section_title("2. ANÀLISI PREDICTIVA DE RISC")
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 7, "Estat Detectat:", 0, 0)
    pdf.set_text_color(*COLOR_ALERTA)
    pdf.cell(0, 7, datos_incidencia.get('estado', 'Pendent').upper(), 0, 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, f"Descripció del model: {datos_incidencia.get('descripcion', '-')}")
    pdf.ln(4)

    # --- PANEL DE PROBABILIDADES (TEXTO VISUAL) ---
    probs = {
        'Avui': datos_incidencia.get('prob_hoy', 0),
        'Demà': datos_incidencia.get('prob_manana', 0),
        '7 Dies': datos_incidencia.get('prob_7dias', 0)
    }
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Probabilitat de Fuga Estimada (Model IA):", 0, 1)
    pdf.ln(2)

    # Cajas de colores
    box_width = 60
    h = 20
    x_start = 15
    current_x = x_start
    
    for label, p in probs.items():
        # Color semáforo suave
        pdf.set_fill_color(245, 245, 245) # Gris base
        if p > 0.85: pdf.set_fill_color(255, 200, 200) # Rojo claro
        elif p > 0.65: pdf.set_fill_color(255, 236, 179) # Naranja claro
        elif p < 0.50: pdf.set_fill_color(200, 230, 200) # Verde claro

        pdf.set_xy(current_x, pdf.get_y())
        pdf.rect(current_x, pdf.get_y(), box_width, h, 'F')
        
        # Etiqueta
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(current_x, pdf.get_y() + 3)
        pdf.cell(box_width, 5, label.upper(), 0, 2, 'C')
        
        # Valor
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(box_width, 8, f"{p:.1%}", 0, 0, 'C')
        
        current_x += box_width + 5
    
    pdf.ln(h + 10)

    # 3. Evidencia Consumo
    if historico_df is not None and not historico_df.empty:
        pdf.add_page()
        pdf.section_title("3. EVIDÈNCIA DE CONSUM (TELELECTURA)")
        
        consumo_total = historico_df['CONSUMO_REAL'].sum()
        promedio = historico_df['CONSUMO_REAL'].mean()
        fecha_ini = historico_df['FECHA_HORA'].min().strftime("%d/%m/%Y")
        fecha_fin = historico_df['FECHA_HORA'].max().strftime("%d/%m/%Y")
        
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f"Període analitzat: {fecha_ini} - {fecha_fin}", 0, 1, 'L', 1)
        pdf.cell(95, 8, f"Consum Total Acumulat: {consumo_total:.2f} Litres", 0, 0, 'L', 1)
        pdf.cell(95, 8, f"Mitjana per lectura: {promedio:.2f} L/h", 0, 1, 'L', 1)
        pdf.ln(5)
        
        chart_consumo = f"temp_consumo_{incidencia_id}.png"
        try:
            _generar_grafica_consumo(historico_df, chart_consumo)
            pdf.image(chart_consumo, x=10, w=190)
            os.remove(chart_consumo)
            pdf.ln(2)
            pdf.set_font('Arial', 'I', 8)
            pdf.cell(0, 5, "Fig 1. Detall horari del consum registrat.", 0, 1, 'C')
        except Exception as e:
            pdf.cell(0, 10, f"Error generant gràfica de consum: {e}", 0, 1)
            
    output_dir = '../generated_reports/technical_reports/'
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"Informe_Tecnic_{incidencia_id}.pdf")
    pdf.output(filename)
    print(f"✅ Informe Técnico generado: {filename}")
    return filename

# ==============================================================================
# 2. CARTA POSTAL (CLIENTE)
# ==============================================================================
def generar_carta_postal_pdf(incidencia_id, cliente):
    pdf = PDF_GesAI()
    pdf.add_page()
    fecha = time.strftime("%d/%m/%Y")
    
    pdf.ln(10)
    
    # --- Destinatario ---
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, "PER A:", 0, 1)
    pdf.set_x(110)
    pdf.set_font('Arial', '', 11)
    
    nombre = cliente.get('nombre', 'Client')
    direccion = cliente.get('direccion', 'Adreça Desconeguda')
    
    pdf.set_fill_color(245, 245, 245) 
    pdf.multi_cell(85, 6, f"{nombre}\n{direccion}", 0, 'L', True)
    
    pdf.ln(35)
    
    # Asunto
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*COLOR_ALERTA)
    pdf.cell(0, 10, f"AVÍS IMPORTANT: ANOMALIA DE CONSUM (PÒLISSA: {cliente.get('cliente_id', 'N/A')})", 0, 1, 'L')
    pdf.set_draw_color(*COLOR_ALERTA)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # Cuerpo
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 11)
    cuerpo = (
        f"Apreciat/da client/a,\n\n"
        f"En data {fecha}, els nostres sistemes de monitoratge intel·ligent (GeSAI) han detectat un patró de consum "
        f"d'aigua inusual al seu comptador (Ref. Incidència #{incidencia_id}).\n\n"
        f"Li enviem aquesta notificació per correu postal perquè no disposem de les seves dades de contacte digital "
        f"(mòbil o email) actualitzades. Li preguem que revisi la seva instal·lació."
    )
    pdf.multi_cell(0, 6, cuerpo)
    pdf.ln(15)
    
    # Caja de Acción
    pdf.set_fill_color(230, 242, 255)
    pdf.set_draw_color(*COLOR_PRIMARIO)
    pdf.set_line_width(0.5)
    
    y_box = pdf.get_y()
    pdf.rect(10, y_box, 190, 30, 'DF')
    
    pdf.set_xy(15, y_box + 5)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(0, 6, "ACTUALITZI LES SEVES DADES PER REBRE ALERTES AL MÒBIL", 0, 1)
    
    pdf.set_x(15)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.write(6, "Registri's a la nostra Àrea de Clients a: ")
    pdf.set_font('Arial', 'U', 10)
    pdf.set_text_color(0, 0, 255)
    pdf.write(6, "https://www.aiguesdebarcelona.cat/es/area-clientes", "https://www.aiguesdebarcelona.cat/es/area-clientes")
    pdf.ln(20)
    
    # Info de Contacto
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "CANALS D'ATENCIÓ:", 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, "Avaries (24h):", 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "900 700 720 / 935 218 218", 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, "Atenció Client (8h-20h):", 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "900 710 710 / 935 219 777", 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, "Des de l'estranger:", 0, 0)
    pdf.cell(0, 6, "+34 935 219 777", 0, 1)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 9)
    pdf.write(6, "Més informació: ")
    pdf.set_text_color(0, 0, 255)
    pdf.set_font('Arial', 'U', 9)
    pdf.write(6, "www.aiguesdebarcelona.cat/es/contacto", "https://www.aiguesdebarcelona.cat/es/contacto")
    
    output_dir = '../generated_reports/regular_mails/'
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"Carta_Incidencia_{incidencia_id}.pdf")
    pdf.output(filename)
    print(f"✅ Carta Postal generada: {filename}")
    return filename