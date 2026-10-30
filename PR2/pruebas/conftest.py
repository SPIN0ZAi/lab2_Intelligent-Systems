"""Configuración de las pruebas públicas de la PR2.

Por defecto se prueba el cuaderno `Lab2_26-27_ES.ipynb` de la carpeta superior.
Para probar otro fichero:

    SSII_ENTREGA=ruta/al/cuaderno.ipynb python3 -m pytest PR2/pruebas -q
"""

import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from ssii_estacion.entrega import FUNCIONES_PR2, cargar_entrega   # noqa: E402

ENTREGA_POR_DEFECTO = RAIZ / "PR2" / "Lab2_26-27_ES.ipynb"


@pytest.fixture(scope="session")
def entrega():
    ruta = os.environ.get("SSII_ENTREGA") or ENTREGA_POR_DEFECTO
    return cargar_entrega(ruta, funciones=FUNCIONES_PR2)


@pytest.fixture(scope="session")
def q_learning(entrega):
    return entrega["q_learning"]


@pytest.fixture(scope="session")
def politica_de(entrega):
    return entrega["politica_de"]


@pytest.fixture(scope="session")
def iteracion_valores(entrega):
    return entrega["iteracion_valores"]


@pytest.fixture(scope="session")
def politica_desde_valores(entrega):
    return entrega["politica_desde_valores"]
