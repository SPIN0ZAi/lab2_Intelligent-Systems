"""Carga las funciones de una entrega, para poder probarlas.

COMÚN a las tres prácticas: `FUNCIONES_PR1`, `FUNCIONES_PR2` y `FUNCIONES_PR3`
dicen qué funciones se espera encontrar en cada cuaderno. No hace falta usarlo
directamente: lo usan las pruebas públicas de cada práctica (`PRn/pruebas`)
para leer el cuaderno, y lo usa la corrección automática del mismo modo, de
modo que lo que pasa las pruebas en tu equipo se carga igual al corregir.

Una entrega es el cuaderno `.ipynb` completado (o un `.py` equivalente). De un
cuaderno se ejecutan **solo las celdas de definiciones** —las que contienen
funciones o clases—, nunca las que exploran, dibujan o exportan ficheros: así
probar una entrega no escribe nada ni tarda lo que tarde su estudio
experimental.

Las importaciones habituales del paquete se inyectan antes de ejecutar nada,
de modo que da igual en qué celda las pusiera cada pareja.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

from . import busqueda, entorno as _entorno, modelo, recorrido as _recorrido, solucion

FUNCIONES_PR1 = ("primero_el_mejor", "anchura", "coste_uniforme", "voraz", "a_estrella")
FUNCIONES_PR2 = ("q_learning", "politica_de", "iteracion_valores", "politica_desde_valores")
FUNCIONES_PR3 = ("ascension_colinas", "colinas_con_reinicios", "cruce_ox", "algoritmo_genetico")


class EntregaInvalida(Exception):
    """La entrega no se puede cargar o no define lo que debería."""


def _entorno_base() -> dict:
    return {
        "__name__": "entrega",
        "Pos": modelo.Pos,
        "Estacion": modelo.Estacion,
        "ACCIONES": modelo.ACCIONES,
        "Frontera": busqueda.Frontera,
        "Cerrados": busqueda.Cerrados,
        "Contadores": busqueda.Contadores,
        "Nodo": busqueda.Nodo,
        "reconstruir_camino": busqueda.reconstruir_camino,
        "solucion_pr1": solucion.solucion_pr1,
        "guardar_solucion": solucion.guardar_solucion,
        "validar_solucion_pr1": solucion.validar_solucion_pr1,
        "solucion_pr2": solucion.solucion_pr2,
        "EntornoEstacion": _entorno.EntornoEstacion,
        "ModeloEstacion": _entorno.ModeloEstacion,
        "evaluar_politica": _entorno.evaluar_politica,
        "random": __import__("random"),
        "solucion_pr3": solucion.solucion_pr3,
        "Evaluador": _recorrido.Evaluador,
        "cargar_matriz": _recorrido.cargar_matriz,
        "coste_recorrido": _recorrido.coste_recorrido,
        "invertir": _recorrido.invertir,
        "orden_aleatorio": _recorrido.orden_aleatorio,
        "orden_valido": _recorrido.orden_valido,
    }


def es_celda_de_definiciones(codigo: str) -> bool:
    """¿La celda solo define cosas? (funciones, clases, importaciones, constantes)"""
    try:
        arbol = ast.parse(codigo)
    except SyntaxError:
        return False
    permitidos = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
                  ast.ClassDef, ast.Assign, ast.AnnAssign)

    def es_cadena_suelta(n):   # un docstring al principio de la celda
        return (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str))

    hay_funcion = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                      for n in arbol.body)
    return hay_funcion and all(isinstance(n, permitidos) or es_cadena_suelta(n)
                               for n in arbol.body)


def codigo_de_cuaderno(ruta: str | Path) -> str:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    trozos = []
    for celda in datos.get("cells", []):
        if celda.get("cell_type") != "code":
            continue
        codigo = "".join(celda.get("source", []))
        codigo = "\n".join(l for l in codigo.splitlines() if not l.lstrip().startswith(("%", "!")))
        if es_celda_de_definiciones(codigo):
            trozos.append(codigo)
    return "\n\n".join(trozos)


def cargar_entrega(ruta: str | Path, *, funciones: tuple[str, ...] = FUNCIONES_PR1) -> dict:
    """Devuelve el espacio de nombres de la entrega, ya ejecutado.

    Lanza EntregaInvalida si el fichero no existe, si el código no compila o
    si falta alguna de las funciones que la práctica pide.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise EntregaInvalida(f"no existe la entrega {ruta}")
    if ruta.suffix == ".ipynb":
        codigo = codigo_de_cuaderno(ruta)
    else:
        codigo = ruta.read_text(encoding="utf-8")
    if not codigo.strip():
        raise EntregaInvalida(f"{ruta.name}: no hay ninguna celda con definiciones")

    raiz = ruta.resolve().parent.parent  # la carpeta de la práctica, con ssii_estacion
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))

    espacio = _entorno_base()
    try:
        exec(compile(codigo, f"<{ruta.name}>", "exec"), espacio)
    except Exception as e:  # noqa: BLE001 - el error de la entrega se reporta tal cual
        raise EntregaInvalida(f"{ruta.name}: error al ejecutar las definiciones: {e!r}") from e

    faltan = [f for f in funciones if not callable(espacio.get(f))]
    if faltan:
        raise EntregaInvalida(f"{ruta.name}: faltan funciones: {', '.join(faltan)}")
    return espacio
