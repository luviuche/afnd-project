import pandas as pd
from graphviz import Digraph

class AutomataVisualizer:
    def __init__(self, transiciones, estado_inicial, estados_aceptacion):
        self.nfa_transiciones = transiciones
        self.estado_inicial = estado_inicial
        self.estados_aceptacion = estados_aceptacion

        # Extraer el alfabeto dinámicamente (ej. '0', '1')
        self.alfabeto = set()
        for estado, trans in self.nfa_transiciones.items():
            self.alfabeto.update(trans.keys())
        self.alfabeto = sorted(list(self.alfabeto))

        self.dfa_transiciones_crudas ={}
        self.mapeo_variables = {}
        self.dfa_transiciones_final = {}

    # --- METODO AYUDANTE ---
    def _imprimir_tabla(self, diccionario_transiciones, titulo):
        print(f"--- {titulo} ---")
        if not diccionario_transiciones:
            print("La tabla está vacía.\n")
            return

        # Crear DataFrame, transponerlo (estados como filas) y rellenar nulos
        df = pd.DataFrame(diccionario_transiciones).T
        # Asegurar que todas las columnas del alfabeto existan y ordenarlas
        df = df.reindex(columns=self.alfabeto).fillna('-')
        print(df)
        print("\n")

    # ---------------------------------------------------------
    # PASO 1: Tabla de transiciones (AFND Original)
    # ---------------------------------------------------------
    def mostrar_tabla_original(self):
        self._imprimir_tabla(self.nfa_transiciones, "Paso 1: Tabla de Transiciones (AFND)")

    # ---------------------------------------------------------
    # PASO 2: Contemplar nuevos estados (Algoritmo Dinámico)
    # ---------------------------------------------------------
    def calcular_nuevos_estados(self):
        print("--- Paso 2: Contemplar Nuevos Estados ---")
        estado_inicial_conjunto = frozenset([self.estado_inicial])
        estados_por_procesar = [estado_inicial_conjunto]
        estados_procesados = set()
        self.dfa_transiciones_crudas = {}

        while estados_por_procesar:
            estado_actual = estados_por_procesar.pop(0)
            if estado_actual in estados_procesados: continue

            estados_procesados.add(estado_actual)
            self.dfa_transiciones_crudas[estado_actual] = {}

            for simbolo in self.alfabeto:
                nuevo_estado_destino = set()
                for sub_estado in estado_actual:
                    if sub_estado in self.nfa_transiciones and simbolo in self.nfa_transiciones[sub_estado]:
                        nuevo_estado_destino.update(self.nfa_transiciones[sub_estado][simbolo])

                if nuevo_estado_destino:
                    destino_frozenset = frozenset(nuevo_estado_destino)
                    self.dfa_transiciones_crudas[estado_actual][simbolo] = destino_frozenset

                    if destino_frozenset not in estados_procesados:
                        estados_por_procesar.append(destino_frozenset)

        print(f"Se descubrieron {len(self.dfa_transiciones_crudas)} estados en total.\n")

    # ---------------------------------------------------------
    # PASO 3: Cambio de variable (Nueva tabla)
    # ---------------------------------------------------------
    def cambio_de_variable(self):
        print("--- Paso 3: Cambio de Variable ---")
        letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        for idx, conjunto in enumerate(self.dfa_transiciones_crudas.keys()):
            self.mapeo_variables[conjunto] = letras[idx]

        for estado_origen, trans in self.dfa_transiciones_crudas.items():
            origen_var = self.mapeo_variables[estado_origen]
            self.dfa_transiciones_final[origen_var] = {}
            for simbolo, estado_destino in trans.items():
                if estado_destino in self.mapeo_variables:
                    destino_var = self.mapeo_variables[estado_destino]
                    self.dfa_transiciones_final[origen_var][simbolo] = destino_var

        print("Mapeo interno:", {str(list(k)): v for k, v in self.mapeo_variables.items()})
        print()
        self._imprimir_tabla(self.dfa_transiciones_final, "Nueva Tabla (AFD Generado)")

    # ---------------------------------------------------------
    # PASO 4: Pintar los autómatas
    # ---------------------------------------------------------
    def pintar_automata(self, nombre_archivo='automata_dfa'):
        print(f"--- Pintando el autómata: {nombre_archivo} ---")
        dot = Digraph(comment='Autómata', format='png')
        dot.attr(rankdir='LR')
        dot.attr('node', fontname='Helvetica')  # Estilo de fuente más limpio

        dfa_estados_aceptacion = self._obtener_estados_aceptacion_dfa()

        for origen, trans in self.dfa_transiciones_final.items():
            forma = 'doublecircle' if origen in dfa_estados_aceptacion else 'circle'
            dot.node(origen, origen, shape=forma)
            for simbolo, destino in trans.items():
                dot.edge(origen, destino, label=simbolo)

        dot.node('', '', shape='none')
        if self.dfa_transiciones_final:
            primer_estado = list(self.dfa_transiciones_final.keys())[0]
            dot.edge('', primer_estado)

        dot.render(nombre_archivo, view=True)
        print(f"Gráfico generado con éxito.\n")

    # --- METODO AYUDANTE ---
    def _obtener_estados_aceptacion_dfa(self):
        aceptacion = set()
        for conjunto, letra in self.mapeo_variables.items():
            if any(est in self.estados_aceptacion for est in conjunto):
                aceptacion.add(letra)
        return aceptacion

    # ---------------------------------------------------------
    # PASO 5: Evaluar caminos y eliminar estados muertos
    # ---------------------------------------------------------
    def evaluar_y_limpiar_caminos(self):
        print("--- Paso 5: Evaluar caminos y optimizar ---")
        dfa_estados_aceptacion = self._obtener_estados_aceptacion_dfa()
        estados_vivos = set(dfa_estados_aceptacion)
        hubo_cambios = True

        while hubo_cambios:
            hubo_cambios = False
            for origen, trans in self.dfa_transiciones_final.items():
                if origen not in estados_vivos:
                    if any(destino in estados_vivos for destino in trans.values()):
                        estados_vivos.add(origen)
                        hubo_cambios = True

        estados_actuales = list(self.dfa_transiciones_final.keys())
        estados_eliminados = [e for e in estados_actuales if e not in estados_vivos]

        # Eliminar estados y limpiar transiciones
        for estado in estados_eliminados:
            del self.dfa_transiciones_final[estado]

        for origen in self.dfa_transiciones_final:
            a_borrar = [s for s, d in self.dfa_transiciones_final[origen].items() if d not in estados_vivos]
            for s in a_borrar: del self.dfa_transiciones_final[origen][s]

        if estados_eliminados:
            print(f"-> Se eliminaron los estados trampa/inalcanzables: {estados_eliminados}\n")
            self._imprimir_tabla(self.dfa_transiciones_final, "Tabla Final Optimizada (Sin trampas)")
            self.pintar_automata('automata_dfa_limpio')
        else:
            print("-> El autómata ya es óptimo. No hay estados muertos.\n")

    # ---------------------------------------------------------
    # PASO EXTRA: Evaluar cadenas en el AFD limpio
    # ---------------------------------------------------------
    def evaluar_cadena(self, cadena):
        print(f"--- Evaluando la cadena: '{cadena}' ---")

        # 1. Encontrar cuál es el estado inicial del AFD
        estado_actual = None
        for conjunto, letra in self.mapeo_variables.items():
            if self.estado_inicial in conjunto:
                estado_actual = letra
                break

        # Validar que el autómata no haya quedado completamente vacío
        if not estado_actual or estado_actual not in self.dfa_transiciones_final:
            print("Error: El autómata no tiene un estado inicial válido para iniciar.\n")
            return False

        camino = [f"[{estado_actual}]"]

        # 2. Recorrer la cadena símbolo por símbolo
        for simbolo in cadena:
            if simbolo not in self.alfabeto:
                print(f"Rechazada ❌: El símbolo '{simbolo}' no pertenece al alfabeto {self.alfabeto}.")
                return False

            transiciones_estado = self.dfa_transiciones_final.get(estado_actual, {})

            if simbolo in transiciones_estado:
                estado_actual = transiciones_estado[simbolo]
                camino.append(f"--({simbolo})--> [{estado_actual}]")
            else:
                camino.append(f"--({simbolo})--> [X Muro/Trampa X]")
                print(f"Ruta: {' '.join(camino)}")
                print(f"Resultado: CADENA RECHAZADA ❌ (Se cortó el camino en '{simbolo}')\n")
                return False

        # 3. Verificar si el estado en el que terminó es de aceptación
        print(f"Ruta: {' '.join(camino)}")
        estados_aceptacion = self._obtener_estados_aceptacion_dfa()

        if estado_actual in estados_aceptacion:
            print("Resultado: CADENA ACEPTADA ✅\n")
            return True
        else:
            print(f"Resultado: CADENA RECHAZADA ❌ (Terminó en [{estado_actual}], que no es de aceptación)\n")
            return False


# === EJECUCIÓN DEL PROGRAMA ===
if __name__ == "__main__":
    transiciones_nfa_trampa = {
        'q0': {'0': ['q0', 'q1'], '1': ['q3']},
        'q1': {'1': ['q2']},
        'q2': {'0': ['q2'], '1': ['q2']},
        'q3': {'0': ['q3'], '1': ['q3']}
    }

    programa = AutomataVisualizer(transiciones_nfa_trampa, 'q0', ['q2'])
    programa.mostrar_tabla_original()
    programa.calcular_nuevos_estados()
    programa.cambio_de_variable()
    programa.pintar_automata('automata_con_trampa')
    programa.evaluar_y_limpiar_caminos()

    # --- PRUEBAS DE CADENAS PARA EL PROFESOR ---
    # 1. Una cadena válida que debería llegar a 'D' (Aceptada)
    programa.evaluar_cadena("01")

    # 2. Una cadena válida más larga que se queda ciclando en la aceptación (Aceptada)
    programa.evaluar_cadena("01010")

    # 3. Una cadena que intenta ir por la ruta eliminada (Rechazada)
    programa.evaluar_cadena("10")

    # 4. Una cadena que se queda a la mitad (Rechazada)
    programa.evaluar_cadena("0")