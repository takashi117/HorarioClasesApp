from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt 
import random

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
        self.setColumnCount(len(self.dias))
        self.setRowCount(self.total_filas)
        self.setHorizontalHeaderLabels(self.dias)
        
        horas_labels = []
        for h in range(self.hora_inicio, self.hora_fin):
            horas_labels.append(f"{h:02d}:00")
            horas_labels.append(f"{h:02d}:30")
        self.setVerticalHeaderLabels(horas_labels)
        
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setAlternatingRowColors(True)

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