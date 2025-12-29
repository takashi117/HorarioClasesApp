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
                    salon TEXT,
                    FOREIGN KEY (opcion_id) REFERENCES opciones (id) ON DELETE CASCADE
                );
            """)

            # Migracion ligera: asegurar que la columna 'salon' existe en bloques
            cursor.execute("PRAGMA table_info(bloques)")
            columnas = [col[1] for col in cursor.fetchall()]
            if 'salon' not in columnas:
                cursor.execute("ALTER TABLE bloques ADD COLUMN salon TEXT")
                cursor.execute(
                    """
                    UPDATE bloques
                    SET salon = (
                        SELECT o.salon FROM opciones o WHERE o.id = bloques.opcion_id
                    )
                    WHERE salon IS NULL
                    """
                )

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
    Inserta una opcion (profesor) y sus bloques con salon para una materia
    existente usando un cursor abierto dentro de una transaccion activa.
    """
    bloques = datos['bloques']
    salon_opcion = bloques[0].get('salon', '') if bloques else ''

    sql_opcion = "INSERT INTO opciones (materia_id, profesor, salon) VALUES (?, ?, ?)"
    cursor.execute(sql_opcion, (id_materia, datos['profesor'], salon_opcion))
    id_opcion = cursor.lastrowid

    sql_bloque = "INSERT INTO bloques (opcion_id, dia, hora_inicio, hora_fin, salon) VALUES (?, ?, ?, ?, ?)"
    for bloque in bloques:
        cursor.execute(sql_bloque, (
            id_opcion,
            bloque['dia'],
            bloque['inicio'],
            bloque['fin'],
            bloque.get('salon', '')
        ))

def insertar_materia_completa(datos):
    """
    Guarda una materia con una o varias alternativas de horario.
    datos['opciones'] debe contener la lista de alternativas; en su defecto
    se aceptara una estructura plana con 'bloques' y 'profesor'.
    """
    conn = crear_conexion()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("INSERT INTO materias (nombre) VALUES (?)", (datos['nombre'],))
        id_materia = cursor.lastrowid

        opciones = datos.get('opciones') or [datos]
        for opcion in opciones:
            _insertar_opcion_y_bloques(cursor, id_materia, opcion)

        conn.commit()
        print(f"Materia '{datos['nombre']}' guardada con {len(opciones)} alternativas.")
        return True

    except Error as e:
        print(f"Error al insertar: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def insertar_opciones_para_materia(id_materia, opciones):
    """Agrega una o mas opciones a una materia existente."""
    conn = crear_conexion()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        for opcion in opciones:
            _insertar_opcion_y_bloques(cursor, id_materia, opcion)
        conn.commit()
        print(f"Se agregaron {len(opciones)} opciones a la materia ID {id_materia}.")
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

def obtener_materia_con_opciones(id_materia):
    """Recupera la materia y todas sus alternativas con sus bloques."""
    conn = crear_conexion()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM materias WHERE id = ?", (id_materia,))
        fila = cursor.fetchone()
        if not fila:
            return None

        nombre = fila[0]
        cursor.execute("SELECT id FROM materias WHERE LOWER(nombre) = LOWER(?) ORDER BY id", (nombre,))
        ids_materias = [id_row[0] for id_row in cursor.fetchall()]
        if not ids_materias:
            return None

        query_opciones = f"""
            SELECT o.id, o.profesor, o.salon
            FROM opciones o
            WHERE o.materia_id IN ({','.join(['?'] * len(ids_materias))})
            ORDER BY o.id ASC
        """
        cursor.execute(query_opciones, ids_materias)
        opciones_rows = cursor.fetchall()

        resultado = {"id": ids_materias[0], "nombre": nombre, "opciones": []}

        for opcion_id, profesor, salon_opcion in opciones_rows:
            cursor.execute(
                "SELECT dia, hora_inicio, hora_fin, salon FROM bloques WHERE opcion_id = ?",
                (opcion_id,)
            )
            bloques = [
                {
                    "dia": dia,
                    "inicio": inicio,
                    "fin": fin,
                    "salon": salon if salon else salon_opcion
                }
                for dia, inicio, fin, salon in cursor.fetchall()
            ]

            resultado["opciones"].append({
                "id": opcion_id,
                "profesor": profesor,
                "bloques": bloques
            })

        return resultado

    except Error as e:
        print(f"Error al obtener materia: {e}")
        return None
    finally:
        conn.close()

def actualizar_materia_existente(id_materia, nuevos_datos):
    """Actualiza la materia y reemplaza todas sus alternativas por las nuevas."""
    conn = crear_conexion()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT nombre FROM materias WHERE id = ?", (id_materia,))
        fila = cursor.fetchone()
        if not fila:
            return False

        nombre_actual = fila[0]
        cursor.execute(
            "UPDATE materias SET nombre = ? WHERE LOWER(nombre) = LOWER(?)",
            (nuevos_datos['nombre'], nombre_actual)
        )

        cursor.execute("SELECT id FROM materias WHERE LOWER(nombre) = LOWER(?)", (nuevos_datos['nombre'],))
        ids_materias = [row[0] for row in cursor.fetchall()]
        if not ids_materias:
            return False

        cursor.execute(
            f"DELETE FROM opciones WHERE materia_id IN ({','.join(['?'] * len(ids_materias))})",
            ids_materias
        )

        id_base = ids_materias[0]
        for opcion in nuevos_datos.get('opciones', []):
            _insertar_opcion_y_bloques(cursor, id_base, opcion)

        conn.commit()
        return True
    except Error as e:
        print(f"Error al actualizar materia: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
