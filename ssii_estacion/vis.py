"""Visualización de la estación, planta a planta.

COMÚN a las tres prácticas:

* `dibujar` (PR1 y PR3): las plantas con un camino o unos puntos superpuestos.
* `dibujar_politica` (PR2): una flecha por posición con la acción de la
  política y, si se le da la tabla Q o las utilidades U, el valor de fondo.

Con tres o más niveles, un dibujo 3D es ilegible y no sirve para depurar. Lo
que sí sirve es una fila de plantas en 2D, con las escotillas marcadas y el
camino superpuesto. Es lo que se entrega al alumnado.
"""

from __future__ import annotations

# No se fija el backend: en Jupyter se usa el inline y la figura se muestra;
# fuera de un entorno gráfico matplotlib cae solo en Agg.
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from .modelo import Estacion, Pos

# 0 mamparo · 1 pasillo · 2 baja gravedad · 3 conducto técnico
COLORES = ListedColormap(["#2F3640", "#F5F6FA", "#FFD9A0", "#F0A07C"])
NOMBRES = ["mamparo", "coste 1", "coste 2", "coste 3"]


def dibujar(
    estacion: Estacion,
    *,
    camino: list[Pos] | None = None,
    puntos: dict[str, Pos] | None = None,
    titulo: str | None = None,
    ruta_salida: str | None = None,
    ancho_planta: float = 3.6,
):
    """Dibuja todas las plantas en fila. Devuelve la figura de matplotlib."""
    n = estacion.niveles
    fig, ejes = plt.subplots(
        1, n, figsize=(ancho_planta * n, ancho_planta * estacion.filas / estacion.columnas + 1.2)
    )
    if n == 1:
        ejes = [ejes]

    escotillas: dict[int, list[tuple[int, int]]] = {}
    for con in estacion.conexiones:
        escotillas.setdefault(con["nivel"], []).append((con["fila"], con["col"]))
        escotillas.setdefault(con["nivel"] + 1, []).append((con["fila"], con["col"]))

    for nivel, ax in enumerate(ejes):
        ax.imshow(
            estacion.rejillas[nivel], cmap=COLORES, vmin=0, vmax=3, interpolation="nearest"
        )
        ax.set_title(f"Nivel {nivel}", fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])

        for f, c in escotillas.get(nivel, []):
            ax.plot(c, f, marker="s", markersize=6, markerfacecolor="none",
                    markeredgecolor="#0B7285", markeredgewidth=1.8)

        if camino:
            tramo = [p for p in camino if p.nivel == nivel]
            # Se dibuja por segmentos contiguos para no unir trozos separados
            seg: list[Pos] = []
            for p in camino:
                if p.nivel == nivel:
                    seg.append(p)
                else:
                    if len(seg) > 1:
                        ax.plot([q.col for q in seg], [q.fila for q in seg],
                                color="#C2255C", linewidth=2.0, solid_capstyle="round")
                    seg = []
            if len(seg) > 1:
                ax.plot([q.col for q in seg], [q.fila for q in seg],
                        color="#C2255C", linewidth=2.0, solid_capstyle="round")
            if tramo:
                ax.plot([q.col for q in tramo], [q.fila for q in tramo], ".",
                        color="#C2255C", markersize=3)

        if puntos:
            for etiqueta, p in puntos.items():
                if p.nivel == nivel:
                    ax.plot(p.col, p.fila, marker="o", markersize=9,
                            markerfacecolor="#2B8A3E" if etiqueta.lower().startswith("o") else "#1864AB",
                            markeredgecolor="white", markeredgewidth=1.4)
                    ax.annotate(etiqueta, (p.col, p.fila), textcoords="offset points",
                                xytext=(7, 6), fontsize=9, color="#212529",
                                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))

    leyenda = [
        plt.Rectangle((0, 0), 1, 1, fc=COLORES(i), ec="#adb5bd") for i in range(4)
    ] + [Line2D([], [], marker="s", color="#0B7285", markerfacecolor="none", linestyle="none", markersize=7)]
    fig.legend(leyenda, NOMBRES + ["escotilla"], loc="lower center", ncol=5,
               frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    if titulo:
        fig.suptitle(titulo, fontsize=12)
    fig.tight_layout()
    if ruta_salida:
        fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# PR2: la política sobre el plano
# ---------------------------------------------------------------------------
_FLECHAS = {"NORTE": (0, -1), "SUR": (0, 1), "ESTE": (1, 0), "OESTE": (-1, 0)}
_SIN_VISITAR = "#868E96"
_DISTINTA = "#C92A2A"


def dibujar_politica(
    entorno,
    politica: dict,
    *,
    Q: dict | None = None,
    U: dict | None = None,
    comparar_con: dict | None = None,
    titulo: str | None = None,
    ruta_salida: str | None = None,
    ancho_planta: float = 4.2,
):
    """Dibuja una política de la PR2 sobre las plantas de la estación.

    En cada posición transitable se dibuja la acción que elige la política:
    una flecha para NORTE, ESTE, SUR u OESTE, y un triángulo hacia arriba o
    hacia abajo para SUBIR y BAJAR. Las posiciones que no están en la política
    (el agente no las ha visitado nunca) salen en gris.

    * Sin `Q`, el fondo son los costes de las celdas, como en la PR1.
    * Con `Q`, el fondo es el valor aprendido, max_a Q(s, a): se ve hasta dónde
      se ha propagado la recompensa del destino.
    * Con `U` (las utilidades que calcula iteración de valores), el fondo es
      U(s). `Q` y `U` no se pueden dar a la vez.

    `entorno` puede ser el `EntornoEstacion` o el `ModeloEstacion`.
    * Con `comparar_con` (otra política), las acciones que difieren de ella se
      dibujan en rojo.

    El plano lo lee el paquete del entorno solo para dibujarlo: el agente sigue
    sin verlo, y el código de la práctica no necesita tocarlo.
    Devuelve la figura de matplotlib.
    """
    if Q is not None and U is not None:
        raise ValueError("da Q o U, no los dos")
    V = U
    if Q is not None:
        V = {s: max(q.values()) for s, q in Q.items() if q}
    estacion = entorno._est
    destino = estacion.destino
    n = estacion.niveles
    con_valor = V is not None
    fig, ejes = plt.subplots(
        1, n, figsize=(ancho_planta * n + (1.0 if (Q is not None or U is not None) else 0),
                       ancho_planta * estacion.filas / estacion.columnas + 1.0)
    )
    if n == 1:
        ejes = [ejes]

    if con_valor:
        valores = sorted(V.values())
        vmin = valores[len(valores) // 20] if valores else 0
        vmax = valores[-1] if valores else 1
        mapa_valor = plt.get_cmap("viridis")
    # Tamaño de las flechas en función de cuántas celdas hay por planta
    escala = max(6.0, 9.0 * 10 / max(estacion.filas, estacion.columnas))
    largo = 0.32

    imagen = None
    for nivel, ax in enumerate(ejes):
        rejilla = estacion.rejillas[nivel]
        if con_valor:
            # Mamparos en oscuro; el resto, con el valor aprendido
            ax.imshow([[0 if v == 0 else 1 for v in fila] for fila in rejilla],
                      cmap=ListedColormap([COLORES(0), "#FFFFFF"]), vmin=0, vmax=1,
                      interpolation="nearest")
            matriz = [[float("nan")] * estacion.columnas for _ in range(estacion.filas)]
            for p, v in V.items():
                if p.nivel == nivel:
                    matriz[p.fila][p.col] = v
            imagen = ax.imshow(matriz, cmap=mapa_valor, vmin=vmin, vmax=vmax,
                               interpolation="nearest")
            color_accion = "white"
        else:
            ax.imshow(rejilla, cmap=COLORES, vmin=0, vmax=3, interpolation="nearest")
            color_accion = "#343A40"
        ax.set_title(f"Nivel {nivel}", fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])

        for f in range(estacion.filas):
            for c in range(estacion.columnas):
                if rejilla[f][c] == 0:
                    continue
                p = Pos(nivel, f, c)
                if p == destino:
                    continue
                accion = politica.get(p)
                if accion is None:
                    ax.add_patch(Rectangle((c - .5, f - .5), 1, 1, fc=_SIN_VISITAR,
                                           ec="none", alpha=.6))
                    continue
                distinta = comparar_con is not None and comparar_con.get(p) not in (None, accion)
                color = _DISTINTA if distinta else color_accion
                if accion in _FLECHAS:
                    dx, dy = _FLECHAS[accion]
                    ax.annotate("", xy=(c + dx * largo, f + dy * largo),
                                xytext=(c - dx * largo, f - dy * largo),
                                arrowprops=dict(arrowstyle="-|>", color=color,
                                                lw=1.6 if distinta else .9,
                                                mutation_scale=escala))
                else:
                    ax.plot(c, f, marker="^" if accion == "SUBIR" else "v", color=color,
                            markersize=escala * .6, linestyle="none")

        for con in estacion.conexiones:
            if nivel in (con["nivel"], con["nivel"] + 1):
                ax.plot(con["col"], con["fila"], marker="s", markersize=escala + 3,
                        markerfacecolor="none", markeredgecolor="#0B7285", markeredgewidth=1.8)
        for p, color in ((estacion.origen, "#2B8A3E"), (destino, "#1864AB")):
            if p.nivel == nivel:
                ax.plot(p.col, p.fila, marker="o", markersize=9, markerfacecolor=color,
                        markeredgecolor="white", markeredgewidth=1.4)

    leyenda, nombres = [], []
    if not con_valor:
        leyenda += [Rectangle((0, 0), 1, 1, fc=COLORES(i), ec="#adb5bd") for i in range(4)]
        nombres += NOMBRES
    leyenda += [
        Rectangle((0, 0), 1, 1, fc=_SIN_VISITAR, alpha=.6),
        Line2D([], [], marker="s", color="#0B7285", markerfacecolor="none", linestyle="none", markersize=7),
        Line2D([], [], marker="o", color="#2B8A3E", markeredgecolor="white", linestyle="none", markersize=8),
        Line2D([], [], marker="o", color="#1864AB", markeredgecolor="white", linestyle="none", markersize=8),
        Line2D([], [], marker="^", color="#343A40", linestyle="none", markersize=6),
        Line2D([], [], marker="v", color="#343A40", linestyle="none", markersize=6),
    ]
    nombres += ["sin visitar", "escotilla", "origen", "destino", "SUBIR", "BAJAR"]
    if comparar_con is not None:
        leyenda.append(Line2D([], [], color=_DISTINTA, lw=2))
        nombres.append("acción distinta")
    fig.legend(leyenda, nombres, loc="lower center", ncol=len(nombres), frameon=False,
               fontsize=8.5, bbox_to_anchor=(0.5, -0.02))
    if titulo:
        fig.suptitle(titulo, fontsize=12)
    fig.tight_layout(rect=(0, 0.05, 0.93 if con_valor else 1, 1))
    if con_valor and imagen is not None:
        barra = fig.add_axes((0.945, 0.2, 0.012, 0.6))
        fig.colorbar(imagen, cax=barra, label="max_a Q(s, a)" if Q is not None else "U(s)")
    if ruta_salida:
        fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    return fig
