

# src/reports_manager.py

from fpdf import FPDF
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import time

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
    pdf.ln(5)

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
    
    pdf.ln(6)
    
    # Detalles técnicos
    pdf.key_value_row("Probabilitat de Fuga:", f"{datos_incidencia.get('prob_hoy', 0):.2%} (Model Predictiu)")
    pdf.key_value_row("Descripció Tècnica:", datos_incidencia.get('descripcion', '-'))

       # --- 3. Evidencia Consumo (NUEVO DISEÑO TABLA) ---
    if historico_df is not None and not historico_df.empty:
        pdf.section_title("3. Anàlisi de Consum")
        
        # Calcular datos
        consumo_total = historico_df['CONSUMO_REAL'].sum()
        promedio = historico_df['CONSUMO_REAL'].mean()
        fecha_ini = historico_df['FECHA_HORA'].min().strftime("%d/%m")
        fecha_fin = historico_df['FECHA_HORA'].max().strftime("%d/%m")
        
        # Dibujar Grid de Métricas (3 Columnas)
        y_start = pdf.get_y()
        
        # Fondo Gris
        pdf.set_fill_color(*COLOR_LINEA)
        pdf.rect(15, y_start, 180, 15, 'F')
        
        pdf.set_y(y_start + 3)
        
        # Columna 1: Periodo
        pdf.set_x(15)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(60, 4, "PERÍODE", 0, 2, 'C')
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 5, f"{fecha_ini} - {fecha_fin}", 0, 0, 'C')
        
        # Columna 2: Total
        pdf.set_xy(75, y_start + 3)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(60, 4, "VOLUM TOTAL", 0, 2, 'C')
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(*COLOR_PRIMARIO)
        pdf.cell(60, 5, f"{consumo_total:.2f} L", 0, 0, 'C')
        
        # Columna 3: Mitjana
        pdf.set_xy(135, y_start + 3)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(60, 4, "MITJANA / HORA", 0, 2, 'C')
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 5, f"{promedio:.2f} L/h", 0, 0, 'C')
        
        pdf.ln(10) # Salir de la caja
        
        # Gráfica
        chart_path = f"temp_chart_{incidencia_id}.png"

        try:
            _generar_grafica_consumo_compacta(historico_df, chart_path)
            
            # 1. Insertar la imagen
            pdf.image(chart_path, x=15, w=180) 
            
            # --- NUEVO: AÑADIR REFERENCIA FIG. 1 ---
            pdf.ln(1) # Pequeño espacio vertical (1mm)
            pdf.set_font('Arial', 'I', 8) # Fuente Itálica, tamaño 8
            pdf.set_text_color(100, 100, 100) # Color gris para que parezca un pie de foto
            # 'C' al final centra el texto respecto a la página
            pdf.cell(0, 5, "Fig 1. Dades de telelectura del comptador: consum real (m³) vs temps.", 0, 1, 'C') 
            # ---------------------------------------

            os.remove(chart_path)
        except Exception as e:
            pdf.cell(0, 5, f"Error gràfica: {e}", 0, 1)
    # Guardar
    output_dir = '../generated_reports/technical_reports/'
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"Informe_Tecnic_{incidencia_id}.pdf")
    pdf.output(filename)
    print(f"✅ Informe Profesional generado: {filename}")
    return filename


# ==============================================================================
# 2. CARTA POSTAL (ESTILO CORRESPONDENCIA OFICIAL)
# ==============================================================================
def generar_carta_postal_pdf(incidencia_id, cliente):
    pdf = PDF_GesAI()
    pdf.add_page()
    fecha = time.strftime("%d/%m/%Y")
    
    # --- Bloque Dirección (Ventana Derecha) ---
    # Posición estándar para sobres con ventana derecha
    pdf.set_y(50) 
    pdf.set_x(110) 
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(0, 0, 0)
    
    # Datos del destinatario limpios
    nombre = cliente.get('nombre', 'Estimado Cliente')
    direccion = cliente.get('direccion', 'Adreça Desconeguda')
    
    pdf.multi_cell(85, 5, f"{nombre}\n{direccion}\n08xxx Barcelona", 0, 'L')
    
    pdf.ln(30) # Espacio tras la dirección
    
    # --- Contenido de la Carta ---
    
    # Asunto destacado
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(*COLOR_ALERTA)
    pdf.cell(0, 8, f"AVÍS IMPORTANT: ANOMALIA DE CONSUM (REF. #{incidencia_id})", 0, 1, 'L')
    pdf.ln(5)
    
    # Texto cuerpo (Justificado y profesional)
    pdf.set_text_color(40, 40, 40)
    pdf.set_font('Helvetica', '', 10)
    
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
    
    # --- Call to Action (Recuadro Limpio) ---
    pdf.set_draw_color(*COLOR_PRIMARIO)
    pdf.set_line_width(0.3)
    # Fondo muy sutil
    pdf.set_fill_color(250, 252, 255)
    
    y_start = pdf.get_y()
    pdf.rect(15, y_start, 180, 20, 'DF')
    
    pdf.set_xy(20, y_start + 5)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(0, 5, "ACTUALITZI LES SEVES DADES PER REBRE AVISOS AL MÒBIL:", 0, 1)
    
    pdf.set_x(20)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0, 0, 0)
    pdf.write(5, "Accedeixi a l'Àrea de Clients: ")
    pdf.set_font('Helvetica', 'U', 9)
    pdf.set_text_color(0, 0, 255)
    pdf.write(5, "https://www.aiguesdebarcelona.cat/es/area-clientes", "https://www.aiguesdebarcelona.cat/es/area-clientes")
    
    pdf.ln(20)
    
    # --- Pie de Contacto (Limpio) ---
    pdf.set_draw_color(200, 200, 200)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_text_color(80, 80, 80)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(0, 5, "CANALS D'ATENCIÓ AL CLIENT", 0, 1)
    
    pdf.set_font('Helvetica', '', 8)
    # Fila 1
    pdf.cell(30, 5, "Avaries (24h):", 0, 0)
    pdf.cell(60, 5, "900 700 720  /  935 218 218", 0, 0)
    pdf.cell(40, 5, "Des de l'estranger:", 0, 0)
    pdf.cell(0, 5, "+34 935 219 777", 0, 1)
    # Fila 2
    pdf.cell(30, 5, "Atenció Client:", 0, 0)
    pdf.cell(60, 5, "900 710 710  /  935 219 777", 0, 0)
    pdf.cell(40, 5, "Web:", 0, 0)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0, 5, "www.aiguesdebarcelona.cat", 0, 1, link="https://www.aiguesdebarcelona.cat")

    # Guardar
    output_dir = '../generated_reports/regular_mails/'
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"Carta_Incidencia_{incidencia_id}.pdf")
    pdf.output(filename)
    print(f"✅ Carta Profesional generada: {filename}")
    return filename