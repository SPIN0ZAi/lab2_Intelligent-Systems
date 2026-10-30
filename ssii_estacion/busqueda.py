"""Frontera, conjunto de alcanzados y contadores instrumentados.

EXCLUSIVO DE LA PR1 (búsqueda en espacio de estados). La PR2 usa
`entorno.py` y la PR3 `recorrido.py`.

La razón de que esto lo dé el profesorado y no lo escriba el alumnado es la
corrección automática: los cinco contadores son extremadamente sensibles al
orden de generación de sucesores y a cómo se rompen los empates. Con estas
clases, dos implementaciones correctas del mismo algoritmo producen
exactamente los mismos números.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any

from .modelo import Pos


@dataclass
class Nodo:
    """Un nodo del árbol de búsqueda.

    Recuerda la distinción del tema 2: los ESTADOS no tienen padre, ni
    profundidad, ni coste. Los NODOS sí. Un mismo estado puede estar
    representado por varios nodos distintos.
    """

    estado: Pos
    padre: "Nodo | None" = None
    accion: str | None = None
    coste: int = 0          # g(n): coste del camino desde el origen
    profundidad: int = 0

    def camino(self) -> list["Nodo"]:
        """Nodos desde la raíz hasta este nodo, en orden."""
        ruta, actual = [], self
        while actual is not None:
            ruta.append(actual)
            actual = actual.padre
        ruta.reverse()
        return ruta


def reconstruir_camino(nodo: Nodo) -> tuple[list[Pos], list[str]]:
    """Devuelve (posiciones, acciones) del camino que lleva hasta `nodo`."""
    nodos = nodo.camino()
    posiciones = [n.estado for n in nodos]
    acciones = [n.accion for n in nodos[1:]]
    return posiciones, acciones


@dataclass
class Contadores:
    """Los cinco contadores que hay que reportar en la solución.

    Definiciones NORMATIVAS (las mismas que se usan en teoría):

    - generados: nodos creados, incluido el nodo raíz.
    - explorados: nodos EXTRAÍDOS de la frontera para ser examinados.
    - expandidos: de los explorados, aquellos a los que se les han generado
      sucesores. Un nodo extraído cuyo estado ya estaba en alcanzados se
      descarta sin expandir, y un nodo objetivo termina la búsqueda sin
      expandirse. Por tanto siempre: expandidos <= explorados <= generados.
    - max_frontera: tamaño máximo que alcanza la lista de abiertos.
    - max_alcanzados: tamaño máximo que alcanza el conjunto de cerrados.
    """

    generados: int = 0
    explorados: int = 0
    expandidos: int = 0
    max_frontera: int = 0
    max_alcanzados: int = 0

    def como_dict(self) -> dict[str, int]:
        return {
            "nodos_generados": self.generados,
            "nodos_explorados": self.explorados,
            "nodos_expandidos": self.expandidos,
            "max_frontera": self.max_frontera,
            "max_alcanzados": self.max_alcanzados,
        }


@dataclass(order=True)
class _Entrada:
    prioridad: float
    orden: int
    nodo: Any = field(compare=False)


class Frontera:
    """Cola de prioridad con desempate FIFO, contadores incluidos.

    El desempate es NORMATIVO: entre dos nodos con la misma prioridad f, sale
    primero el que se insertó antes. Se implementa con un contador de inserción
    como segundo componente de la tupla del montículo. Sin esta regla, dos
    implementaciones igual de correctas dan contadores distintos.

    Para búsqueda en anchura se usa f = profundidad; para coste uniforme,
    f = g; para voraz, f = h; para A*, f = g + h. Es decir: un único
    algoritmo, parametrizado por f. Es el marco BEST-FIRST-SEARCH de la
    4.ª edición de Russell y Norvig.
    """

    def __init__(self, contadores: Contadores | None = None) -> None:
        self._monticulo: list[_Entrada] = []
        self._orden = 0
        self.contadores = contadores or Contadores()

    def insertar(self, nodo: Nodo, prioridad: float) -> None:
        heapq.heappush(self._monticulo, _Entrada(prioridad, self._orden, nodo))
        self._orden += 1
        self.contadores.max_frontera = max(
            self.contadores.max_frontera, len(self._monticulo)
        )

    def extraer(self) -> Nodo:
        """Extrae el nodo de menor f. Cuenta como 'explorado'."""
        entrada = heapq.heappop(self._monticulo)
        self.contadores.explorados += 1
        return entrada.nodo

    def vacia(self) -> bool:
        return not self._monticulo

    def __len__(self) -> int:
        return len(self._monticulo)


class Cerrados:
    """Conjunto de estados alcanzados, con el mejor coste conocido para cada uno.

    Uso recomendado (el del tema 3 con la 4.ª edición): antes de insertar un
    sucesor, se consulta `mejora(estado, g)`. Devuelve True si el estado no se
    había alcanzado nunca o si se ha llegado a él por un camino más barato, y
    en ese caso actualiza el registro. Esto es lo que evita el error clásico de
    descartar un repetido que llegaba por un camino mejor, que rompe la
    optimalidad de coste uniforme y de A*.
    """

    def __init__(self, contadores: Contadores | None = None) -> None:
        self._mejor: dict[Pos, int] = {}
        self.contadores = contadores or Contadores()

    def mejora(self, estado: Pos, coste: int) -> bool:
        previo = self._mejor.get(estado)
        if previo is None or coste < previo:
            self._mejor[estado] = coste
            self.contadores.max_alcanzados = max(
                self.contadores.max_alcanzados, len(self._mejor)
            )
            return True
        return False

    def contiene(self, estado: Pos) -> bool:
        return estado in self._mejor

    def coste(self, estado: Pos) -> int | None:
        return self._mejor.get(estado)

    def __len__(self) -> int:
        return len(self._mejor)
