from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, 
                               QTabWidget, QFrame, QListWidget, QMessageBox,
                               QListWidgetItem, QFileDialog)

from PySide6.QtGui import QPixmap, QPainter, QRegion
from PySide6.QtCore import Qt, QPoint, QSize, QRect

from ui.dialogs import DialogoMateria
from ui.grid_widget import HorarioGrid
import database

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("UniScheduler Pro - Gestor de Horarios")
        self.resize(1100, 750) 
        
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
        
        # Lista de Materias
        self.lista_materias = QListWidget()
        self.lista_materias.itemDoubleClicked.connect(self.editar_materia_seleccionada)
        layout_izq.addWidget(self.lista_materias)
        
        # Botones de Accion
        self.btn_borrar = QPushButton("Eliminar Seleccionada")
        self.btn_borrar.setStyleSheet("background-color: #ffcccc; color: red;")
        self.btn_borrar.clicked.connect(self.eliminar_materia_seleccionada)
        layout_izq.addWidget(self.btn_borrar)
        
        self.btn_agregar = QPushButton("Agregar Nueva Materia")
        self.btn_agregar.setStyleSheet("padding: 8px; font-weight: bold;")
        self.btn_agregar.clicked.connect(self.abrir_dialogo_agregar)
        layout_izq.addWidget(self.btn_agregar)
        
        self.btn_generar = QPushButton("Generar Horarios")
        self.btn_generar.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; margin-top: 10px;")
        layout_izq.addWidget(self.btn_generar)
        
        # --- Panel Derecho (Tabs) ---
        self.panel_derecho = QWidget()
        layout_der = QVBoxLayout(self.panel_derecho)
        
        self.tabs = QTabWidget()
        
        # Tab 1: Vista Global
        self.tab_global = QWidget()
        layout_tab1 = QVBoxLayout(self.tab_global)
        self.grid_global = HorarioGrid() 
        layout_tab1.addWidget(self.grid_global)
        
        # Tab 2: Resultados
        self.tab_resultados = QWidget()
        layout_tab2 = QVBoxLayout(self.tab_resultados)
        
        # Navegacion de resultados
        layout_nav = QHBoxLayout()
        self.btn_prev = QPushButton("<< Anterior")
        self.btn_prev.clicked.connect(self.mostrar_horario_anterior)
        self.btn_prev.setEnabled(False)
        
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
        
        # Grid de resultados
        self.grid_resultados = HorarioGrid()
        layout_tab2.addWidget(self.grid_resultados)
        
        # Boton Exportar
        self.btn_exportar = QPushButton("Exportar este Horario (Imagen)")
        layout_tab2.addWidget(self.btn_exportar)
        
        self.tabs.addTab(self.tab_global, "Vista Global")
        self.tabs.addTab(self.tab_resultados, "Horarios Generados")
        
        layout_der.addWidget(self.tabs)
        layout_principal.addWidget(self.panel_izquierdo)
        layout_principal.addWidget(self.panel_derecho)

        # --- Inicializacion de Datos ---
        self.cargar_lista_materias()
        self.actualizar_vista_global()
        
        # Variables de estado para el motor
        self.resultados_generados = [] 
        self.indice_actual = 0
        
        # CONEXIONES FINALES (IMPORTANTE)
        self.btn_generar.clicked.connect(self.ejecutar_generador)
        self.btn_exportar.clicked.connect(self.exportar_horario_imagen)

    # --- FUNCIONES DE LOGICA ---

    def abrir_dialogo_agregar(self):
        dialogo = DialogoMateria(self)
        if dialogo.exec(): 
            datos = dialogo.obtener_datos()
            if database.insertar_materia_completa(datos):
                self.cargar_lista_materias() 
                self.actualizar_vista_global()
                QMessageBox.information(self, "Exito", "Materia guardada correctamente")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar la materia")

    def cargar_lista_materias(self):
        self.lista_materias.clear()
        materias = database.obtener_todas_las_materias()
        contador = 1 
        for id_mat, nombre in materias:
            item = QListWidgetItem(f"{contador}. {nombre}")
            item.setData(Qt.UserRole, id_mat) 
            self.lista_materias.addItem(item)
            contador += 1

    def eliminar_materia_seleccionada(self):
        item_actual = self.lista_materias.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Atencion", "Selecciona una materia para borrar.")
            return
            
        id_materia = item_actual.data(Qt.UserRole)
        nombre_mostrar = item_actual.text()
        
        respuesta = QMessageBox.question(
            self, "Confirmar", 
            f"Estas seguro de borrar la materia '{nombre_mostrar}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            if database.eliminar_materia(id_materia):
                self.cargar_lista_materias()
                self.actualizar_vista_global() 
                QMessageBox.information(self, "Listo", "Materia eliminada.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar.")

    def editar_materia_seleccionada(self, item):
        id_materia = item.data(Qt.UserRole)
        datos_actuales = database.obtener_materia_por_id(id_materia)
        if not datos_actuales: return

        dialogo = DialogoMateria(self)
        dialogo.cargar_datos_para_editar(datos_actuales)
        
        if dialogo.exec():
            nuevos_datos = dialogo.obtener_datos()
            if database.actualizar_materia_existente(id_materia, nuevos_datos):
                self.cargar_lista_materias()
                self.actualizar_vista_global()
                QMessageBox.information(self, "Exito", "Materia actualizada.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar.")

    def actualizar_vista_global(self):
        self.grid_global.limpiar()
        conn = database.crear_conexion()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT m.nombre, o.profesor, o.salon, b.dia, b.hora_inicio, b.hora_fin
                FROM bloques b
                JOIN opciones o ON b.opcion_id = o.id
                JOIN materias m ON o.materia_id = m.id
            """
            cursor.execute(query)
            filas = cursor.fetchall()
            
            colores_materias = {}
            for nombre, prof, salon, dia, inicio, fin in filas:
                if nombre not in colores_materias:
                    colores_materias[nombre] = self.grid_global.generar_color_random()
                self.grid_global.pintar_bloque(nombre, prof, salon, dia, inicio, fin, colores_materias[nombre])
                
        except Exception as e:
            print(f"Error al leer datos para el grid: {e}")
        finally:
            conn.close()

    # --- MOTOR Y GENERACION ---

    def cargar_datos_para_motor(self):
        import engine
        conn = database.crear_conexion()
        if not conn: return []
        
        cursor = conn.cursor()
        query = """
            SELECT m.nombre, o.id, o.profesor, o.salon, b.dia, b.hora_inicio, b.hora_fin
            FROM bloques b
            JOIN opciones o ON b.opcion_id = o.id
            JOIN materias m ON o.materia_id = m.id
        """
        cursor.execute(query)
        filas = cursor.fetchall()
        conn.close()
        
        agrupacion = {}
        for nombre, id_op, prof, salon, dia, inicio, fin in filas:
            if nombre not in agrupacion: agrupacion[nombre] = {}
            if id_op not in agrupacion[nombre]:
                agrupacion[nombre][id_op] = {
                    "profesor": prof, "salon": salon, "bloques_obj": []
                }
            
            min_inicio = engine.convertir_hora_a_minutos(inicio)
            min_fin = engine.convertir_hora_a_minutos(fin)
            agrupacion[nombre][id_op]["bloques_obj"].append(engine.Bloque(dia, min_inicio, min_fin))
            
        lista_materias_motor = []
        id_falso = 1
        for nombre_mat, opciones_dict in agrupacion.items():
            lista_opciones_obj = []
            for id_op, info in opciones_dict.items():
                op_obj = engine.Opcion(
                    id_opcion=id_op,
                    nombre_materia=nombre_mat,
                    profesor=info['profesor'],
                    salon=info['salon'],
                    bloques=info['bloques_obj']
                )
                lista_opciones_obj.append(op_obj)
            lista_materias_motor.append(engine.Materia(id_falso, nombre_mat, lista_opciones_obj))
            id_falso += 1
        return lista_materias_motor

    def ejecutar_generador(self):
        import engine
        materias_motor = self.cargar_datos_para_motor()
        if not materias_motor:
            QMessageBox.warning(self, "Vacio", "No hay materias registradas.")
            return

        self.resultados_generados = engine.generar_combinaciones(materias_motor)
        cant = len(self.resultados_generados)
        
        if cant == 0:
            QMessageBox.warning(self, "Ups", "No hay combinaciones posibles sin choques.")
            self.lbl_contador.setText("0 / 0")
            self.grid_resultados.limpiar()
            return
        
        QMessageBox.information(self, "Exito", f"Se encontraron {cant} combinaciones.")
        self.tabs.setCurrentIndex(1)
        self.indice_actual = 0
        self.mostrar_resultado_actual()

    def mostrar_resultado_actual(self):
        if not self.resultados_generados: return
        
        combinacion = self.resultados_generados[self.indice_actual]
        total = len(self.resultados_generados)
        self.lbl_contador.setText(f"Opcion {self.indice_actual + 1} de {total}")
        
        self.btn_prev.setEnabled(self.indice_actual > 0)
        self.btn_next.setEnabled(self.indice_actual < total - 1)
        
        self.grid_resultados.limpiar()
        import engine 
        
        colores_por_materia = {}
        for opcion in combinacion:
            if opcion.nombre_materia not in colores_por_materia:
                colores_por_materia[opcion.nombre_materia] = self.grid_resultados.generar_color_random()
            
            color = colores_por_materia[opcion.nombre_materia]
            for bloque in opcion.bloques:
                self.grid_resultados.pintar_bloque(
                    opcion.nombre_materia, opcion.profesor, opcion.salon,
                    bloque.dia, engine.minutos_a_hora(bloque.hora_inicio), 
                    engine.minutos_a_hora(bloque.hora_fin), color
                )

    def mostrar_horario_siguiente(self):
        if self.indice_actual < len(self.resultados_generados) - 1:
            self.indice_actual += 1
            self.mostrar_resultado_actual()

    def mostrar_horario_anterior(self):
        if self.indice_actual > 0:
            self.indice_actual -= 1
            self.mostrar_resultado_actual()

    def exportar_horario_imagen(self):
        """
        Genera imagen completa forzando al widget a redimensionarse temporalmente
        al tamano total de su contenido (Truco del Estiramiento).
        """
        if not self.resultados_generados:
            QMessageBox.warning(self, "Vacio", "Primero genera un horario.")
            return

        nombre_archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Imagen", "Mi_Horario_Smart.png", "Imagen PNG (*.png);;Imagen JPG (*.jpg)"
        )
        
        if nombre_archivo:
            try:
                # 1. ANALISIS DE LIMITES (Smart Crop)
                combinacion_actual = self.resultados_generados[self.indice_actual]
                min_minutos = 24 * 60  
                max_minutos = 0
                
                for opcion in combinacion_actual:
                    for bloque in opcion.bloques:
                        if bloque.hora_inicio < min_minutos: min_minutos = bloque.hora_inicio
                        if bloque.hora_fin > max_minutos: max_minutos = bloque.hora_fin
                            
                # Calcular filas a ocultar
                hora_base_minutos = self.grid_resultados.hora_inicio * 60
                fila_inicio_real = (min_minutos - hora_base_minutos) // 30
                fila_fin_real = (max_minutos - hora_base_minutos) // 30
                
                fila_minima = max(0, fila_inicio_real - 2)
                fila_maxima = min(self.grid_resultados.rowCount(), fila_fin_real + 2)

                # Ocultar/Mostrar filas
                for r in range(self.grid_resultados.rowCount()):
                    if r < fila_minima or r >= fila_maxima:
                        self.grid_resultados.setRowHidden(r, True)
                    else:
                        self.grid_resultados.setRowHidden(r, False)

                # 2. CALCULAR TAMAnO TOTAL REAL
                # Obtenemos el tamano de los encabezados y sumamos el contenido visible
                v_header = self.grid_resultados.verticalHeader()
                h_header = self.grid_resultados.horizontalHeader()
                
                # frameWidth * 2 es para incluir los bordes del widget
                borde = self.grid_resultados.frameWidth() * 2
                
                total_width = v_header.width() + h_header.length() + borde
                total_height = h_header.height() + v_header.length() + borde
                
                # 3. EL TRUCO: REDIMENSIONAR EL WIDGET REALMENTE
                # Guardamos el estado actual para restaurarlo despues
                old_min_size = self.grid_resultados.minimumSize()
                old_max_size = self.grid_resultados.maximumSize()
                old_h_policy = self.grid_resultados.horizontalScrollBarPolicy()
                old_v_policy = self.grid_resultados.verticalScrollBarPolicy()
                
                # Forzamos tamano gigante y quitamos scrollbars
                self.grid_resultados.setFixedSize(total_width, total_height)
                self.grid_resultados.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.grid_resultados.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                
                # 4. RENDERIZAR
                # Ahora que el widget es gigante fisicamente, render tomara todo
                pixmap = QPixmap(total_width, total_height)
                self.grid_resultados.render(pixmap)
                
                # 5. RESTAURAR ESTADO (Muy importante)
                self.grid_resultados.setMinimumSize(old_min_size)
                self.grid_resultados.setMaximumSize(old_max_size)
                self.grid_resultados.setHorizontalScrollBarPolicy(old_h_policy)
                self.grid_resultados.setVerticalScrollBarPolicy(old_v_policy)
                
                # Restaurar filas ocultas para seguir usando el programa
                for r in range(self.grid_resultados.rowCount()):
                    self.grid_resultados.setRowHidden(r, False)

                # 6. GUARDAR
                pixmap.save(nombre_archivo)
                QMessageBox.information(self, "Exito", f"Imagen completa guardada:\n{nombre_archivo}")
                
            except Exception as e:
                # Restauracion de emergencia
                self.grid_resultados.setMinimumSize(QSize(0,0))
                self.grid_resultados.setMaximumSize(QSize(16777215, 16777215))
                for r in range(self.grid_resultados.rowCount()):
                    self.grid_resultados.setRowHidden(r, False)
                QMessageBox.critical(self, "Error", f"Fallo al guardar:\n{e}")