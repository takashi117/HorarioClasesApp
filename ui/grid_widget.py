from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtGui import QColor
import random

class HorarioGrid(QTableWidget):
    def __init__(self):
        super().__init__()
        
        # Configuracion de dias y horas
        self.dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        self.hora_inicio = 7  # 7:00 AM
        self.hora_fin = 24    # 12:00 AM (00:00)
        
        # Calculamos cuantas filas de 30 minutos necesitamos
        # (24 - 7) * 2 = 30 bloques de media hora
        self.total_filas = (self.hora_fin - self.hora_inicio) * 2
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setColumnCount(len(self.dias))
        self.setRowCount(self.total_filas)
        
        self.setHorizontalHeaderLabels(self.dias)
        
        # Generar etiquetas verticales (07:00, 07:30, 08:00...)
        horas_labels = []
        for h in range(self.hora_inicio, self.hora_fin):
            horas_labels.append(f"{h:02d}:00")
            horas_labels.append(f"{h:02d}:30")
        self.setVerticalHeaderLabels(horas_labels)
        
        # Ajustes visuales
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Llenar ancho
        self.setEditTriggers(QAbstractItemView.NoEditTriggers) # No editable
        self.setSelectionMode(QAbstractItemView.NoSelection)   # No seleccionable
        self.setAlternatingRowColors(True)

    def limpiar(self):
        """Borra todos los bloques y resetea la tabla"""
        self.clearContents()
        self.clearSpans() 

    def pintar_bloque(self, nombre_materia, profesor, salon, dia_str, h_inicio_str, h_fin_str, color_hex=None):
        """
        Dibuja un bloque. Si ya existe uno, lo marca como CONFLICTO.
        """
        try:
            if dia_str not in self.dias: return 
            col = self.dias.index(dia_str)
            
            h_ini, m_ini = map(int, h_inicio_str.split(':'))
            row_start = (h_ini - self.hora_inicio) * 2
            if m_ini >= 30: row_start += 1
            
            h_fin, m_fin = map(int, h_fin_str.split(':'))
            row_end = (h_fin - self.hora_inicio) * 2
            if m_fin >= 30: row_end += 1
            
            duracion_filas = row_end - row_start
            if duracion_filas <= 0: return 

            # --- DETECCION DE CONFLICTOS ---
            # Verificamos si la celda inicial ya tiene un item
            item_existente = self.item(row_start, col)
            
            nuevo_texto = f"{nombre_materia}\n{profesor}\n({salon})"
            
            if item_existente:
                # YA EXISTE ALGO AQUI -> ES UN CHOQUE
                texto_actual = item_existente.text()
                
                # Evitar poner el mismo choque dos veces
                if "CONFLICTO" not in texto_actual:
                    texto_conflictivo = "CONFLICTO:\n" + texto_actual + "\nVS\n" + nuevo_texto
                else:
                    texto_conflictivo = texto_actual + "\nVS\n" + nuevo_texto
                
                # Actualizamos el item existente para mostrar el error
                item_existente.setText("CHOQUE")
                item_existente.setToolTip(texto_conflictivo) # Al pasar el mouse se ve el detalle
                item_existente.setBackground(QColor("#e74c3c")) # Rojo Alerta
                # No creamos item nuevo, usamos el espacio del anterior
                return

            # --- SI NO HAY CHOQUE, CREAMOS EL BLOQUE NORMAL ---
            item = QTableWidgetItem(nuevo_texto)
            item.setToolTip(f"{nombre_materia} con {profesor}") # Tooltip ayuda a leer si el bloque es chico
            
            if color_hex:
                item.setBackground(QColor(color_hex))
            else:
                item.setBackground(QColor("#3498db"))
                
            item.setForeground(QColor("white"))
            item.setTextAlignment(0x0084) # Alinear arriba y centro (Qt.AlignHCenter | Qt.AlignTop)
            
            self.setItem(row_start, col, item)
            if duracion_filas > 1:
                self.setSpan(row_start, col, duracion_filas, 1)
                
        except Exception as e:
            print(f"Error pintando bloque: {e}")

    def generar_color_random(self):
        """Genera colores pastel para las materias"""
        r = random.randint(100, 200)
        g = random.randint(100, 200)
        b = random.randint(150, 250)
        return f"#{r:02x}{g:02x}{b:02x}"