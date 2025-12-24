from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, 
                               QTabWidget, QFrame, QListWidget, QMessageBox)
from PySide6.QtCore import Qt
from ui.dialogs import DialogoMateria
from ui.grid_widget import HorarioGrid
import database # Importamos nuestro modulo de base de datos

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("UniScheduler Pro - Gestor de Horarios")
        self.resize(1000, 700) # Tamano inicial
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout_principal = QHBoxLayout(central_widget)
        
        # --- Panel Izquierdo ---
        self.panel_izquierdo = QFrame()
        self.panel_izquierdo.setFrameShape(QFrame.StyledPanel)
        self.panel_izquierdo.setFixedWidth(300)
        
        layout_izq = QVBoxLayout(self.panel_izquierdo)
        
        layout_izq.addWidget(QLabel("<b>Mis Materias</b>"))
        
        # LISTA DE MATERIAS (Nuevo Widget)
        self.lista_materias = QListWidget()
        layout_izq.addWidget(self.lista_materias)
        
        # Botones
        self.btn_borrar = QPushButton("Eliminar Seleccionada")
        self.btn_borrar.setStyleSheet("background-color: #ffcccc; color: red;") # Un poco rojo para alerta
        self.btn_borrar.clicked.connect(self.eliminar_materia_seleccionada)
        layout_izq.addWidget(self.btn_borrar)

        self.btn_agregar = QPushButton("Agregar Nueva Materia")
        self.btn_agregar.setStyleSheet("padding: 8px; font-weight: bold;")
        self.btn_agregar.clicked.connect(self.abrir_dialogo_agregar)
        layout_izq.addWidget(self.btn_agregar)
        
        self.btn_generar = QPushButton("Generar Horarios")
        self.btn_generar.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        layout_izq.addWidget(self.btn_generar)
        
        # --- Panel Derecho ---
        self.panel_derecho = QWidget()
        layout_der = QVBoxLayout(self.panel_derecho)
        
        self.tabs = QTabWidget()
        
        # --- PEGAR ESTO ---
        self.tab_global = QWidget()
        layout_tab1 = QVBoxLayout(self.tab_global)

        # Creamos el Grid y lo guardamos en self.grid_global para usarlo luego
        self.grid_global = HorarioGrid() 
        layout_tab1.addWidget(self.grid_global)
        # ------------------
        
        self.tab_resultados = QWidget()
        lbl_res = QLabel("Aqui apareceran las combinaciones generadas por el motor")
        lbl_res.setAlignment(Qt.AlignCenter)
        layout_tab2 = QVBoxLayout(self.tab_resultados)
        layout_tab2.addWidget(lbl_res)
        
        self.tabs.addTab(self.tab_global, "Vista Global")
        self.tabs.addTab(self.tab_resultados, "Horarios Generados")
        
        layout_der.addWidget(self.tabs)
        
        layout_principal.addWidget(self.panel_izquierdo)
        layout_principal.addWidget(self.panel_derecho)

        # Cargar materias existentes al iniciar
        self.cargar_lista_materias()
        self.actualizar_vista_global()

    def abrir_dialogo_agregar(self):
        dialogo = DialogoMateria(self)
        if dialogo.exec(): 
            datos = dialogo.obtener_datos()
            # Guardar en Base de Datos
            if database.insertar_materia_completa(datos):
                self.cargar_lista_materias() # Actualizar la lista visual
                self.actualizar_vista_global()
                QMessageBox.information(self, "Exito", "Materia guardada correctamente")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar la materia")

    def cargar_lista_materias(self):
        """Consulta la BD y llena la lista visual"""
        self.lista_materias.clear()
        materias = database.obtener_todas_las_materias()
        for id_mat, nombre in materias:
            self.lista_materias.addItem(f"{id_mat} - {nombre}")

    def eliminar_materia_seleccionada(self):
        # 1. Verificar si hay algo seleccionado
        item_actual = self.lista_materias.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Atencion", "Selecciona una materia de la lista para borrar.")
            return
            
        # 2. Obtener el ID del texto (Ej: "1 - Matematicas")
        texto = item_actual.text()
        id_materia = texto.split(' - ')[0] # Tomamos lo que esta antes del guion
        
        # 3. Preguntar confirmacion (Buena practica de UX)
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"Estas seguro de borrar la materia {id_materia}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            if database.eliminar_materia(id_materia):
                # 4. Refrescar todo
                self.cargar_lista_materias()
                
                # Si ya tienes implementado el grid del paso anterior, descomenta esto:
                self.actualizar_vista_global() 
                
                QMessageBox.information(self, "Listo", "Materia eliminada.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar.")

    def actualizar_vista_global(self):
        """Lee TODAS las materias de la BD y las pinta en el grid global"""
        self.grid_global.limpiar()
        conn = database.crear_conexion()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Obtenemos Materia, Dia y Horas uniendo las 3 tablas
            query = """
                SELECT m.nombre, b.dia, b.hora_inicio, b.hora_fin
                FROM bloques b
                JOIN opciones o ON b.opcion_id = o.id
                JOIN materias m ON o.materia_id = m.id
            """
            cursor.execute(query)
            filas = cursor.fetchall()
            
            # Diccionario para recordar el color de cada materia
            colores_materias = {}
            
            for nombre, dia, inicio, fin in filas:
                if nombre not in colores_materias:
                    colores_materias[nombre] = self.grid_global.generar_color_random()
                
                # Usamos la funcion del grid para pintar
                self.grid_global.pintar_bloque(nombre, dia, inicio, fin, colores_materias[nombre])
                
        except Exception as e:
            print(f"Error al leer datos para el grid: {e}")
        finally:
            conn.close()

    