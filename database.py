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
    Guarda materia con soporte para multiples bloques de horarios distintos.
    datos['bloques'] debe ser una lista de diccionarios: 
    [{'dia': 'Lun', 'inicio': '07:00', 'fin': '09:00'}, ...]
    """
    conn = crear_conexion()
    if conn is None: return False
    
    try:
        cursor = conn.cursor()
        
        # 1. Insertar Materia
        sql_materia = "INSERT INTO materias (nombre) VALUES (?)"
        cursor.execute(sql_materia, (datos['nombre'],))
        id_materia = cursor.lastrowid
        
        # 2. Insertar Opcion (Profesor y Salon)
        # Nota: Asumimos una opcion por defecto por ahora.
        sql_opcion = "INSERT INTO opciones (materia_id, profesor, salon) VALUES (?, ?, ?)"
        cursor.execute(sql_opcion, (id_materia, datos['profesor'], datos['salon']))
        id_opcion = cursor.lastrowid
        
        # 3. Insertar LOS BLOQUES (Aqui esta el cambio mayor)
        sql_bloque = "INSERT INTO bloques (opcion_id, dia, hora_inicio, hora_fin) VALUES (?, ?, ?, ?)"
        
        # Ahora recorremos la lista de bloques que nos manda el dialogo
        for bloque in datos['bloques']:
            cursor.execute(sql_bloque, (
                id_opcion, 
                bloque['dia'], 
                bloque['inicio'], 
                bloque['fin']
            ))
            
        conn.commit()
        print(f"Materia '{datos['nombre']}' guardada con {len(datos['bloques'])} bloques.")
        return True
        
    except Error as e:
        print(f"Error al insertar: {e}")
        conn.rollback()
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

def obtener_materia_por_id(id_materia):
    """
    Recupera toda la estructura de una materia para poder editarla.
    Retorna un diccionario compatible con el dialogo.
    """
    conn = crear_conexion()
    if not conn: return None
    
    data = {"id": id_materia, "bloques": []}
    
    try:
        cursor = conn.cursor()
        
        # 1. Obtener datos basicos (Materia + Opcion)
        # Asumimos que por ahora solo hay 1 opcion por materia creada desde el UI
        query_info = """
            SELECT m.nombre, o.profesor, o.salon
            FROM materias m
            JOIN opciones o ON o.materia_id = m.id
            WHERE m.id = ?
        """
        cursor.execute(query_info, (id_materia,))
        fila = cursor.fetchone()
        
        if fila:
            data["nombre"] = fila[0]
            data["profesor"] = fila[1]
            data["salon"] = fila[2]
            
            # 2. Obtener los bloques de tiempo
            query_bloques = """
                SELECT b.dia, b.hora_inicio, b.hora_fin
                FROM bloques b
                JOIN opciones o ON b.opcion_id = o.id
                WHERE o.materia_id = ?
            """
            cursor.execute(query_bloques, (id_materia,))
            bloques = cursor.fetchall()
            
            for dia, inicio, fin in bloques:
                data["bloques"].append({
                    "dia": dia,
                    "inicio": inicio,
                    "fin": fin
                })
                
        return data
        
    except Error as e:
        print(f"Error al obtener materia: {e}")
        return None
    finally:
        conn.close()

def actualizar_materia_existente(id_materia, nuevos_datos):
    """
    Truco de Ingeniero: En lugar de hacer UPDATE complejos,
    es mas seguro borrar la vieja y crear la nueva con el mismo ID 
    o simplemente borrar y crear una nueva (aunque cambie el ID, es mas facil).
    
    Para mantener la integridad, haremos: Eliminar -> Insertar.
    """
    eliminar_materia(id_materia) # Ya la tenemos hecha
    return insertar_materia_completa(nuevos_datos) # Ya la tenemos hecha