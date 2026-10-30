"""Modelo del entorno: la estación espacial multinivel.

COMÚN a las tres prácticas: la estación, las posiciones y las acciones son las
mismas en PR1, PR2 y PR3."""

from __future__ import annotations

from typing import Iterator, NamedTuple


class Pos(NamedTuple):
    """Posición en la estación: [nivel, fila, columna]."""

    nivel: int
    fila: int
    col: int

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return f"({self.nivel},{self.fila},{self.col})"

    def como_lista(self) -> list[int]:
        return [self.nivel, self.fila, self.col]


# ---------------------------------------------------------------------------
# ORDEN CANÓNICO DE GENERACIÓN DE SUCESORES
#
# Este orden es NORMATIVO. Junto con el desempate FIFO de la frontera, es lo
# que hace que los contadores de dos implementaciones correctas coincidan
# exactamente. No lo cambies.
# ---------------------------------------------------------------------------
ACCIONES: tuple[tuple[str, int, int, int], ...] = (
    ("NORTE", 0, -1, 0),
    ("ESTE", 0, 0, +1),
    ("SUR", 0, +1, 0),
    ("OESTE", 0, 0, -1),
    ("SUBIR", +1, 0, 0),
    ("BAJAR", -1, 0, 0),
)

MURO = 0


class Estacion:
    """Una estación espacial multinivel.

    Cada nivel es una rejilla de `filas` x `columnas`. El valor de una celda es
    su *coste de ocupación*: 0 significa no transitable (mamparo, zona
    prohibida) y k >= 1 es el coste de estar en ella (1 pasillo libre,
    2 zona de baja gravedad, 3 conducto técnico, ...).

    Movimiento horizontal: 4-vecindad dentro del mismo nivel.
    Movimiento vertical: solo por conexiones explícitas, que unen la MISMA
    (fila, columna) entre dos niveles CONSECUTIVOS. Físicamente son escotillas
    o ascensores, y por eso ocupan la misma vertical en ambas plantas.

    Coste de una transición horizontal entre celdas u y v:

        c(u, v) = max(coste_celda(u), coste_celda(v))

    Es simétrico y entero a propósito: la simetría es lo que permite que en la
    PR3 la matriz de distancias sea simétrica y que 2-opt siga siendo válido.
    La lectura física es "el tramo cuesta lo que la peor de sus dos celdas".

    Coste de una transición vertical: el coste declarado por la conexión, igual
    en ambos sentidos.
    """

    def __init__(
        self,
        rejillas: list[list[list[int]]],
        conexiones: list[dict],
        *,
        identificador: str = "sin-nombre",
        metadatos: dict | None = None,
    ) -> None:
        self.rejillas = rejillas
        self.niveles = len(rejillas)
        self.filas = len(rejillas[0])
        self.columnas = len(rejillas[0][0])
        self.identificador = identificador
        self.metadatos = metadatos or {}

        # Conexiones verticales indexadas por (nivel, fila, col) -> {destino: coste}
        self._conexiones: dict[Pos, dict[Pos, int]] = {}
        self.conexiones = conexiones
        for con in conexiones:
            n, f, c = con["nivel"], con["fila"], con["col"]
            coste = con["coste"]
            abajo, arriba = Pos(n, f, c), Pos(n + 1, f, c)
            self._conexiones.setdefault(abajo, {})[arriba] = coste
            self._conexiones.setdefault(arriba, {})[abajo] = coste

        self.coste_min_conexion = (
            min(con["coste"] for con in conexiones) if conexiones else 1
        )

    # ------------------------------------------------------------------
    # Consultas básicas
    # ------------------------------------------------------------------
    def dentro(self, p: Pos) -> bool:
        return (
            0 <= p.nivel < self.niveles
            and 0 <= p.fila < self.filas
            and 0 <= p.col < self.columnas
        )

    def coste_celda(self, p: Pos) -> int:
        """Coste de ocupación de la celda. 0 = no transitable."""
        if not self.dentro(p):
            return MURO
        return self.rejillas[p.nivel][p.fila][p.col]

    def es_transitable(self, p: Pos) -> bool:
        return self.coste_celda(p) > MURO

    def hay_conexion(self, a: Pos, b: Pos) -> bool:
        return b in self._conexiones.get(a, {})

    # ------------------------------------------------------------------
    # Sucesores — SIEMPRE en orden canónico
    # ------------------------------------------------------------------
    def sucesores(self, p: Pos) -> list[tuple[str, Pos, int]]:
        """Devuelve [(accion, destino, coste)] en el ORDEN CANÓNICO de ACCIONES.

        Es la única función que el alumnado debe usar para generar sucesores.
        Usar otro orden cambia los contadores y hace fallar la corrección
        automática, aunque el camino encontrado sea igual de óptimo.
        """
        salida: list[tuple[str, Pos, int]] = []
        for nombre, dn, df, dc in ACCIONES:
            destino = Pos(p.nivel + dn, p.fila + df, p.col + dc)
            if not self.dentro(destino) or not self.es_transitable(destino):
                continue
            if dn == 0:
                coste = max(self.coste_celda(p), self.coste_celda(destino))
            else:
                coste = self._conexiones.get(p, {}).get(destino)
                if coste is None:
                    continue  # no hay escotilla aquí
            salida.append((nombre, destino, coste))
        return salida

    def coste_transicion(self, a: Pos, b: Pos) -> int | None:
        """Coste de ir de a a b si son adyacentes; None si no lo son."""
        for _, destino, coste in self.sucesores(a):
            if destino == b:
                return coste
        return None

    # ------------------------------------------------------------------
    # Heurísticas de referencia
    # ------------------------------------------------------------------
    def h_manhattan(self, p: Pos, objetivo: Pos) -> int:
        """h1: distancia Manhattan 3D, contando cada cambio de nivel como 1.

        Admisible: toda acción cuesta >= 1 y reduce la suma |df|+|dc|+|dn| en
        como mucho 1. Consistente por el mismo motivo.
        """
        return (
            abs(p.fila - objetivo.fila)
            + abs(p.col - objetivo.col)
            + abs(p.nivel - objetivo.nivel)
        )

    def h_manhattan_conexiones(self, p: Pos, objetivo: Pos) -> int:
        """h2: como h1, pero cada cambio de nivel cuesta al menos
        `coste_min_conexion`.

        Domina a h1 cuando la conexión más barata cuesta más de 1, que es el
        caso en todas las instancias del catálogo. Sigue siendo admisible:
        cambiar de nivel exige atravesar una conexión, y ninguna cuesta menos
        que el mínimo.
        """
        return (
            abs(p.fila - objetivo.fila)
            + abs(p.col - objetivo.col)
            + abs(p.nivel - objetivo.nivel) * self.coste_min_conexion
        )

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def celdas_transitables(self) -> Iterator[Pos]:
        for n in range(self.niveles):
            for f in range(self.filas):
                for c in range(self.columnas):
                    p = Pos(n, f, c)
                    if self.es_transitable(p):
                        yield p

    def n_transitables(self) -> int:
        return sum(1 for _ in self.celdas_transitables())

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (
            f"<Estacion {self.identificador}: {self.niveles} niveles de "
            f"{self.filas}x{self.columnas}, {self.n_transitables()} celdas "
            f"transitables, {len(self.conexiones)} conexiones>"
        )
