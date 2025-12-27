from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtGui import QColor, QPainter, QFont, QPen
from PySide6.QtCore import Qt, QRect
import random

class HeaderRegla(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)
        
    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        
        # 1. Limpiar Fondo (Evita basura visual)
        painter.fillRect(self.viewport().rect(), QColor("#333333"))
        
        # 2. Linea Vertical Derecha
        pen_borde = QPen(QColor("#555555"))
        pen_borde.setWidth(1)
        painter.setPen(pen_borde)
        
        width = self.viewport().width()
        height = self.viewport().height()
        painter.drawLine(width - 1, 0, width - 1, height)
        
        # 3. Configurar Fuente
        painter.setPen(Qt.white)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        
        # 4. Dibujar Horas
        count = self.count()
        hora_inicio_grid = 7 
        
        for i in range(count):
            y = self.sectionViewportPosition(i)
            h = self.sectionSize(i)
            rect = QRect(0, y, width, h)
            
            # Optimizacion de visibilidad
            if rect.bottom() < 0 or rect.top() > height:
                continue
                
            minutos_inicio = (hora_inicio_grid * 60) + (i * 30)
            h_val = minutos_inicio // 60
            m_val = minutos_inicio % 60
            texto = f"{h_val:02d}:{m_val:02d}"
            
            # A) Primera Hora (07:00) -> Pegada al TOPE (Adentro)
            if i == 0:
                rect_texto = QRect(0, rect.top(), width - 5, 20)
                painter.drawText(rect_texto, Qt.AlignRight | Qt.AlignTop, texto)
            
            # B) Resto de horas -> Centradas en la LINEA SUPERIOR
            else:
                rect_texto = QRect(0, rect.top() - 10, width - 5, 20)
                painter.drawText(rect_texto, Qt.AlignRight | Qt.AlignVCenter, texto)
            
            # C) Hora Final (24:00) -> Pegada al PISO (Adentro)
            # CORRECCION: En lugar de centrar en la linea (que la corta),
            # la dibujamos pegada al fondo de la celda, igual que la primera.
            if i == count - 1:
                min_fin = minutos_inicio + 30
                h_f = min_fin // 60
                m_f = min_fin % 60
                texto_fin = f"{h_f:02d}:{m_f:02d}"
                
                # Usamos rect.bottom() - 20 para definir el area dentro de la celda
                rect_fin = QRect(0, rect.bottom() - 20, width - 5, 20)
                painter.drawText(rect_fin, Qt.AlignRight | Qt.AlignBottom, texto_fin)

class HorarioGrid(QTableWidget):
    def __init__(self):
        super().__init__()
        
        self.dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        self.hora_inicio = 7
        self.hora_fin = 24 # Hasta media noche
        self.total_filas = (self.hora_fin - self.hora_inicio) * 2
        
        # --- MEMORIA LOGICA ---
        # Diccionario para saber quien ocupa que celda realmente
        self.celdas_ocupadas = {} 
        
        self.setup_ui()
        
    def setup_ui(self):
        # 1. Dimensiones de la tabla
        self.setColumnCount(len(self.dias))
        self.setRowCount(self.total_filas)
        
        # 2. Encabezados Horizontales (Dias)
        self.setHorizontalHeaderLabels(self.dias)
        
        # 3. Encabezados Verticales (Horas)
        # Generamos etiquetas base. Aunque HeaderRegla hace su propio calculo visual,
        # es importante setear esto para que la tabla tenga la estructura correcta.
        horas_labels = []
        for h in range(self.hora_inicio, self.hora_fin):
            horas_labels.append(f"{h:02d}:00")
            horas_labels.append(f"{h:02d}:30")
            
        # Nos aseguramos que la lista de etiquetas coincida con las filas totales
        if len(horas_labels) > self.total_filas:
            horas_labels = horas_labels[:self.total_filas]
            
        self.setVerticalHeaderLabels(horas_labels)
        
        # 4. Ajustes Visuales y de Comportamiento
        # Estirar columnas para llenar el espacio
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Desactivar edicion y seleccion para que sea solo visual
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        # Filas con colores alternados (Zebrastripe) para guiar el ojo
        self.setAlternatingRowColors(True)

        # 5. ACTIVAR EL HEADER PERSONALIZADO (El "Eje de Tiempo")
        # Instanciamos la clase que dibuja en el "techo" de la celda
        self.header_regla = HeaderRegla(self)
        
        # Reemplazamos el header por defecto con el nuestro
        self.setVerticalHeader(self.header_regla)
        
        # Fijamos un ancho de 50px para que los numeros quepan bien
        self.verticalHeader().setFixedWidth(50)

        self.verticalScrollBar().valueChanged.connect(self.verticalHeader().viewport().update)

    def limpiar(self):
        """Borra todo, incluyendo la memoria logica."""
        self.clearContents()
        self.clearSpans()
        self.celdas_ocupadas = {} 

    def pintar_bloque(self, nombre_materia, profesor, salon, dia_str, h_inicio_str, h_fin_str, color_hex=None):
        try:
            if dia_str not in self.dias: return 
            col = self.dias.index(dia_str)
            
            # Calculo de filas
            h_ini, m_ini = map(int, h_inicio_str.split(':'))
            row_start = (h_ini - self.hora_inicio) * 2
            if m_ini >= 30: row_start += 1
            
            h_fin, m_fin = map(int, h_fin_str.split(':'))
            row_end = (h_fin - self.hora_inicio) * 2
            if m_fin >= 30: row_end += 1
            
            duracion_filas = row_end - row_start
            if duracion_filas <= 0: return 

            # --- DETECCION DE CONFLICTOS ---
            item_conflicto = None
            for r in range(row_start, row_end):
                if (r, col) in self.celdas_ocupadas:
                    item_conflicto = self.celdas_ocupadas[(r, col)]
                    break
            
            nuevo_texto = f"{nombre_materia}\n{profesor}\n({salon})"

            if item_conflicto:
                # --- LOGICA DE LISTA NUMERADA ---
                # 1. Recuperamos la lista de materias que ya estan en ese bloque
                lista_materias = item_conflicto.data(Qt.UserRole)
                
                if not lista_materias:
                    # Si el bloque era normal y es su primer choque, quizas no tenia lista aun.
                    # Creamos la lista usando el texto que ya tenia.
                    lista_materias = [item_conflicto.text()]

                # 2. Agregamos la nueva materia a la lista
                lista_materias.append(nuevo_texto)
                
                # 3. Guardamos la lista actualizada
                item_conflicto.setData(Qt.UserRole, lista_materias)
                
                # 4. Reconstruimos el Tooltip numerado desde cero
                tooltip_construido = "!!! CONFLICTO DETECTADO !!!"
                for i, materia in enumerate(lista_materias):
                    # i+1 genera los numeros 1, 2, 3...
                    tooltip_construido += f"\n\n{i+1}. {materia}"
                
                # 5. Actualizamos visualmente
                item_conflicto.setToolTip(tooltip_construido)
                item_conflicto.setText("!!! CHOQUE MULTIPLE\n(Ver detalles)")
                item_conflicto.setBackground(QColor("#e74c3c")) # Rojo
                
                return # Salimos para no pintar encima

            # --- SI NO HAY CHOQUE ---
            item = QTableWidgetItem(nuevo_texto)
            item.setToolTip(f"{nombre_materia}\n{profesor}\n{salon}")
            
            # Guardamos este texto en la lista interna para estar listos por si alguien choca despues
            item.setData(Qt.UserRole, [nuevo_texto]) 
            
            if color_hex:
                item.setBackground(QColor(color_hex))
            else:
                item.setBackground(QColor("#3498db"))
                
            item.setForeground(QColor("white"))
            item.setTextAlignment(0x0084) 
            
            self.setItem(row_start, col, item)
            if duracion_filas > 1:
                self.setSpan(row_start, col, duracion_filas, 1)
            
            # Registrar propiedad del espacio
            for r in range(row_start, row_end):
                self.celdas_ocupadas[(r, col)] = item
                
        except Exception as e:
            print(f"Error pintando bloque: {e}")

    def generar_color_random(self):
        r = random.randint(100, 200)
        g = random.randint(100, 200)
        b = random.randint(150, 250)
        return f"#{r:02x}{g:02x}{b:02x}"