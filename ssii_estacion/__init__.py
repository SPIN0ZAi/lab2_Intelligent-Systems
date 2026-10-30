"""
ssii_estacion — infraestructura común de las prácticas de Sistemas Inteligentes.

Curso 2026-27. ESII Albacete, UCLM.

Este paquete lo proporciona el profesorado. El alumnado NO debe modificarlo:
implementa algoritmos, no fontanería. Todo lo que hay aquí (carga de
instancias, sucesores en orden canónico, frontera con desempate fijo,
contadores, validación y volcado de soluciones) está pensado para que dos
implementaciones correctas produzcan exactamente los mismos números.

Alcance de cada módulo:

    modelo.py      común        la estación, las posiciones y las acciones
    instancia.py   común        carga y validación de instancias
    solucion.py    común        construcción y validación de soluciones
    vis.py         común        dibujo de las plantas (PR1, PR3) y de las políticas (PR2)
    entrega.py     común        carga de entregas para las pruebas
    busqueda.py    solo PR1     frontera, cerrados, nodos y contadores
    entorno.py     solo PR2     entorno estocástico y opaco (reset / paso)
    recorrido.py   solo PR3     matriz, coste del recorrido y Evaluador
"""

from .modelo import Estacion, Pos, ACCIONES
from .instancia import cargar_instancia, InstanciaInvalida
from .busqueda import Frontera, Cerrados, Contadores, Nodo, reconstruir_camino
from .solucion import (
    solucion_pr1,
    solucion_pr2,
    solucion_pr3,
    guardar_solucion,
    validar_solucion_pr1,
    validar_solucion_pr2,
    validar_solucion_pr3,
)

__version__ = "1.0.0"
ESQUEMA_VERSION = "ssii-estacion/1"

__all__ = [
    "Estacion",
    "Pos",
    "ACCIONES",
    "cargar_instancia",
    "InstanciaInvalida",
    "Frontera",
    "Cerrados",
    "Contadores",
    "Nodo",
    "reconstruir_camino",
    "solucion_pr1",
    "solucion_pr2",
    "solucion_pr3",
    "guardar_solucion",
    "validar_solucion_pr1",
    "validar_solucion_pr2",
    "validar_solucion_pr3",
    "ESQUEMA_VERSION",
    "__version__",
]
