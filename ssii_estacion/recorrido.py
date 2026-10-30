"""La PR3: recorrer N puntos de la estación en el mejor orden posible.

EXCLUSIVO DE LA PR3 (metaheurísticas).

La matriz de distancias son ejecuciones del algoritmo de la PR1 entre cada par
de puntos: aquí ya no se busca un camino, sino el ORDEN en que visitarlos. El
espacio de soluciones son las permutaciones, y con 15 puntos hay 1,3 billones,
así que se recorre con metaheurísticas.

Lo que pone el paquete es la contabilidad, por la misma razón que en la PR1
pone la frontera y los contadores: para que dos entregas sean comparables. El
`Evaluador` cuenta cada evaluación de la función objetivo y guarda la curva de
convergencia, de modo que "mi genético es mejor que mi ascensión de colinas"
solo pueda decirse con el mismo presupuesto de evaluaciones.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .modelo import Pos


def cargar_matriz(ruta: str | Path) -> tuple[list[Pos], list[list[int]]]:
    """Lee una matriz de distancias del catálogo. Devuelve (puntos, matriz).

    `puntos[0]` es la base; `matriz[i][j]`, el coste óptimo de ir de i a j.
    """
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    puntos = [Pos(*p) for p in datos["puntos"]]
    return puntos, datos["matriz"]


def coste_recorrido(matriz: list[list[int]], orden: list[int]) -> int:
    """Coste del recorrido cerrado: sale de la base (0), visita `orden`, vuelve."""
    ruta = [0] + list(orden) + [0]
    return sum(matriz[a][b] for a, b in zip(ruta, ruta[1:]))


def orden_valido(orden, n_puntos: int) -> bool:
    """¿`orden` es una permutación de 1..n_puntos? (la base no se incluye)"""
    return sorted(orden) == list(range(1, n_puntos + 1))


def orden_aleatorio(n_puntos: int, rnd: random.Random) -> list[int]:
    orden = list(range(1, n_puntos + 1))
    rnd.shuffle(orden)
    return orden


def invertir(orden: list[int], i: int, j: int) -> list[int]:
    """El movimiento 2-opt: invierte el segmento [i, j] (ambos incluidos).

    Es válido porque la matriz es simétrica: al invertir un segmento, el coste
    interior no cambia y solo hay que pagar los dos extremos nuevos.
    """
    if i > j:
        i, j = j, i
    return orden[:i] + orden[i:j + 1][::-1] + orden[j + 1:]


class PresupuestoAgotado(Exception):
    """Se han gastado todas las evaluaciones permitidas."""


class Evaluador:
    """Función objetivo con contador de evaluaciones y curva de convergencia.

    Todas las metaheurísticas de la práctica se comparan con el MISMO
    presupuesto: es la única forma de que la comparación signifique algo.

        ev = Evaluador(matriz, presupuesto=20_000)
        c = ev.coste(orden)          # cuenta una evaluación
        while not ev.agotado: ...    # el bucle lo controlas tú
    """

    def __init__(self, matriz: list[list[int]], presupuesto: int, *,
                 ventana: int = 100, estricto: bool = False) -> None:
        self.matriz = matriz
        self.n_puntos = len(matriz) - 1
        self.presupuesto = presupuesto
        self.ventana = ventana
        self.estricto = estricto
        self.evaluaciones = 0
        self.mejor_coste: int | None = None
        self.mejor_orden: list[int] | None = None
        self.curva: list[int] = []

    @property
    def agotado(self) -> bool:
        return self.evaluaciones >= self.presupuesto

    def coste(self, orden: list[int]) -> int:
        if self.estricto and self.agotado:
            raise PresupuestoAgotado(
                f"{self.evaluaciones} evaluaciones: se acabó el presupuesto")
        c = coste_recorrido(self.matriz, orden)
        self.evaluaciones += 1
        if self.mejor_coste is None or c < self.mejor_coste:
            self.mejor_coste, self.mejor_orden = c, list(orden)
        if self.evaluaciones % self.ventana == 0:
            self.curva.append(self.mejor_coste)
        return c

    def reinicia_contador(self) -> None:
        """Nueva repetición: se conserva la matriz, se olvida lo aprendido."""
        self.evaluaciones = 0
        self.mejor_coste = self.mejor_orden = None
        self.curva = []

    def resumen(self) -> dict:
        return {"evaluaciones": self.evaluaciones, "presupuesto": self.presupuesto,
                "mejor_coste": self.mejor_coste, "mejor_orden": self.mejor_orden,
                "curva": self.curva}

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (f"<Evaluador {self.n_puntos} puntos: {self.evaluaciones}/"
                f"{self.presupuesto} evaluaciones, mejor {self.mejor_coste}>")
