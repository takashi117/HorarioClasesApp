from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QTimeEdit, 
                               QComboBox, QPushButton, QGroupBox, 
                               QListWidget, QMessageBox)
from PySide6.QtCore import QTime, Qt

class DialogoMateria(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Materia - Horarios Multiples")
        self.setFixedWidth(500) # Un poco mas ancho
        self.bloques_temporales = [] # Aqui guardaremos los horarios antes de guardar en BD
        self.opcion_id = None
        
        layout = QVBoxLayout(self)
        
        # --- 1. Datos Basicos ---
        grupo_datos = QGroupBox("Datos de la Materia")
        layout_datos = QVBoxLayout(grupo_datos)
        
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre de la materia")
        layout_datos.addWidget(QLabel("Nombre:"))
        layout_datos.addWidget(self.input_nombre)
        
        layout_fila2 = QHBoxLayout()
        
        self.input_profesor = QLineEdit()
        self.input_profesor.setText("Profesor Pendiente") # Valor por defecto solicitado
        layout_fila2.addWidget(QLabel("Profesor:"))
        layout_fila2.addWidget(self.input_profesor)
        
        self.input_salon = QLineEdit()
        self.input_salon.setPlaceholderText("Salon")
        layout_fila2.addWidget(QLabel("Salon:"))
        layout_fila2.addWidget(self.input_salon)
        
        layout_datos.addLayout(layout_fila2)
        layout.addWidget(grupo_datos)
        
        # --- 2. Constructor de Horarios ---
        grupo_horario = QGroupBox("Agregar Bloques de Horario")
        layout_horario = QHBoxLayout(grupo_horario)
        
        # Selector de Dia
        self.combo_dias = QComboBox()
        self.combo_dias.addItems(["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"])
        layout_horario.addWidget(self.combo_dias)
        
        # Selector de Horas
        self.time_inicio = QTimeEdit()
        self.time_inicio.setDisplayFormat("HH:mm")
        self.time_inicio.setTime(QTime(7, 0))
        layout_horario.addWidget(self.time_inicio)
        
        layout_horario.addWidget(QLabel("a"))
        
        self.time_fin = QTimeEdit()
        self.time_fin.setDisplayFormat("HH:mm")
        self.time_fin.setTime(QTime(9, 0))
        layout_horario.addWidget(self.time_fin)
        
        # Boton Agregar Bloque (+)
        self.btn_mas = QPushButton(" + ")
        self.btn_mas.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.btn_mas.clicked.connect(self.agregar_bloque_a_lista)
        layout_horario.addWidget(self.btn_mas)
        
        layout.addWidget(grupo_horario)
        
        # --- 3. Lista Visual de Horarios ---
        self.lista_horarios = QListWidget()
        self.lista_horarios.setFixedHeight(100) # Que no ocupe mucho espacio
        layout.addWidget(QLabel("Horarios Agregados:"))
        layout.addWidget(self.lista_horarios)
        
        # Boton para borrar bloque de la lista (por si se equivoca)
        self.btn_borrar_bloque = QPushButton("Quitar Horario Seleccionado")
        self.btn_borrar_bloque.clicked.connect(self.borrar_bloque_lista)
        layout.addWidget(self.btn_borrar_bloque)
        
        # --- 4. Botones Finales ---
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar Materia")
        self.btn_guardar.clicked.connect(self.validar_y_guardar)
        self.btn_guardar.setStyleSheet("padding: 8px;")
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar)
        
        layout.addLayout(btn_layout)

    def agregar_bloque_a_lista(self):
        """Toma los datos de los spinners y los agrega a la lista temporal."""
        dia = self.combo_dias.currentText()
        inicio = self.time_inicio.time().toString("HH:mm")
        fin = self.time_fin.time().toString("HH:mm")
        
        # Validacion simple: Inicio debe ser antes que fin
        if self.time_inicio.time() >= self.time_fin.time():
            QMessageBox.warning(self, "Error", "La hora de inicio debe ser menor a la final.")
            return

        # Guardamos en memoria
        bloque = {'dia': dia, 'inicio': inicio, 'fin': fin}
        self.bloques_temporales.append(bloque)
        
        # Mostramos en la lista visual
        texto_item = f"{dia}: {inicio} - {fin}"
        self.lista_horarios.addItem(texto_item)

    def borrar_bloque_lista(self):
        fila = self.lista_horarios.currentRow()
        if fila >= 0:
            self.lista_horarios.takeItem(fila) # Borrar de la vista
            del self.bloques_temporales[fila]  # Borrar de la memoria
            
    def validar_y_guardar(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return

        if not self.bloques_temporales:
            QMessageBox.warning(self, "Error", "Debes agregar al menos un horario con el boton (+).")
            return
            
        self.accept()

    def cargar_datos_para_editar(self, datos):
        """Rellena el formulario con datos existentes"""
        self.setWindowTitle("Editar Materia")
        self.btn_guardar.setText("Actualizar Materia")
        self.opcion_id = datos.get('opcion_id')
        
        # 1. Textos
        self.input_nombre.setText(datos['nombre'])
        self.input_profesor.setText(datos['profesor'])
        self.input_salon.setText(datos['salon'])
        
        # 2. Reconstruir lista de bloques
        self.bloques_temporales = datos['bloques'] # Copiamos la lista
        self.lista_horarios.clear()
        
        for bloque in self.bloques_temporales:
            texto = f"{bloque['dia']}: {bloque['inicio']} - {bloque['fin']}"
            self.lista_horarios.addItem(texto)

    def obtener_datos(self):
        return {
            "nombre": self.input_nombre.text(),
            "profesor": self.input_profesor.text(),
            "salon": self.input_salon.text(),
            "bloques": self.bloques_temporales, # Enviamos la lista completa
            "opcion_id": self.opcion_id
        }