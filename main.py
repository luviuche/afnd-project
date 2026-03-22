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
    # NFA con un estado trampa (q3)
    transiciones_nfa_trampa = {
        'q0': {'0': ['q0', 'q1'], '1': ['q3']},
        'q1': {'1': ['q2']},
        'q2': {'0': ['q2'], '1': ['q2']},
        'q3': {'0': ['q3'], '1': ['q3']}  # ¡El pozo sin fondo!
    }

    # Instanciamos el programa con el nuevo diccionario
    programa = AutomataVisualizer(transiciones_nfa_trampa, 'q0', ['q2'])

    programa.mostrar_tabla_original()
    programa.calcular_nuevos_estados()
    programa.cambio_de_variable()

    # Pintamos el autómata inicial (verás un estado que no lleva a nada)
    programa.pintar_automata('automata_con_trampa')

    # Evaluamos y limpiamos (debería eliminar el estado trampa y generar un nuevo gráfico)
    programa.evaluar_y_limpiar_caminos()