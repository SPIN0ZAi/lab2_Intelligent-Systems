"""Bloque 3 — iteración de valores: casos pequeños con respuesta conocida."""

import pytest

from ayuda_pr2 import modelo_pasillo
from ssii_estacion.modelo import ACCIONES

ACCIONES_VALIDAS = {a[0] for a in ACCIONES}


def residuo_bellman(modelo, U, gamma):
    """El mayor |U(s) - max_a sum p (r + gamma U(s'))|: 0 si U es el valor óptimo."""
    peor = 0.0
    for s in modelo.estados:
        if modelo.es_terminal(s):
            continue
        mejor = max(sum(p * (r + gamma * U[s2]) for p, s2, r in modelo.transiciones(s, a))
                    for a in modelo.acciones)
        peor = max(peor, abs(U[s] - mejor))
    return peor


def test_devuelve_valores_e_historial(iteracion_valores):
    modelo = modelo_pasillo()
    salida = iteracion_valores(modelo, gamma=0.95)
    assert isinstance(salida, tuple) and len(salida) == 2, "devuelve (U, historial)"
    U, historial = salida
    assert set(U) == set(modelo.estados), "una utilidad por cada estado del modelo"
    assert U[modelo.destino] == 0, "el destino es terminal: su utilidad es 0"
    assert historial and historial[-1] < 1e-4, f"no ha convergido: {historial[-3:]}"


def test_valor_del_pasillo_determinista(iteracion_valores):
    """Cuatro pasos de coste 1 hasta el destino (+100): el valor se calcula a mano."""
    modelo = modelo_pasillo(p_exito=1.0)
    U, _ = iteracion_valores(modelo, gamma=0.95)
    esperado = -1 - 0.95 - 0.95 ** 2 + 0.95 ** 3 * 99
    assert U[modelo.origen] == pytest.approx(esperado, abs=1e-3)


def test_politica_del_pasillo(iteracion_valores, politica_desde_valores):
    for p_exito in (1.0, 0.8):
        modelo = modelo_pasillo(p_exito=p_exito)
        U, _ = iteracion_valores(modelo, gamma=0.95)
        politica = politica_desde_valores(modelo, U, gamma=0.95)
        assert set(politica) == {s for s in modelo.estados if not modelo.es_terminal(s)}
        assert set(politica.values()) == {"ESTE"}, f"con p_exito={p_exito}: {politica}"


def test_cumple_bellman_con_resbalones(iteracion_valores):
    """Con movimiento estocástico, U tiene que satisfacer la ecuación de Bellman."""
    modelo = modelo_pasillo(p_exito=0.8)
    U, _ = iteracion_valores(modelo, gamma=0.95)
    assert residuo_bellman(modelo, U, 0.95) < 1e-3, "U no satisface la ecuación de Bellman"


def test_gamma_se_usa(iteracion_valores):
    modelo = modelo_pasillo(p_exito=0.8)
    a, _ = iteracion_valores(modelo, gamma=0.95)
    b, _ = iteracion_valores(modelo, gamma=0.5)
    assert a[modelo.origen] != pytest.approx(b[modelo.origen]), "gamma no se está usando"
