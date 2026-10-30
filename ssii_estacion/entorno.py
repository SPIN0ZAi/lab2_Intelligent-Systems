"""El entorno de la PR2: la estación vista desde dentro, sin plano.

Incluye también `ModeloEstacion`, el modelo completo del problema (las
probabilidades de transición y las recompensas), que solo se usa para
calcular la política óptima con iteración de valores.

EXCLUSIVO DE LA PR2 (aprendizaje por refuerzo).

En la PR1 el agente lo sabe todo y planifica. Aquí no sabe nada: solo puede
reiniciar el episodio, ejecutar una acción y observar dónde acaba y qué
recompensa recibe. Ni el mapa, ni los costes de las celdas, ni la función de
transición están a su alcance; por eso hay que aprender la política.

El movimiento es estocástico. Con probabilidad `p_exito` se ejecuta la acción
elegida; en caso contrario:

* si era horizontal, se ejecuta otra horizontal al azar (el agente resbala);
* si era SUBIR o BAJAR, la escotilla se atasca y el agente se queda donde está.

Si la acción ejecutada no es posible (mamparo, o no hay escotilla), el agente
choca: no se mueve y cobra la recompensa de colisión.

Cada episodio termina al llegar al destino o al agotar el límite de pasos. El
límite es parte de la dinámica, como `p_exito`: no es una recompensa, y cortar
un episodio por tiempo no es llegar a un estado terminal.

La dinámica sale de `consulta.dinamica` de la instancia: `p_exito`,
`limite_pasos` y las recompensas (`consulta.dinamica.recompensas`). Las tres
cosas se pueden sustituir al construir el entorno; rediseñar las recompensas
es parte del trabajo de la práctica.
"""

from __future__ import annotations

import random
import statistics
from pathlib import Path

from .modelo import ACCIONES, Estacion, Pos

HORIZONTALES = ("NORTE", "ESTE", "SUR", "OESTE")
VERTICALES = ("SUBIR", "BAJAR")
TODAS = tuple(a[0] for a in ACCIONES)

RECOMPENSAS_POR_DEFECTO = {
    "objetivo": 100,
    "paso_por_coste": -1,
    "colision": -5,
}


class EntornoEstacion:
    """Estación estocástica y opaca: `reset()` y `paso(accion)`.

    No expone la estación. El atributo que la guarda empieza por guion bajo y
    consultarlo es hacer trampa: si el agente pudiera leer el mapa, la política
    óptima se calcularía con A* y no habría nada que aprender.
    """

    def __init__(self, estacion: Estacion, *, semilla: int = 0,
                 recompensas: dict | None = None, p_exito: float | None = None,
                 limite_pasos: int | None = None) -> None:
        self._est = estacion
        self._rnd = random.Random(semilla)
        self.semilla = semilla
        self.p_exito = p_exito if p_exito is not None else getattr(estacion, "p_exito", 0.8)
        if recompensas and "limite_pasos" in recompensas:
            raise ValueError("limite_pasos no es una recompensa: pásalo como "
                             "EntornoEstacion(..., limite_pasos=N)")
        base = dict(RECOMPENSAS_POR_DEFECTO)
        base.update(getattr(estacion, "recompensas", {}) or {})
        base.update(recompensas or {})
        self.recompensas = base
        # Límite de pasos: el que se pase, el de la instancia o, si no hay, uno
        # proporcional al tamaño de la estación (el que usa el generador).
        self.limite_pasos = int(
            limite_pasos
            or getattr(estacion, "limite_pasos", None)
            or 4 * estacion.filas * estacion.columnas
        )
        self.acciones = TODAS
        self.instancia = estacion.identificador
        self.estado_inicial = estacion.origen
        self.pasos = 0
        self.episodios = 0
        self.pos = estacion.origen

    @classmethod
    def desde_instancia(cls, ruta: str | Path, **kwargs) -> "EntornoEstacion":
        from .instancia import cargar_instancia
        return cls(cargar_instancia(ruta), **kwargs)

    # ------------------------------------------------------------------
    def reset(self) -> Pos:
        """Empieza un episodio nuevo y devuelve el estado inicial."""
        self.pos = self._est.origen
        self.pasos = 0
        self.episodios += 1
        return self.pos

    def paso(self, accion: str) -> tuple[Pos, float, bool, dict]:
        """Ejecuta una acción. Devuelve (estado, recompensa, terminado, info).

        `info` trae `exito` (si el episodio acabó en el destino), `coste` (lo
        que costó el movimiento realmente ejecutado, 0 si no hubo movimiento),
        `accion_ejecutada` y `choque`.
        """
        if accion not in self.acciones:
            raise ValueError(f"acción desconocida: {accion!r}; deben ser {self.acciones}")
        self.pasos += 1
        ejecutada = self._deslizar(accion)
        disponibles = {a: (destino, coste) for a, destino, coste in self._est.sucesores(self.pos)}

        if ejecutada is not None and ejecutada in disponibles:
            destino, coste = disponibles[ejecutada]
            self.pos = destino
            recompensa = self.recompensas["paso_por_coste"] * coste
            choque = False
        else:                                    # mamparo, escotilla ausente o atascada
            coste = 0
            recompensa = self.recompensas["colision"]
            choque = True

        exito = self.pos == self._est.destino
        if exito:
            recompensa += self.recompensas["objetivo"]
        terminado = exito or self.pasos >= self.limite_pasos
        info = {"exito": exito, "coste": coste, "choque": choque,
                "accion_ejecutada": ejecutada, "pasos": self.pasos}
        return self.pos, recompensa, terminado, info

    # ------------------------------------------------------------------
    def _deslizar(self, accion: str) -> str | None:
        """La acción que se ejecuta de verdad. None = la escotilla se atasca."""
        if self._rnd.random() < self.p_exito:
            return accion
        if accion in HORIZONTALES:
            return self._rnd.choice([a for a in HORIZONTALES if a != accion])
        return None

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (f"<EntornoEstacion {self.instancia}: p_exito={self.p_exito}, "
                f"límite {self.limite_pasos} pasos, recompensas {self.recompensas}>")


class ModeloEstacion:
    """El modelo del proceso de decisión de Markov de la estación: lo que el
    agente de Q-learning NO tiene.

    Da, para cada estado y acción, las transiciones posibles con su
    probabilidad y su recompensa, exactamente con las mismas reglas que
    `EntornoEstacion.paso`: resbalones, escotillas atascadas y choques. Sirve
    para calcular la política óptima con iteración de valores y comparar con
    ella lo que aprende Q-learning. Usarlo dentro de Q-learning es hacer
    trampa, y la corrección lo comprueba.

        modelo = ModeloEstacion.desde_instancia("../catalogo/pr2/PR2-S-01.json")
        modelo.estados                      # todas las posiciones transitables
        modelo.acciones                     # las seis acciones
        modelo.es_terminal(s)               # True solo en el destino
        modelo.transiciones(s, a)           # [(probabilidad, s2, recompensa), ...]

    El problema es de horizonte infinito con descuento: el límite de pasos del
    entorno no forma parte del modelo, porque cortar un episodio no es llegar
    a un estado terminal.
    """

    def __init__(self, estacion: Estacion, *, recompensas: dict | None = None,
                 p_exito: float | None = None) -> None:
        if recompensas and "limite_pasos" in recompensas:
            raise ValueError("limite_pasos no es una recompensa ni forma parte del modelo")
        self._est = estacion
        self.p_exito = p_exito if p_exito is not None else getattr(estacion, "p_exito", 0.8)
        base = dict(RECOMPENSAS_POR_DEFECTO)
        base.update(getattr(estacion, "recompensas", {}) or {})
        base.update(recompensas or {})
        self.recompensas = base
        self.acciones = TODAS
        self.instancia = estacion.identificador
        self.origen = estacion.origen
        self.destino = estacion.destino
        self.estados = list(estacion.celdas_transitables())
        self._cache: dict = {}

    @classmethod
    def desde_instancia(cls, ruta: str | Path, **kwargs) -> "ModeloEstacion":
        from .instancia import cargar_instancia
        return cls(cargar_instancia(ruta), **kwargs)

    def es_terminal(self, estado: Pos) -> bool:
        return estado == self.destino

    def transiciones(self, estado: Pos, accion: str) -> list[tuple[float, Pos, float]]:
        """Lista de (probabilidad, estado siguiente, recompensa) al ejecutar
        `accion` en `estado`. Las probabilidades suman 1. Desde el destino, que
        es terminal, no hay transiciones."""
        if accion not in self.acciones:
            raise ValueError(f"acción desconocida: {accion!r}; deben ser {self.acciones}")
        clave = (estado, accion)
        if clave in self._cache:
            return self._cache[clave]
        if self.es_terminal(estado):
            return []
        if accion in HORIZONTALES:
            otras = [a for a in HORIZONTALES if a != accion]
            ejecutadas = [(self.p_exito, accion)] + [((1 - self.p_exito) / 3, a) for a in otras]
        else:
            ejecutadas = [(self.p_exito, accion), (1 - self.p_exito, None)]
        disponibles = {a: (d, c) for a, d, c in self._est.sucesores(estado)}
        juntas: dict[tuple[Pos, float], float] = {}
        for prob, ejecutada in ejecutadas:
            if prob == 0:
                continue
            if ejecutada is not None and ejecutada in disponibles:
                destino, coste = disponibles[ejecutada]
                recompensa = self.recompensas["paso_por_coste"] * coste
            else:
                destino, recompensa = estado, self.recompensas["colision"]
            if destino == self.destino:
                recompensa += self.recompensas["objetivo"]
            juntas[(destino, recompensa)] = juntas.get((destino, recompensa), 0.0) + prob
        salida = [(p, d, r) for (d, r), p in juntas.items()]
        self._cache[clave] = salida
        return salida

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (f"<ModeloEstacion {self.instancia}: {len(self.estados)} estados, "
                f"p_exito={self.p_exito}, recompensas {self.recompensas}>")


def evaluar_politica(entorno: EntornoEstacion, politica: dict, *, episodios: int = 200,
                     semilla: int = 12345, accion_por_defecto: str = "NORTE") -> dict:
    """Ejecuta la política aprendida y mide cómo se comporta.

    Lo que se evalúa NO es la tabla Q: es el comportamiento de la política.
    Se usa esta misma función en la corrección, de modo que los números de
    todas las entregas son comparables. La semilla fija los episodios de
    prueba, que son los mismos para todo el mundo.
    """
    estado_rnd = entorno._rnd
    entorno._rnd = random.Random(semilla)
    try:
        exitos, recompensas, pasos, costes = 0, [], [], []
        for _ in range(episodios):
            s = entorno.reset()
            total, coste, k = 0.0, 0, 0
            while True:
                a = politica.get(s, accion_por_defecto)
                s, r, fin, info = entorno.paso(a)
                total += r
                coste += info["coste"]
                k += 1
                if fin:
                    exitos += int(info["exito"])
                    recompensas.append(total)
                    pasos.append(k)
                    if info["exito"]:
                        costes.append(coste)
                    break
    finally:
        entorno._rnd = estado_rnd
    return {
        "episodios": episodios,
        "semilla": semilla,
        "tasa_exito": exitos / episodios,
        "recompensa_media": round(statistics.fmean(recompensas), 2),
        "recompensa_desv": round(statistics.pstdev(recompensas), 2),
        "pasos_medios": round(statistics.fmean(pasos), 2),
        "coste_medio": round(statistics.fmean(costes), 2) if costes else None,
    }
