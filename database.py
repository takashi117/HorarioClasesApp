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

def _insertar_opcion_y_bloques(cursor, id_materia, datos):
    """
    Inserta una opcion (profesor + salon) y sus bloques para una materia
    existente usando un cursor abierto dentro de una transaccion activa.
    """
    sql_opcion = "INSERT INTO opciones (materia_id, profesor, salon) VALUES (?, ?, ?)"
    cursor.execute(sql_opcion, (id_materia, datos['profesor'], datos['salon']))
    id_opcion = cursor.lastrowid

    sql_bloque = "INSERT INTO bloques (opcion_id, dia, hora_inicio, hora_fin) VALUES (?, ?, ?, ?)"
    for bloque in datos['bloques']:
        cursor.execute(sql_bloque, (
            id_opcion,
            bloque['dia'],
            bloque['inicio'],
            bloque['fin']
        ))

def insertar_materia_completa(datos):
    """
    Guarda materia con soporte para multiples bloques de horarios distintos.
    datos['bloques'] debe ser una lista de diccionarios:
    [{'dia': 'Lun', 'inicio': '07:00', 'fin': '09:00'}, ...]
    """
    conn = crear_conexion()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # 1. Insertar Materia
        sql_materia = "INSERT INTO materias (nombre) VALUES (?)"
        cursor.execute(sql_materia, (datos['nombre'],))
        id_materia = cursor.lastrowid

        # 2. Insertar Opcion (Profesor y Salon)
        _insertar_opcion_y_bloques(cursor, id_materia, datos)

        conn.commit()
        print(f"Materia '{datos['nombre']}' guardada con {len(datos['bloques'])} bloques.")
        return True

    except Error as e:
        print(f"Error al insertar: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def insertar_opcion_para_materia(id_materia, datos):
    """Agrega una nueva opcion (profesor/salon + bloques) a una materia existente."""
    conn = crear_conexion()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        _insertar_opcion_y_bloques(cursor, id_materia, datos)
        conn.commit()
        print(f"Opcion agregada a materia ID {id_materia} con {len(datos['bloques'])} bloques.")
        return True
    except Error as e:
        print(f"Error al insertar opcion: {e}")
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
            cursor.execute("SELECT MIN(id) as id, nombre FROM materias GROUP BY nombre")
            materias = cursor.fetchall() # Retorna lista de tuplas [(1, 'Fisica'), (2, 'Calculo')]
        except Error as e:
            print(f"Error al leer: {e}")
        finally:
            conn.close()
    return materias

def obtener_materia_por_nombre(nombre):
    """Retorna el ID de la materia cuyo nombre coincide (sin distincion de mayusculas)."""
    conn = crear_conexion()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM materias WHERE LOWER(nombre) = LOWER(?) LIMIT 1", (nombre,))
        fila = cursor.fetchone()
        return fila[0] if fila else None
    except Error as e:
        print(f"Error al buscar materia por nombre: {e}")
        return None
    finally:
        conn.close()

def eliminar_materia(id_materia):
    """Borra una materia y todas sus coincidencias de nombre para evitar duplicados."""
    conn = crear_conexion()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM materias WHERE id = ?", (id_materia,))
        fila = cursor.fetchone()
        if not fila:
            return False

        nombre = fila[0]
        cursor.execute("DELETE FROM materias WHERE LOWER(nombre) = LOWER(?)", (nombre,))
        conn.commit()
        return True
    except Error as e:
        print(f"Error al eliminar: {e}")
        return False
    finally:
        conn.close()

def obtener_materia_por_id(id_materia):
    """
    Recupera la materia y la primera opcion para poder editarla sin
    perder otras alternativas ya guardadas.
    """
    conn = crear_conexion()
    if not conn:
        return None

    data = {"id": id_materia, "bloques": []}

    try:
        cursor = conn.cursor()

        query_info = """
            SELECT m.nombre, o.id, o.profesor, o.salon
            FROM materias m
            JOIN opciones o ON o.materia_id = m.id
            WHERE m.id = ?
            ORDER BY o.id ASC
            LIMIT 1
        """
        cursor.execute(query_info, (id_materia,))
        fila = cursor.fetchone()

        if fila:
            data["nombre"] = fila[0]
            data["opcion_id"] = fila[1]
            data["profesor"] = fila[2]
            data["salon"] = fila[3]

            query_bloques = """
                SELECT b.dia, b.hora_inicio, b.hora_fin
                FROM bloques b
                WHERE b.opcion_id = ?
            """
            cursor.execute(query_bloques, (data["opcion_id"],))
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
    """Actualiza nombre y la primera opcion de una materia sin borrar las demas."""
    conn = crear_conexion()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("UPDATE materias SET nombre = ? WHERE id = ?", (nuevos_datos['nombre'], id_materia))

        opcion_id = nuevos_datos.get('opcion_id')
        if opcion_id is None:
            cursor.execute("SELECT id FROM opciones WHERE materia_id = ? ORDER BY id ASC LIMIT 1", (id_materia,))
            fila = cursor.fetchone()
            opcion_id = fila[0] if fila else None

        if opcion_id:
            cursor.execute("UPDATE opciones SET profesor = ?, salon = ? WHERE id = ?", (
                nuevos_datos['profesor'], nuevos_datos['salon'], opcion_id
            ))

            cursor.execute("DELETE FROM bloques WHERE opcion_id = ?", (opcion_id,))
            sql_bloque = "INSERT INTO bloques (opcion_id, dia, hora_inicio, hora_fin) VALUES (?, ?, ?, ?)"
            for bloque in nuevos_datos['bloques']:
                cursor.execute(sql_bloque, (
                    opcion_id,
                    bloque['dia'],
                    bloque['inicio'],
                    bloque['fin']
                ))
        else:
            _insertar_opcion_y_bloques(cursor, id_materia, nuevos_datos)

        conn.commit()
        return True
    except Error as e:
        print(f"Error al actualizar materia: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()