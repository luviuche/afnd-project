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
    # PASO 2: Contemplar nuevos estados (Algoritmo Dinámico)
    # ---------------------------------------------------------
    def calcular_nuevos_estados(self):
        print("--- Paso 2: Contemplar Nuevos Estados ---")

        # El estado inicial del DFA es el conjunto que contiene al estado inicial del NFA
        estado_inicial_conjunto = frozenset([self.estado_inicial])

        # Usamos una lista como cola para procesar los nuevos estados que vayamos descubriendo
        estados_por_procesar = [estado_inicial_conjunto]
        estados_procesados = set()  # Para no evaluar el mismo estado dos veces

        self.dfa_transiciones_crudas = {}

        while estados_por_procesar:
            estado_actual = estados_por_procesar.pop(0)

            if estado_actual in estados_procesados:
                continue

            estados_procesados.add(estado_actual)
            self.dfa_transiciones_crudas[estado_actual] = {}

            # 1. Encontrar qué símbolos (0, 1, etc.) salen desde los sub-estados actuales
            simbolos_posibles = set()
            for sub_estado in estado_actual:
                if sub_estado in self.nfa_transiciones:
                    simbolos_posibles.update(self.nfa_transiciones[sub_estado].keys())

            # 2. Calcular hacia dónde nos lleva cada símbolo
            for simbolo in simbolos_posibles:
                nuevo_estado_destino = set()

                for sub_estado in estado_actual:
                    if sub_estado in self.nfa_transiciones and simbolo in self.nfa_transiciones[sub_estado]:
                        # Unimos todos los destinos alcanzables con este símbolo
                        nuevo_estado_destino.update(self.nfa_transiciones[sub_estado][simbolo])

                # 3. Si hay destinos, registramos la transición y encolamos el nuevo estado
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

    # ---------------------------------------------------------
    # PASO 4: Pintar los autómatas
    # ---------------------------------------------------------
    def pintar_automata(self, nombre_archivo='automata_dfa'):
        print("--- Paso 4: Pintando el autómata ---")
        dot = Digraph(comment='Autómata')
        dot.attr(rankdir='LR')  # De izquierda a derecha

        # 1. Identificar qué nuevas variables (A, B, C...) son de aceptación
        # Un estado es de aceptación si contiene al menos un estado de aceptación del NFA original
        dfa_estados_aceptacion = set()
        for conjunto_original, nueva_letra in self.mapeo_variables.items():
            if any(estado in self.estados_aceptacion for estado in conjunto_original):
                dfa_estados_aceptacion.add(nueva_letra)

        # 2. Añadir estados y flechas
        for origen, trans in self.dfa_transiciones_final.items():
            # Asignar doble círculo si está en nuestra lista de aceptación
            forma = 'doublecircle' if origen in dfa_estados_aceptacion else 'circle'
            dot.node(origen, origen, shape=forma)

            for simbolo, destino in trans.items():
                dot.edge(origen, destino, label=simbolo)

        # Estado inicial invisible apuntando al inicio
        dot.node('', '', shape='none')
        primer_estado = list(self.dfa_transiciones_final.keys())[0] if self.dfa_transiciones_final else ''
        if primer_estado:
            dot.edge('', primer_estado)

        dot.render(nombre_archivo, format='png', view=True)
        print(f"Estados de aceptación detectados automáticamente: {dfa_estados_aceptacion}")
        print(f"Gráfico guardado y abierto como {nombre_archivo}.png\n")

    # ---------------------------------------------------------
    # PASO 5: Evaluar caminos y eliminar estados muertos
    # ---------------------------------------------------------
    def evaluar_y_limpiar_caminos(self):
        print("--- Paso 5: Evaluar caminos y eliminar estados muertos ---")

        # 1. Recuperar cuáles son los estados de aceptación del DFA
        dfa_estados_aceptacion = set()
        for conjunto_original, nueva_letra in self.mapeo_variables.items():
            if any(estado in self.estados_aceptacion for estado in conjunto_original):
                dfa_estados_aceptacion.add(nueva_letra)

        # 2. Identificar "estados vivos" (los que pueden llegar a una aceptación)
        estados_vivos = set(dfa_estados_aceptacion)
        hubo_cambios = True

        while hubo_cambios:
            hubo_cambios = False
            for origen, trans in self.dfa_transiciones_final.items():
                if origen not in estados_vivos:
                    # Si alguna de sus transiciones lleva a un estado vivo, este también está vivo
                    for simbolo, destino in trans.items():
                        if destino in estados_vivos:
                            estados_vivos.add(origen)
                            hubo_cambios = True
                            break  # Ya sabemos que este estado sobrevive

        # 3. Eliminar los estados que no están "vivos"
        estados_eliminados = []
        estados_actuales = list(self.dfa_transiciones_final.keys())

        for estado in estados_actuales:
            if estado not in estados_vivos:
                estados_eliminados.append(estado)
                del self.dfa_transiciones_final[estado]

        # 4. Limpiar las flechas (transiciones) que apuntaban a los estados eliminados
        for origen in self.dfa_transiciones_final:
            transiciones_a_borrar = [
                simbolo for simbolo, destino in self.dfa_transiciones_final[origen].items()
                if destino not in estados_vivos
            ]
            for simbolo in transiciones_a_borrar:
                del self.dfa_transiciones_final[origen][simbolo]

        # 5. Resultados
        if estados_eliminados:
            print(f"Se eliminaron los siguientes estados muertos/trampa: {estados_eliminados}")
            print("Generando nuevo gráfico limpio...")
            self.pintar_automata('automata_dfa_limpio')
        else:
            print("Todos los estados actuales son válidos y pueden llegar a un estado de aceptación.")
            print("No fue necesario eliminar ningún estado.\n")


# === EJECUCIÓN DEL PROGRAMA ===
if __name__ == "__main__":
    # Definimos un AFND de ejemplo (diccionario de diccionarios)
    transiciones_nfa = {
        'q0': {'0': ['q0', 'q1'], '1': ['q0']},
        'q1': {'1': ['q2']},
        'q2': {'0': ['q2'], '1': ['q2']}
    }

    programa = AutomataVisualizer(transiciones_nfa, 'q0', ['q2'])

    programa.mostrar_tabla_original()
    programa.calcular_nuevos_estados()
    programa.cambio_de_variable()
    programa.pintar_automata()
    programa.evaluar_y_limpiar_caminos()