"""Construcción, volcado y validación de las soluciones en JSON.

COMÚN a las tres prácticas: una función por práctica (`solucion_pr1`,
`solucion_pr2`, `solucion_pr3`) y su validador correspondiente.
"""

from __future__ import annotations

import json
from pathlib import Path

from .busqueda import Contadores
from .modelo import Estacion, Pos

ESQUEMA_VERSION = "ssii-estacion/1"


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------
def _cabecera(instancia_id: str, practica: str, algoritmo: str, autores: list[str]):
    return {
        "version": ESQUEMA_VERSION,
        "practica": practica,
        "instancia": instancia_id,
        "algoritmo": algoritmo,
        "autores": autores,
    }


def solucion_pr1(
    *,
    instancia_id: str,
    algoritmo: str,
    autores: list[str],
    camino: list[Pos],
    acciones: list[str],
    coste: int,
    contadores: Contadores,
    heuristica: str | None = None,
    tiempo_s: float | None = None,
    encontrada: bool = True,
) -> dict:
    """Solución de la PR1: camino, coste y estadísticas de ejecución."""
    doc = _cabecera(instancia_id, "PR1", algoritmo, autores)
    doc.update(
        {
            "heuristica": heuristica,
            "encontrada": encontrada,
            "coste": coste,
            "longitud": max(len(camino) - 1, 0),
            "camino": [p.como_lista() for p in camino],
            "acciones": acciones,
            "estadisticas": contadores.como_dict(),
        }
    )
    if tiempo_s is not None:
        doc["tiempo_s"] = round(tiempo_s, 6)
    return doc


def solucion_pr2(
    *,
    instancia_id: str,
    algoritmo: str,
    autores: list[str],
    politica: dict[Pos, str],
    hiperparametros: dict,
    entrenamiento: dict,
    evaluacion: dict,
) -> dict:
    """Solución de la PR2: política aprendida y evaluación de esa política.

    `politica` mapea estado -> acción. `entrenamiento` recoge la curva de
    aprendizaje (recompensa media por ventana de episodios). `evaluacion`
    recoge el resultado de ejecutar la política aprendida sobre episodios de
    prueba: tasa de éxito, coste medio y pasos medios.
    """
    doc = _cabecera(instancia_id, "PR2", algoritmo, autores)
    doc.update(
        {
            "hiperparametros": hiperparametros,
            "politica": {
                f"{p.nivel},{p.fila},{p.col}": a for p, a in sorted(politica.items())
            },
            "entrenamiento": entrenamiento,
            "evaluacion": evaluacion,
        }
    )
    return doc


def solucion_pr3(
    *,
    instancia_id: str,
    algoritmo: str,
    autores: list[str],
    orden: list[int],
    coste: float,
    presupuesto_evaluaciones: int,
    ejecuciones: list[dict],
    convergencia: list[float] | None = None,
    parametros: dict | None = None,
) -> dict:
    """Solución de la PR3: orden de visita y estadística sobre repeticiones.

    `orden` son los índices de los puntos de visita, sin incluir la base.
    `ejecuciones` es una lista con una entrada por repetición, cada una con su
    semilla y su mejor coste: es lo que permite reportar media y desviación en
    lugar de un único número afortunado.
    """
    doc = _cabecera(instancia_id, "PR3", algoritmo, autores)
    costes = [e["coste"] for e in ejecuciones] or [coste]
    media = sum(costes) / len(costes)
    varianza = sum((c - media) ** 2 for c in costes) / len(costes)
    doc.update(
        {
            "parametros": parametros or {},
            "presupuesto_evaluaciones": presupuesto_evaluaciones,
            "orden": orden,
            "coste": coste,
            "resumen": {
                "repeticiones": len(costes),
                "mejor": min(costes),
                "peor": max(costes),
                "media": round(media, 4),
                "desviacion": round(varianza**0.5, 4),
            },
            "ejecuciones": ejecuciones,
        }
    )
    if convergencia is not None:
        doc["convergencia"] = convergencia
    return doc


def guardar_solucion(doc: dict, ruta: str | Path) -> Path:
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return destino


# ---------------------------------------------------------------------------
# Validación (la misma que usa el corrector automático)
# ---------------------------------------------------------------------------
def validar_solucion_pr1(estacion: Estacion, doc: dict) -> list[str]:
    """Comprueba que el camino de una solución PR1 es realmente un camino.

    NO comprueba que el camino sea el mismo que el de referencia: en una
    rejilla hay muchos caminos óptimos distintos y todos son igual de válidos.
    Lo que se comprueba es que sea contiguo, transitable, que empiece y acabe
    donde toca, y que el coste declarado coincida con el coste real.

    Devuelve la lista de problemas encontrados; vacía significa correcto.
    """
    problemas: list[str] = []

    if doc.get("version") != ESQUEMA_VERSION:
        problemas.append(f"version incorrecta: {doc.get('version')!r}")
    if doc.get("instancia") != estacion.identificador:
        problemas.append(
            f"la solución dice resolver {doc.get('instancia')!r} pero la "
            f"instancia es {estacion.identificador!r}"
        )

    if not doc.get("encontrada", True):
        return problemas  # nada más que validar

    camino = [Pos(*p) for p in doc.get("camino", [])]
    if not camino:
        problemas.append("el camino está vacío")
        return problemas

    if camino[0] != estacion.origen:
        problemas.append(f"el camino empieza en {camino[0]}, no en {estacion.origen}")
    if camino[-1] != estacion.destino:
        problemas.append(f"el camino acaba en {camino[-1]}, no en {estacion.destino}")

    coste_real = 0
    for i, (a, b) in enumerate(zip(camino, camino[1:])):
        if not estacion.es_transitable(b):
            problemas.append(f"paso {i}: {b} no es transitable")
            continue
        c = estacion.coste_transicion(a, b)
        if c is None:
            problemas.append(f"paso {i}: {a} y {b} no son adyacentes")
            continue
        coste_real += c

    if doc.get("coste") != coste_real:
        problemas.append(
            f"el coste declarado ({doc.get('coste')}) no coincide con el coste "
            f"real del camino ({coste_real})"
        )

    est = doc.get("estadisticas", {})
    faltan = [
        k
        for k in (
            "nodos_generados",
            "nodos_explorados",
            "nodos_expandidos",
            "max_frontera",
            "max_alcanzados",
        )
        if k not in est
    ]
    if faltan:
        problemas.append(f"faltan estadísticas: {', '.join(faltan)}")
    else:
        if not (est["nodos_expandidos"] <= est["nodos_explorados"] <= est["nodos_generados"]):
            problemas.append(
                "las estadísticas son incoherentes: debe cumplirse "
                "expandidos <= explorados <= generados, y se ha recibido "
                f"{est['nodos_expandidos']} <= {est['nodos_explorados']} <= "
                f"{est['nodos_generados']}"
            )

    return problemas


def validar_solucion_pr2(estacion: Estacion, doc: dict) -> list[str]:
    """Comprueba la forma de una solución PR2.

    NO juzga la política: de eso se encarga la reevaluación con
    `ssii_estacion.entorno.evaluar_politica`, que es lo único comparable entre
    entregas. Aquí solo se mira que el documento esté bien formado.
    """
    from .modelo import ACCIONES

    acciones = {a[0] for a in ACCIONES}
    problemas: list[str] = []

    if doc.get("version") != ESQUEMA_VERSION:
        problemas.append(f"version incorrecta: {doc.get('version')!r}")
    if doc.get("instancia") != estacion.identificador:
        problemas.append(
            f"la solución dice resolver {doc.get('instancia')!r} pero la "
            f"instancia es {estacion.identificador!r}"
        )

    politica = doc.get("politica")
    if not isinstance(politica, dict) or not politica:
        problemas.append("la política está vacía o no es un diccionario")
        return problemas

    for clave, accion in politica.items():
        try:
            p = Pos(*(int(x) for x in str(clave).split(",")))
        except (TypeError, ValueError):
            problemas.append(f"política: clave mal formada {clave!r}")
            break
        if not estacion.es_transitable(p):
            problemas.append(f"política: {p} no es una posición transitable")
            break
        if accion not in acciones:
            problemas.append(f"política: acción desconocida {accion!r} en {p}")
            break

    for campo in ("hiperparametros", "entrenamiento", "evaluacion"):
        if not isinstance(doc.get(campo), dict) or not doc[campo]:
            problemas.append(f"falta el bloque {campo}")

    ev = doc.get("evaluacion", {})
    if isinstance(ev, dict) and ev:
        tasa = ev.get("tasa_exito")
        if not isinstance(tasa, (int, float)) or not 0 <= tasa <= 1:
            problemas.append(f"evaluacion.tasa_exito fuera de rango: {tasa!r}")
        if not isinstance(ev.get("pasos_medios"), (int, float)):
            problemas.append("evaluacion.pasos_medios ausente o no numérico")

    hiper = doc.get("hiperparametros", {})
    if isinstance(hiper, dict):
        faltan = [k for k in ("alpha", "gamma", "episodios") if k not in hiper]
        if faltan:
            problemas.append(f"hiperparametros: faltan {', '.join(faltan)}")

    return problemas


def validar_solucion_pr3(matriz: list[list[int]], doc: dict) -> list[str]:
    """Comprueba una solución PR3 contra la matriz oficial de la instancia.

    No se compara el orden con el de referencia —hay muchos recorridos buenos y
    dos ejecuciones con semillas distintas dan permutaciones distintas—, sino
    que el orden sea válido, que el coste declarado sea el real, que el
    presupuesto de evaluaciones se haya respetado y que el resumen cuadre con
    las repeticiones que se reportan.
    """
    from .recorrido import coste_recorrido, orden_valido

    problemas: list[str] = []
    n = len(matriz) - 1

    if doc.get("version") != ESQUEMA_VERSION:
        problemas.append(f"version incorrecta: {doc.get('version')!r}")

    orden = doc.get("orden")
    if not isinstance(orden, list) or not orden_valido(orden, n):
        problemas.append(f"el orden no es una permutación de los {n} puntos: {orden!r}")
        return problemas

    real = coste_recorrido(matriz, orden)
    if doc.get("coste") != real:
        problemas.append(
            f"el coste declarado ({doc.get('coste')}) no coincide con el coste "
            f"real del recorrido ({real})")

    presupuesto = doc.get("presupuesto_evaluaciones")
    if not isinstance(presupuesto, int) or presupuesto <= 0:
        problemas.append(f"presupuesto_evaluaciones inválido: {presupuesto!r}")
        presupuesto = None

    ejecuciones = doc.get("ejecuciones")
    if not isinstance(ejecuciones, list) or len(ejecuciones) < 2:
        problemas.append("hacen falta varias repeticiones con sus semillas")
        return problemas

    semillas = set()
    costes = []
    for k, e in enumerate(ejecuciones):
        if not isinstance(e, dict) or "semilla" not in e or "coste" not in e:
            problemas.append(f"ejecuciones[{k}]: falta la semilla o el coste")
            return problemas
        semillas.add(e["semilla"])
        costes.append(e["coste"])
        gastadas = e.get("evaluaciones")
        if presupuesto and isinstance(gastadas, int) and gastadas > presupuesto + 1:
            problemas.append(
                f"ejecuciones[{k}]: {gastadas} evaluaciones con un presupuesto "
                f"de {presupuesto}")
    if len(semillas) != len(ejecuciones):
        problemas.append("hay repeticiones que comparten semilla")

    resumen = doc.get("resumen", {})
    media = sum(costes) / len(costes)
    desviacion = (sum((c - media) ** 2 for c in costes) / len(costes)) ** 0.5
    esperado = {"repeticiones": len(costes), "mejor": min(costes), "peor": max(costes)}
    for campo, valor in esperado.items():
        if resumen.get(campo) != valor:
            problemas.append(f"resumen.{campo} dice {resumen.get(campo)}, deberían ser {valor}")
    for campo, valor in (("media", media), ("desviacion", desviacion)):
        if not isinstance(resumen.get(campo), (int, float)) or abs(resumen[campo] - valor) > 0.01:
            problemas.append(f"resumen.{campo} dice {resumen.get(campo)}, deberían ser {valor:.4f}")

    if doc.get("coste") != min(costes):
        problemas.append(
            f"el coste entregado ({doc.get('coste')}) no es el mejor de las "
            f"repeticiones ({min(costes)})")

    return problemas
