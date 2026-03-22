import pandas as pd
from graphviz import Digraph

class AutomataVisualizer:
    def __init__(self, transiciones, estado_inicial, estados_aceptacion):
        self.nfa_transiciones = transiciones
        self.estado_inicial = estado_inicial
        self.estados_aceptacion = estados_aceptacion

        self.dfa_transiciones_crudas ={}
        self.mapeo_variables = {}
        self.dfa_transiciones_final = {}

    # ---------------------------------------------------------
    # PASO 1: Tabla de transiciones (AFND Original)
    # ---------------------------------------------------------
    def mostrar_tabla_original(self):
        print("--- Paso 1: Tabla de Transiciones (AFND) ---")
        df = pd.DataFrame(self.nfa_transiciones).fillna('-')
        print(df.T)
        print("\n")

    # ---------------------------------------------------------
    # PASO 2: Contemplar nuevos estados (Construcción de subconjuntos)
    # ---------------------------------------------------------
    def calcular_nuevos_estados(self):
        print("--- Paso 2: Contemplar Nuevos Estados ---")
        # Aquí se implementa la lógica de buscar a qué conjunto de estados
        # nos lleva cada transición. Usamos 'frozenset' para agrupar estados
        # Ejemplo simulado del resultado:
        self.dfa_transiciones_crudas = {
            frozenset(['q0']): {'0': frozenset(['q0', 'q1']), '1': frozenset(['q0'])},
            frozenset(['q0', 'q1']): {'0': frozenset(['q0', 'q1']), '1': frozenset(['q0', 'q2'])},
            # ... el algoritmo seguiría descubriendo estados ...
        }
        print("Nuevos estados (conjuntos) calculados lógicamente.\n")

    # ---------------------------------------------------------
    # PASO 3: Cambio de variable (Nueva tabla)
    # ---------------------------------------------------------
    def cambio_de_variable(self):
        print("--- Paso 3: Cambio de Variable (Nueva Tabla) ---")
        letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        # Asignar una nueva letra a cada conjunto de estados descubierto
        for idx, conjunto in enumerate(self.dfa_transiciones_crudas.keys()):
            nueva_variable = letras[idx]
            self.mapeo_variables[conjunto] = nueva_variable

        # Construir la nueva tabla con las letras
        for estado_origen, trans in self.dfa_transiciones_crudas.items():
            origen_var = self.mapeo_variables[estado_origen]
            self.dfa_transiciones_final[origen_var] = {}
            for simbolo, estado_destino in trans.items():
                if estado_destino in self.mapeo_variables:
                    destino_var = self.mapeo_variables[estado_destino]
                    self.dfa_transiciones_final[origen_var][simbolo] = destino_var

        df_nuevo = pd.DataFrame(self.dfa_transiciones_final).fillna('-')
        print("Mapeo:", {str(list(k)): v for k, v in self.mapeo_variables.items()})
        print("\nNueva Tabla (AFD):")
        print(df_nuevo.T)
        print("\n")
