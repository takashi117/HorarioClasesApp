from dataclasses import dataclass
from typing import List, Tuple

# --- Estructuras de Datos en Memoria ---

@dataclass
class Bloque:
    dia: str          # Ej: "Lunes"
    hora_inicio: int  # Minutos desde las 00:00 (Ej: 13:00 -> 780)
    hora_fin: int     # Minutos desde las 00:00

@dataclass
class Opcion:
    id_opcion: int
    nombre_materia: str
    profesor: str
    salon: str
    bloques: List[Bloque] # Una opcion puede tener varios bloques (Lunes y Miercoles)

@dataclass
class Materia:
    id_materia: int
    nombre: str
    opciones: List[Opcion] # Lista de grupos disponibles para esta materia

# --- Motor de Logica ---

def convertir_hora_a_minutos(hora_str: str) -> int:
    """Convierte '13:30' a 810 minutos para facilitar calculos matematicos."""
    h, m = map(int, hora_str.split(':'))
    return h * 60 + m

def minutos_a_hora(minutos: int) -> str:
    """Convierte 810 minutos de vuelta a '13:30'."""
    h = minutos // 60
    m = minutos % 60
    return f"{h:02d}:{m:02d}"

def hay_choque(bloque1: Bloque, bloque2: Bloque) -> bool:
    """Retorna True si dos bloques se solapan."""
    if bloque1.dia != bloque2.dia:
        return False
    
    # Formula matematica: max(inicio1, inicio2) < min(fin1, fin2)
    inicio_max = max(bloque1.hora_inicio, bloque2.hora_inicio)
    fin_min = min(bloque1.hora_fin, bloque2.hora_fin)
    
    choca = inicio_max < fin_min
    
    # --- DEBUG: Si hay choque, avisa en consola ---
    if choca:
        print(f"   CONFLICTO DETECTADO: {bloque1.dia}")
        print(f"   Bloque A: {minutos_a_hora(bloque1.hora_inicio)} - {minutos_a_hora(bloque1.hora_fin)}")
        print(f"   Bloque B: {minutos_a_hora(bloque2.hora_inicio)} - {minutos_a_hora(bloque2.hora_fin)}")
    # ----------------------------------------------
    
    return choca

def validar_horario(horario_actual: List[Opcion], nueva_opcion: Opcion) -> bool:
    """Revisa si la nueva_opcion choca con algo que ya esta en el horario."""
    for opcion_existente in horario_actual:
        for bloque_nuevo in nueva_opcion.bloques:
            for bloque_existente in opcion_existente.bloques:
                if hay_choque(bloque_nuevo, bloque_existente):
                    return False # Hay conflicto
    return True

def generar_combinaciones(materias: List[Materia]) -> List[List[Opcion]]:
    """
    Algoritmo principal (Backtracking).
    Genera todas las combinaciones validas de horarios.
    """
    resultados = []

    def backtrack(indice_materia, horario_actual):
        # Caso base: Si ya revisamos todas las materias, guardamos el horario
        if indice_materia == len(materias):
            resultados.append(list(horario_actual))
            return

        materia_actual = materias[indice_materia]
        
        # Intentar con cada opcion (profesor/grupo) de la materia actual
        for opcion in materia_actual.opciones:
            if validar_horario(horario_actual, opcion):
                # Si no choca, agregamos y pasamos a la siguiente materia
                horario_actual.append(opcion)
                backtrack(indice_materia + 1, horario_actual)
                horario_actual.pop() # Backtrack: quitamos para probar otra opcion

    backtrack(0, [])
    return resultados

# --- Bloque de Prueba (Solo se ejecuta si corres este archivo) ---
if __name__ == "__main__":
    print("--- Probando Motor de Logica ---")
    
    # Creamos datos falsos para probar
    # Materia 1: Matematicas (Lunes 8-10)
    b1 = Bloque("Lunes", convertir_hora_a_minutos("08:00"), convertir_hora_a_minutos("10:00"))
    op1 = Opcion(1, "Prof. A", "101", [b1])
    mat1 = Materia(1, "Matematicas", [op1])

    # Materia 2: Fisica (Lunes 9-11) -> Deberia chocar con Matematicas
    b2 = Bloque("Lunes", convertir_hora_a_minutos("09:00"), convertir_hora_a_minutos("11:00"))
    op2 = Opcion(2, "Prof. B (Choque)", "102", [b2])
    
    # Materia 2: Fisica (Lunes 10-12) -> No deberia chocar
    b3 = Bloque("Lunes", convertir_hora_a_minutos("10:00"), convertir_hora_a_minutos("12:00"))
    op3 = Opcion(3, "Prof. C (Valido)", "103", [b3])
    
    mat2 = Materia(2, "Fisica", [op2, op3])

    print("Generando combinaciones...")
    combinaciones = generar_combinaciones([mat1, mat2])
    
    print(f"Combinaciones encontradas: {len(combinaciones)}")
    for i, comb in enumerate(combinaciones):
        print(f"\nOpcion {i+1}:")
        for materia in comb:
            print(f" - {materia.profesor}")