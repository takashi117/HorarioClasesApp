from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, 
                               QTabWidget, QFrame, QListWidget, QMessageBox, QListWidgetItem)
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
        self.lista_materias.itemDoubleClicked.connect(self.editar_materia_seleccionada)
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
        
        # Tab 2: Resultados
        self.tab_resultados = QWidget()
        layout_tab2 = QVBoxLayout(self.tab_resultados)
        
        # 1. Controles de Navegacion (Arriba)
        layout_nav = QHBoxLayout()
        
        self.btn_prev = QPushButton("<< Anterior")
        self.btn_prev.clicked.connect(self.mostrar_horario_anterior)
        self.btn_prev.setEnabled(False) # Desactivado al inicio
        
        self.lbl_contador = QLabel("0 / 0")
        self.lbl_contador.setAlignment(Qt.AlignCenter)
        self.lbl_contador.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.btn_next = QPushButton("Siguiente >>")
        self.btn_next.clicked.connect(self.mostrar_horario_siguiente)
        self.btn_next.setEnabled(False)
        
        layout_nav.addWidget(self.btn_prev)
        layout_nav.addWidget(self.lbl_contador)
        layout_nav.addWidget(self.btn_next)
        
        layout_tab2.addLayout(layout_nav)
        
        # 2. El Grid de Visualizacion (Igual que el de la pestana 1)
        self.grid_resultados = HorarioGrid()
        layout_tab2.addWidget(self.grid_resultados)
        
        # 3. Boton Exportar
        self.btn_exportar = QPushButton("Exportar este Horario (Imagen)")
        layout_tab2.addWidget(self.btn_exportar)
        
        self.tabs.addTab(self.tab_global, "Vista Global")
        self.tabs.addTab(self.tab_resultados, "Horarios Generados")
        
        layout_der.addWidget(self.tabs)
        
        layout_principal.addWidget(self.panel_izquierdo)
        layout_principal.addWidget(self.panel_derecho)

        # Cargar materias existentes al iniciar
        self.cargar_lista_materias()
        self.actualizar_vista_global()

        # Variables para los resultados
        self.resultados_generados = [] # Aqui guardaremos las combinaciones
        self.indice_actual = 0

        # Conectar el boton verde
        self.btn_generar.clicked.connect(self.ejecutar_generador)


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
        """Llena la lista visual (Ocultando el ID al usuario)"""
        self.lista_materias.clear()
        materias = database.obtener_todas_las_materias()
        
        contador = 1 # Contador visual
        for id_mat, nombre in materias:
            # Como ya importamos QListWidgetItem arriba, lo usamos directo
            item = QListWidgetItem(f"{contador}. {nombre}")
            
            # Guardamos el ID real en "UserRole" (secreto para el usuario, util para nosotros)
            item.setData(Qt.UserRole, id_mat) 
            
            self.lista_materias.addItem(item)
            contador += 1

    def eliminar_materia_seleccionada(self):
        # 1. Verificar si hay algo seleccionado
        item_actual = self.lista_materias.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Atencion", "Selecciona una materia de la lista para borrar.")
            return
            
        # 2. RECUPERAR EL ID OCULTO
        # Usamos .data(Qt.UserRole) porque el texto visual ya no tiene el ID real
        id_materia = item_actual.data(Qt.UserRole)
        nombre_para_mostrar = item_actual.text() 
        
        # 3. Preguntar confirmacion
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"Estas seguro de borrar la materia '{nombre_para_mostrar}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            # Pasamos el ID real a la base de datos
            if database.eliminar_materia(id_materia):
                # 4. Refrescar todo
                self.cargar_lista_materias()     # Actualiza la lista lateral
                self.actualizar_vista_global()   # Actualiza el Grid de colores (Ya descomentado)
                
                QMessageBox.information(self, "Listo", "Materia eliminada.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar.")

    def cargar_datos_para_motor(self):
        """
        Lee la BD y convierte los datos crudos en objetos para engine.py
        Agrupa materias por NOMBRE exacto.
        """
        import engine # Importamos aqui para usar sus clases
        
        conn = database.crear_conexion()
        if not conn: return []
        
        cursor = conn.cursor()
        
        # Traemos TODO: Materia, Opcion y Bloques
        query = """
            SELECT m.nombre, o.id, o.profesor, o.salon, b.dia, b.hora_inicio, b.hora_fin
            FROM bloques b
            JOIN opciones o ON b.opcion_id = o.id
            JOIN materias m ON o.materia_id = m.id
        """
        cursor.execute(query)
        filas = cursor.fetchall()
        conn.close()
        
        # Diccionario temporal para agrupar:
        # { "Calculo": { 
        #       id_opcion_1: {profesor: "X", bloques: [...]},
        #       id_opcion_2: {profesor: "Y", bloques: [...]} 
        #   } 
        # }
        agrupacion = {}
        
        for nombre, id_opcion, prof, salon, dia, inicio, fin in filas:
            if nombre not in agrupacion:
                agrupacion[nombre] = {}
            
            if id_opcion not in agrupacion[nombre]:
                agrupacion[nombre][id_opcion] = {
                    "profesor": prof,
                    "salon": salon,
                    "bloques_obj": []
                }
            
            # Convertimos horas texto ("07:00") a minutos (420) para el motor
            min_inicio = engine.convertir_hora_a_minutos(inicio)
            min_fin = engine.convertir_hora_a_minutos(fin)
            
            nuevo_bloque = engine.Bloque(dia, min_inicio, min_fin)
            agrupacion[nombre][id_opcion]["bloques_obj"].append(nuevo_bloque)
            
        # Ahora convertimos ese diccionario raro en Lista de objetos Materia
        lista_materias_motor = []
        id_falso_materia = 1
        
        for nombre_mat, opciones_dict in agrupacion.items():
            lista_opciones_obj = []
            
            for id_op, info in opciones_dict.items():
                # Creamos el objeto Opcion
                op_obj = engine.Opcion(
                    id_opcion=id_op,
                    nombre_materia=nombre_mat,
                    profesor=info['profesor'],
                    salon=info['salon'],
                    bloques=info['bloques_obj']
                )
                lista_opciones_obj.append(op_obj)
            
            # Creamos el objeto Materia con todas sus opciones
            mat_obj = engine.Materia(id_falso_materia, nombre_mat, lista_opciones_obj)
            lista_materias_motor.append(mat_obj)
            id_falso_materia += 1
            
        return lista_materias_motor

    def actualizar_vista_global(self):
        """Lee TODAS las materias y las pinta."""
        self.grid_global.limpiar()
        conn = database.crear_conexion()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # AHORA PEDIMOS TAMBIEN PROFESOR Y SALON
            query = """
                SELECT m.nombre, o.profesor, o.salon, b.dia, b.hora_inicio, b.hora_fin
                FROM bloques b
                JOIN opciones o ON b.opcion_id = o.id
                JOIN materias m ON o.materia_id = m.id
            """
            cursor.execute(query)
            filas = cursor.fetchall()
            
            colores_materias = {}
            
            # Desempaquetamos los 6 valores
            for nombre, prof, salon, dia, inicio, fin in filas:
                if nombre not in colores_materias:
                    colores_materias[nombre] = self.grid_global.generar_color_random()
                
                # Pasamos todos los datos al grid
                self.grid_global.pintar_bloque(nombre, prof, salon, dia, inicio, fin, colores_materias[nombre])
                
        except Exception as e:
            print(f"Error al leer datos para el grid: {e}")
        finally:
            conn.close()

    def editar_materia_seleccionada(self, item):
        """Se ejecuta al dar doble click en la lista"""
        # 1. Recuperar ID oculto
        id_materia = item.data(Qt.UserRole)
        
        # 2. Obtener datos de la BD
        datos_actuales = database.obtener_materia_por_id(id_materia)
        if not datos_actuales:
            return

        # 3. Abrir dialogo pre-llenado
        dialogo = DialogoMateria(self)
        dialogo.cargar_datos_para_editar(datos_actuales)
        
        if dialogo.exec():
            # 4. Si el usuario guarda, actualizamos
            nuevos_datos = dialogo.obtener_datos()
            
            # Usamos la estrategia de Borrar + Insertar
            if database.actualizar_materia_existente(id_materia, nuevos_datos):
                self.cargar_lista_materias()
                self.actualizar_vista_global()
                QMessageBox.information(self, "Exito", "Materia actualizada correctamente.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar.")

    def ejecutar_generador(self):
        import engine
        
        # 1. Cargar datos
        materias_motor = self.cargar_datos_para_motor()
        if not materias_motor:
            QMessageBox.warning(self, "Vacio", "No hay materias registradas.")
            return

        # 2. Ejecutar algoritmo (Backtracking)
        self.resultados_generados = engine.generar_combinaciones(materias_motor)
        
        # 3. Mostrar resultados
        cant = len(self.resultados_generados)
        if cant == 0:
            QMessageBox.warning(self, "Ups", "No hay combinaciones posibles sin choques.\nIntenta quitar materias o buscar otros horarios.")
            self.lbl_contador.setText("0 / 0")
            self.grid_resultados.limpiar()
            return
        
        QMessageBox.information(self, "Exito", f"Se encontraron {cant} combinaciones posibles.")
        
        # Cambiar a la pestana de resultados
        self.tabs.setCurrentIndex(1)
        self.indice_actual = 0
        self.mostrar_resultado_actual()

    def mostrar_resultado_actual(self):
        """Pinta el horario segun el indice_actual"""
        if not self.resultados_generados: return
        
        combinacion = self.resultados_generados[self.indice_actual]
        
        total = len(self.resultados_generados)
        self.lbl_contador.setText(f"Opcion {self.indice_actual + 1} de {total}")
        
        self.btn_prev.setEnabled(self.indice_actual > 0)
        self.btn_next.setEnabled(self.indice_actual < total - 1)
        
        self.grid_resultados.limpiar()
        import engine 
        
        # Mapa de colores para mantener consistencia visual
        colores_por_materia = {}

        for opcion in combinacion:
            # Asignar color consistente basado en el nombre de la materia
            if opcion.nombre_materia not in colores_por_materia:
                colores_por_materia[opcion.nombre_materia] = self.grid_resultados.generar_color_random()
            
            color = colores_por_materia[opcion.nombre_materia]
            
            for bloque in opcion.bloques:
                inicio_str = engine.minutos_a_hora(bloque.hora_inicio)
                fin_str = engine.minutos_a_hora(bloque.hora_fin)
                
                # --- CORRECCION VISUAL ---
                # Ahora pasamos los datos limpios. El Grid se encarga de ponerlos bonitos.
                # Ya no mandamos f"Materia\n{Juan}" sino el nombre real.
                
                self.grid_resultados.pintar_bloque(
                    opcion.nombre_materia, # Ej: "Ingles"
                    opcion.profesor,       # Ej: "Pedro"
                    opcion.salon,          # Ej: "B002"
                    bloque.dia, 
                    inicio_str, 
                    fin_str, 
                    color
                )

    def mostrar_horario_siguiente(self):
        if self.indice_actual < len(self.resultados_generados) - 1:
            self.indice_actual += 1
            self.mostrar_resultado_actual()

    def mostrar_horario_anterior(self):
        if self.indice_actual > 0:
            self.indice_actual -= 1
            self.mostrar_resultado_actual()

    