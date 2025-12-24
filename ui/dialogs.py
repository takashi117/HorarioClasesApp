from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QTimeEdit, 
                               QCheckBox, QPushButton, QGroupBox, QMessageBox)
from PySide6.QtCore import QTime

class DialogoMateria(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Materia")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        
        # --- 1. Datos Basicos ---
        grupo_datos = QGroupBox("Informacion de la Materia")
        layout_datos = QVBoxLayout(grupo_datos)
        
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Calculo Integral")
        layout_datos.addWidget(QLabel("Nombre de la Materia:"))
        layout_datos.addWidget(self.input_nombre)
        
        self.input_profesor = QLineEdit()
        self.input_profesor.setPlaceholderText("Ej: Dr. Garcia")
        layout_datos.addWidget(QLabel("Profesor:"))
        layout_datos.addWidget(self.input_profesor)
        
        self.input_salon = QLineEdit()
        self.input_salon.setPlaceholderText("Ej: A-101")
        layout_datos.addWidget(QLabel("Salon:"))
        layout_datos.addWidget(self.input_salon)
        
        layout.addWidget(grupo_datos)
        
        # --- 2. Seleccion de Dias (Checklist) ---
        grupo_dias = QGroupBox("Dias de Clase")
        layout_dias = QHBoxLayout(grupo_dias)
        
        self.dias_checks = []
        dias_nombres = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab"]
        
        for nombre in dias_nombres:
            chk = QCheckBox(nombre)
            self.dias_checks.append(chk)
            layout_dias.addWidget(chk)
            
        layout.addWidget(grupo_dias)
        
        # --- 3. Seleccion de Horas ---
        grupo_horas = QGroupBox("Horario")
        layout_horas = QHBoxLayout(grupo_horas)
        
        self.time_inicio = QTimeEdit()
        self.time_inicio.setDisplayFormat("HH:mm")
        self.time_inicio.setTime(QTime(7, 0)) # Default 7:00 AM
        
        self.time_fin = QTimeEdit()
        self.time_fin.setDisplayFormat("HH:mm")
        self.time_fin.setTime(QTime(9, 0)) # Default 9:00 AM
        
        layout_horas.addWidget(QLabel("De:"))
        layout_horas.addWidget(self.time_inicio)
        layout_horas.addWidget(QLabel("A:"))
        layout_horas.addWidget(self.time_fin)
        
        layout.addWidget(grupo_horas)
        
        # --- 4. Botones ---
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self.validar_y_guardar) # Conectar funcion
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar)
        
        layout.addLayout(btn_layout)

    def validar_y_guardar(self):
        # Validacion simple
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre de la materia es obligatorio.")
            return

        # Verificar que al menos un dia este marcado
        dias_seleccionados = [chk.text() for chk in self.dias_checks if chk.isChecked()]
        if not dias_seleccionados:
            QMessageBox.warning(self, "Error", "Debes seleccionar al menos un dia.")
            return
            
        # Si todo esta bien, aceptamos el dialogo
        # Aqui mas adelante guardaremos en la Base de Datos
        self.accept()
    
    def obtener_datos(self):
        """Retorna un diccionario con los datos del formulario"""
        return {
            "nombre": self.input_nombre.text(),
            "profesor": self.input_profesor.text(),
            "salon": self.input_salon.text(),
            "dias": [chk.text() for chk in self.dias_checks if chk.isChecked()],
            "inicio": self.time_inicio.time().toString("HH:mm"),
            "fin": self.time_fin.time().toString("HH:mm")
        }