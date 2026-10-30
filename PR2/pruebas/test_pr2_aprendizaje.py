"""Bloque 2 — que aprenda: casos pequeños con respuesta conocida."""

from ayuda_pr2 import entorno_pasillo
from ssii_estacion.entorno import evaluar_politica


def test_aprende_el_pasillo_determinista(q_learning, politica_de):
    """Sin estocasticidad, la política óptima es evidente: siempre al ESTE."""
    entorno = entorno_pasillo(p_exito=1.0)
    Q, _ = q_learning(entorno, 400, semilla=0)
    ev = evaluar_politica(entorno, politica_de(Q), episodios=20)
    assert ev["tasa_exito"] == 1.0, "la política aprendida debe llegar siempre"
    assert ev["pasos_medios"] == 4, "el pasillo son 4 pasos; sobran vueltas"


def test_la_curva_mejora(q_learning):
    entorno = entorno_pasillo(p_exito=0.8)
    _, curva = q_learning(entorno, 600, semilla=0)
    assert curva[-1] > curva[0], f"la recompensa media no mejora: {curva}"


def test_aprende_con_movimiento_estocastico(q_learning, politica_de):
    entorno = entorno_pasillo(p_exito=0.8)
    Q, _ = q_learning(entorno, 800, semilla=0)
    ev = evaluar_politica(entorno, politica_de(Q), episodios=50)
    assert ev["tasa_exito"] >= 0.9, f"tasa de éxito {ev['tasa_exito']:.0%}"


def test_cero_episodios_no_revienta(q_learning):
    Q, curva = q_learning(entorno_pasillo(), 0, semilla=0)
    assert Q == {} and curva == []
