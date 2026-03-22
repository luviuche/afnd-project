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