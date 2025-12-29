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
        self.indice_opcion_seleccionada = None
        self.opciones = []
        
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

        layout_datos.addLayout(layout_fila2)
        layout.addWidget(grupo_datos)

        # --- 2. Constructor de Horarios ---
        grupo_horario = QGroupBox("Agregar Bloques de Horario")
        layout_horario = QHBoxLayout(grupo_horario)

        # Selector de Dia
        self.combo_dias = QComboBox()
        self.combo_dias.addItems(["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"])
        layout_horario.addWidget(self.combo_dias)

        self.input_salon_bloque = QLineEdit()
        self.input_salon_bloque.setPlaceholderText("Salon del bloque")
        self.input_salon_bloque.setFixedWidth(110)
        layout_horario.addWidget(self.input_salon_bloque)
        
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

        # --- 3.1. Lista de Alternativas ---
        grupo_opciones = QGroupBox("Alternativas guardadas para esta materia")
        layout_opciones = QVBoxLayout(grupo_opciones)

        self.lista_opciones = QListWidget()
        self.lista_opciones.setFixedHeight(120)
        self.lista_opciones.currentRowChanged.connect(self.cargar_opcion_desde_lista)

        layout_opciones.addWidget(self.lista_opciones)

        botones_opciones = QHBoxLayout()
        self.btn_guardar_opcion = QPushButton("Guardar/Actualizar alternativa")
        self.btn_guardar_opcion.clicked.connect(self.guardar_o_actualizar_opcion)

        self.btn_nueva_opcion = QPushButton("Nueva alternativa")
        self.btn_nueva_opcion.clicked.connect(self.preparar_nueva_opcion)

        self.btn_eliminar_opcion = QPushButton("Eliminar alternativa seleccionada")
        self.btn_eliminar_opcion.clicked.connect(self.eliminar_opcion_seleccionada)

        botones_opciones.addWidget(self.btn_guardar_opcion)
        botones_opciones.addWidget(self.btn_nueva_opcion)
        botones_opciones.addWidget(self.btn_eliminar_opcion)

        layout_opciones.addLayout(botones_opciones)
        layout.addWidget(grupo_opciones)
        
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
        salon = self.input_salon_bloque.text().strip()

        # Validacion simple: Inicio debe ser antes que fin
        if self.time_inicio.time() >= self.time_fin.time():
            QMessageBox.warning(self, "Error", "La hora de inicio debe ser menor a la final.")
            return

        # Guardamos en memoria
        bloque = {'dia': dia, 'inicio': inicio, 'fin': fin, 'salon': salon}
        self.bloques_temporales.append(bloque)

        # Mostramos en la lista visual
        texto_salon = salon if salon else "Salon sin definir"
        texto_item = f"{dia}: {inicio} - {fin} ({texto_salon})"
        self.lista_horarios.addItem(texto_item)

    def borrar_bloque_lista(self):
        fila = self.lista_horarios.currentRow()
        if fila >= 0:
            self.lista_horarios.takeItem(fila) # Borrar de la vista
            del self.bloques_temporales[fila]  # Borrar de la memoria

    def validar_y_guardar(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return

        # Garantizamos que la opcion en edicion quede guardada
        if not self.opciones:
            if not self.guardar_o_actualizar_opcion():
                return
        elif self.bloques_temporales and self.indice_opcion_seleccionada is not None:
            if not self.guardar_o_actualizar_opcion():
                return

        if not self.opciones:
            QMessageBox.warning(self, "Error", "Debes agregar al menos una alternativa.")
            return

        self.accept()

    def cargar_datos_para_editar(self, datos):
        """Rellena el formulario con datos existentes"""
        self.setWindowTitle("Editar Materia")
        self.btn_guardar.setText("Actualizar Materia")
        self.input_nombre.setText(datos['nombre'])
        self.opciones = datos.get('opciones', [])

        self.lista_opciones.clear()
        for idx, opcion in enumerate(self.opciones):
            texto = self._texto_opcion(opcion, idx)
            self.lista_opciones.addItem(texto)

        if self.opciones:
            self.lista_opciones.setCurrentRow(0)
            self.cargar_opcion_desde_lista(0)
        else:
            self.preparar_nueva_opcion()

    def obtener_datos(self):
        return {
            "nombre": self.input_nombre.text(),
            "opciones": self.opciones
        }

    # --- Manejo de alternativas ---
    def preparar_nueva_opcion(self):
        self.indice_opcion_seleccionada = None
        self.opcion_id = None
        self.input_profesor.setText("Profesor Pendiente")
        self.input_salon_bloque.clear()
        self.bloques_temporales = []
        self.lista_horarios.clear()
        self.lista_opciones.clearSelection()

    def cargar_opcion_desde_lista(self, indice):
        if indice is None or indice < 0 or indice >= len(self.opciones):
            return

        opcion = self.opciones[indice]
        self.indice_opcion_seleccionada = indice
        self.opcion_id = opcion.get('id')
        self.input_profesor.setText(opcion.get('profesor', ''))

        self.bloques_temporales = opcion.get('bloques', [])
        self.lista_horarios.clear()
        for bloque in self.bloques_temporales:
            texto_salon = bloque.get('salon') or "Salon sin definir"
            texto = f"{bloque['dia']}: {bloque['inicio']} - {bloque['fin']} ({texto_salon})"
            self.lista_horarios.addItem(texto)

    def guardar_o_actualizar_opcion(self):
        if not self.bloques_temporales:
            QMessageBox.warning(self, "Error", "Debes agregar al menos un horario con el boton (+).")
            return False

        opcion_data = {
            "id": self.opcion_id,
            "profesor": self.input_profesor.text(),
            "bloques": list(self.bloques_temporales)
        }

        if self.indice_opcion_seleccionada is None:
            self.opciones.append(opcion_data)
            row = self.lista_opciones.count()
            self.lista_opciones.addItem(self._texto_opcion(opcion_data, row))
            self.lista_opciones.setCurrentRow(row)
            self.indice_opcion_seleccionada = row
        else:
            self.opciones[self.indice_opcion_seleccionada] = opcion_data
            self.lista_opciones.item(self.indice_opcion_seleccionada).setText(
                self._texto_opcion(opcion_data, self.indice_opcion_seleccionada)
            )

        return True

    def eliminar_opcion_seleccionada(self):
        fila = self.lista_opciones.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atencion", "Selecciona una alternativa para eliminar.")
            return

        self.lista_opciones.takeItem(fila)
        del self.opciones[fila]

        if self.opciones:
            nuevo_indice = min(fila, len(self.opciones) - 1)
            self.lista_opciones.setCurrentRow(nuevo_indice)
            self.cargar_opcion_desde_lista(nuevo_indice)
        else:
            self.preparar_nueva_opcion()

    def _texto_opcion(self, opcion, indice):
        profesor = opcion.get('profesor', '').strip() or 'Profesor Pendiente'
        bloques = opcion.get('bloques', [])
        return f"Alternativa {indice + 1}: {profesor} ({len(bloques)} bloques)"