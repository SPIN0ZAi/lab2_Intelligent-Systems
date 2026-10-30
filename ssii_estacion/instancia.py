"""Carga y validación de instancias en JSON.

COMÚN a las tres prácticas: el bloque `consulta` de la instancia es lo único
que cambia (`camino` en PR1, `politica` en PR2, `recorrido` en PR3).
"""

from __future__ import annotations

import json
from pathlib import Path

from .modelo import Estacion, Pos

ESQUEMA_VERSION = "ssii-estacion/1"


class InstanciaInvalida(ValueError):
    """La instancia no cumple el esquema. El mensaje dice exactamente qué falla."""


def _exige(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise InstanciaInvalida(mensaje)


def _pos(valor, campo: str) -> Pos:
    _exige(
        isinstance(valor, (list, tuple)) and len(valor) == 3,
        f"{campo}: se esperaba [nivel, fila, columna], se recibió {valor!r}",
    )
    _exige(
        all(isinstance(x, int) for x in valor),
        f"{campo}: los tres componentes deben ser enteros, se recibió {valor!r}",
    )
    return Pos(*valor)


def cargar_instancia(ruta: str | Path) -> Estacion:
    """Carga una instancia y la valida. Lanza InstanciaInvalida si algo falla."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return construir_instancia(datos)


def construir_instancia(datos: dict) -> Estacion:
    _exige(isinstance(datos, dict), "la raíz del JSON debe ser un objeto")

    version = datos.get("version")
    _exige(
        version == ESQUEMA_VERSION,
        f"version: se esperaba {ESQUEMA_VERSION!r}, se recibió {version!r}",
    )

    for campo in ("id", "estacion", "consulta"):
        _exige(campo in datos, f"falta el campo obligatorio {campo!r}")

    est = datos["estacion"]
    for campo in ("niveles", "filas", "columnas", "rejillas", "conexiones"):
        _exige(campo in est, f"estacion: falta el campo obligatorio {campo!r}")

    niveles, filas, columnas = est["niveles"], est["filas"], est["columnas"]
    rejillas = est["rejillas"]

    _exige(
        len(rejillas) == niveles,
        f"estacion.rejillas: se declararon {niveles} niveles pero hay {len(rejillas)}",
    )
    for n, rejilla in enumerate(rejillas):
        _exige(
            len(rejilla) == filas,
            f"estacion.rejillas[{n}]: se esperaban {filas} filas, hay {len(rejilla)}",
        )
        for f, fila in enumerate(rejilla):
            _exige(
                len(fila) == columnas,
                f"estacion.rejillas[{n}][{f}]: se esperaban {columnas} columnas, "
                f"hay {len(fila)}",
            )
            for c, v in enumerate(fila):
                _exige(
                    isinstance(v, int) and 0 <= v <= 3,
                    f"estacion.rejillas[{n}][{f}][{c}] = {v!r}: el coste de celda "
                    "debe ser un entero entre 0 (no transitable) y 3",
                )

    # Conexiones verticales
    vistas: set[tuple[int, int, int]] = set()
    for i, con in enumerate(est["conexiones"]):
        for campo in ("nivel", "fila", "col", "coste"):
            _exige(campo in con, f"conexiones[{i}]: falta el campo {campo!r}")
        n, f, c, k = con["nivel"], con["fila"], con["col"], con["coste"]
        _exige(
            0 <= n < niveles - 1,
            f"conexiones[{i}]: nivel {n} fuera de rango; una conexión une el "
            f"nivel n con el n+1, luego n debe estar entre 0 y {niveles - 2}",
        )
        _exige(0 <= f < filas, f"conexiones[{i}]: fila {f} fuera de rango")
        _exige(0 <= c < columnas, f"conexiones[{i}]: col {c} fuera de rango")
        _exige(
            isinstance(k, int) and k >= 1,
            f"conexiones[{i}]: coste {k!r} debe ser un entero >= 1",
        )
        _exige(
            rejillas[n][f][c] > 0 and rejillas[n + 1][f][c] > 0,
            f"conexiones[{i}]: la escotilla ({n},{f},{c}) une celdas no "
            "transitables; ambos extremos deben ser transitables",
        )
        clave = (n, f, c)
        _exige(clave not in vistas, f"conexiones[{i}]: conexión duplicada en {clave}")
        vistas.add(clave)

    estacion = Estacion(
        rejillas,
        est["conexiones"],
        identificador=datos["id"],
        metadatos=datos.get("metadatos", {}),
    )

    # Consulta: depende de la práctica
    consulta = datos["consulta"]
    tipo = consulta.get("tipo")
    _exige(
        tipo in ("camino", "politica", "recorrido"),
        f"consulta.tipo: se esperaba 'camino' (PR1), 'politica' (PR2) o "
        f"'recorrido' (PR3), se recibió {tipo!r}",
    )

    if tipo in ("camino", "politica"):
        origen = _pos(consulta["origen"], "consulta.origen")
        destino = _pos(consulta["destino"], "consulta.destino")
        _exige(
            estacion.es_transitable(origen),
            f"consulta.origen {origen} no es transitable",
        )
        _exige(
            estacion.es_transitable(destino),
            f"consulta.destino {destino} no es transitable",
        )
        estacion.origen, estacion.destino = origen, destino
    if tipo == "recorrido":
        base = _pos(consulta["base"], "consulta.base")
        _exige(estacion.es_transitable(base), f"consulta.base {base} no es transitable")
        puntos = [
            _pos(p, f"consulta.puntos[{i}]")
            for i, p in enumerate(consulta["puntos"])
        ]
        for p in puntos:
            _exige(estacion.es_transitable(p), f"consulta.puntos: {p} no es transitable")
        _exige(
            len(set(puntos)) == len(puntos),
            "consulta.puntos: hay puntos de visita repetidos",
        )
        estacion.base, estacion.puntos = base, puntos
    if tipo == "politica":
        din = consulta.get("dinamica", {})
        estacion.p_exito = din.get("p_exito", 0.8)
        estacion.recompensas = din.get("recompensas", {})
        _exige(
            "limite_pasos" not in estacion.recompensas,
            "consulta.dinamica.recompensas.limite_pasos: el límite de pasos no es una "
            "recompensa; va en consulta.dinamica.limite_pasos, junto a p_exito",
        )
        limite = din.get("limite_pasos")
        _exige(
            limite is None or (isinstance(limite, int) and limite >= 1),
            f"consulta.dinamica.limite_pasos = {limite!r}: debe ser un entero >= 1",
        )
        estacion.limite_pasos = limite

    estacion.tipo_consulta = tipo
    estacion.consulta = consulta
    return estacion
