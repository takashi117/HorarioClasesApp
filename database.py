# -*- coding: utf-8 -*-
import sqlite3
from sqlite3 import Error

def crear_conexion():
    """Crea una conexion a la base de datos SQLite."""
    conn = None
    try:
        conn = sqlite3.connect('horario.db')
        return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
    return conn

def inicializar_db():
    """Crea las tablas necesarias si no existen."""
    conn = crear_conexion()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # 1. Tabla de Materias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    codigo TEXT
                );
            """)

            # 2. Tabla de Opciones (Profesores/Secciones)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    materia_id INTEGER NOT NULL,
                    profesor TEXT,
                    salon TEXT,
                    FOREIGN KEY (materia_id) REFERENCES materias (id) ON DELETE CASCADE
                );
            """)

            # 3. Tabla de Bloques de Horario
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bloques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opcion_id INTEGER NOT NULL,
                    dia TEXT NOT NULL,
                    hora_inicio TEXT NOT NULL,
                    hora_fin TEXT NOT NULL,
                    FOREIGN KEY (opcion_id) REFERENCES opciones (id) ON DELETE CASCADE
                );
            """)
            
            conn.commit()
            print("Base de datos inicializada correctamente.")
        except Error as e:
            print(f"Error al crear las tablas: {e}")
        finally:
            conn.close()
    else:
        print("Error: No se pudo establecer la conexion.")

if __name__ == '__main__':
    inicializar_db()

# --- Funciones de Insercion ---

def insertar_materia_completa(datos):
    """
    Recibe el diccionario del dialogo y guarda todo en la BD.
    Retorna True si fue exitoso.
    """
    conn = crear_conexion()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 1. Insertar la Materia
        # Nota: Por simplicidad, creamos una nueva materia cada vez.
        sql_materia = "INSERT INTO materias (nombre) VALUES (?)"
        cursor.execute(sql_materia, (datos['nombre'],))
        id_materia = cursor.lastrowid # Obtenemos el ID generado
        
        # 2. Insertar la Opcion (Profesor/Salon)
        sql_opcion = "INSERT INTO opciones (materia_id, profesor, salon) VALUES (?, ?, ?)"
        cursor.execute(sql_opcion, (id_materia, datos['profesor'], datos['salon']))
        id_opcion = cursor.lastrowid
        
        # 3. Insertar los Bloques de Horario (Uno por cada dia seleccionado)
        sql_bloque = "INSERT INTO bloques (opcion_id, dia, hora_inicio, hora_fin) VALUES (?, ?, ?, ?)"
        
        for dia in datos['dias']:
            cursor.execute(sql_bloque, (id_opcion, dia, datos['inicio'], datos['fin']))
            
        conn.commit() # Guardar cambios
        print(f"Materia '{datos['nombre']}' guardada correctamente.")
        return True
        
    except Error as e:
        print(f"Error al insertar: {e}")
        conn.rollback() # Deshacer cambios si algo fallo
        return False
    finally:
        conn.close()

def obtener_todas_las_materias():
    """Retorna una lista simple de nombres de materias para mostrar en la lista."""
    conn = crear_conexion()
    materias = []
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM materias")
            materias = cursor.fetchall() # Retorna lista de tuplas [(1, 'Fisica'), (2, 'Calculo')]
        except Error as e:
            print(f"Error al leer: {e}")
        finally:
            conn.close()
    return materias

def eliminar_materia(id_materia):
    """Borra una materia y todos sus datos relacionados (Cascade)."""
    conn = crear_conexion()
    if conn is None: return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM materias WHERE id = ?", (id_materia,))
        conn.commit()
        return True
    except Error as e:
        print(f"Error al eliminar: {e}")
        return False
    finally:
        conn.close()