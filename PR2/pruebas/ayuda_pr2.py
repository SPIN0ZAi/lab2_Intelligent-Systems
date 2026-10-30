"""Utilidades de las pruebas públicas de la PR2: entornos de juguete."""

from ssii_estacion.entorno import EntornoEstacion, ModeloEstacion
from ssii_estacion.modelo import Estacion, Pos

RECOMPENSAS = {"objetivo": 100, "paso_por_coste": -1, "colision": -5}
LIMITE_PASOS = 100


def estacion(rejillas, origen, destino, *, conexiones=(), p_exito=1.0,
             recompensas=None, identificador="prueba"):
    est = Estacion([[list(f) for f in n] for n in rejillas], list(conexiones),
                   identificador=identificador)
    est.origen, est.destino = Pos(*origen), Pos(*destino)
    est.p_exito = p_exito
    est.recompensas = dict(recompensas or RECOMPENSAS)
    est.limite_pasos = LIMITE_PASOS
    return est


PASILLO = [[0, 0, 0, 0, 0, 0, 0],
           [0, 1, 1, 1, 1, 1, 0],
           [0, 0, 0, 0, 0, 0, 0]]


def entorno_pasillo(*, p_exito=1.0, semilla=0, recompensas=None) -> EntornoEstacion:
    """Un pasillo recto de cinco celdas: la política óptima es ir siempre al ESTE."""
    est = estacion([PASILLO], (0, 1, 1), (0, 1, 5), p_exito=p_exito,
                   recompensas=recompensas, identificador="pasillo")
    return EntornoEstacion(est, semilla=semilla)


def modelo_pasillo(*, p_exito=1.0) -> ModeloEstacion:
    """El mismo pasillo, como modelo completo para iteración de valores."""
    est = estacion([PASILLO], (0, 1, 1), (0, 1, 5), p_exito=p_exito, identificador="pasillo")
    return ModeloEstacion(est)


def entorno_callejon(*, semilla=0) -> EntornoEstacion:
    """Una sola celda transitable además del origen: sirve para probar choques."""
    rejilla = [[0, 0, 0],
               [0, 1, 0],
               [0, 0, 0]]
    est = estacion([rejilla], (0, 1, 1), (0, 1, 1), identificador="callejon")
    est.destino = Pos(0, 1, 1)
    return EntornoEstacion(est, semilla=semilla)
