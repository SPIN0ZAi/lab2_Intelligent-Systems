# JSON file format

**Intelligent Systems · 3rd year, Computer Engineering · ESII Albacete, UCLM · 2026-27**

Every instance and every solution of the three labs uses the same schema,
`ssii-estacion/1`. This document is the reference: what it says is what the validator
checks.

You do not need to parse any of this by hand: the `ssii_estacion` package provides
`cargar_instancia` (load instance), `solucion_prN` (build solution) and `guardar_solucion`
(save solution). Field names are in Spanish, the same for every group.

---

## 1. Instances

An instance describes the station and the question asked about it.

```json
{
  "version": "ssii-estacion/1",
  "id": "PR1-S-01",
  "metadatos": { "perfil": "S", "estilo": "diafana", "semilla": 2,
                 "celdas_transitables": 86, "curso": "2026-27" },
  "estacion": {
    "niveles": 2,
    "filas": 10,
    "columnas": 10,
    "rejillas": [ [[0,0,0,...],[0,1,1,...], ...], ... ],
    "conexiones": [
      { "nivel": 0, "fila": 7, "col": 7, "coste": 2 }
    ]
  },
  "consulta": { "tipo": "camino", "origen": [0,8,6], "destino": [1,3,1] }
}
```

| Field | Meaning |
|:--|:--|
| `version` | Always `ssii-estacion/1` |
| `id` | Instance identifier; the solution must repeat it |
| `metadatos.perfil` | Size profile: `S`, `M`, `L` or `XL` |
| `metadatos.estilo` | `diafana` (open-plan) or `habitaciones` (rooms with doors) |
| `metadatos.semilla` | Generator seed: the same seed always gives the same station |
| `estacion.niveles`, `filas`, `columnas` | Levels, rows and columns |
| `estacion.rejillas` | `rejillas[n][f][c]` is the **occupancy cost** of the cell |
| `estacion.conexiones` | Hatches: they join `(nivel, fila, col)` with `(nivel+1, fila, col)` |
| `consulta` | The query; the only part that differs between labs |

**Cell costs**: `0` not traversable (bulkhead, hull), `1` corridor, `2` low-gravity bay,
`3` service duct. The perimeter of every level is always `0`.

**Cost of a horizontal step**: `max(cost(u), cost(v))`, the maximum of the two cells. It is
symmetric: going and coming back cost the same.

**Cost of a vertical step**: the `coste` declared by the hatch, the same in both
directions. Vertical movement exists only where a hatch is declared.

### The `consulta` block

| `tipo` | Lab | Fields |
|:--|:--|:--|
| `camino` (path) | Lab 1 | `origen`, `destino` |
| `politica` (policy) | Lab 2 | `origen`, `destino`, `dinamica` |
| `recorrido` (route) | Lab 3 | `base`, `puntos` |

Positions are triples `[level, row, column]`, with the origin at the top-left corner of
each level.

For Lab 2, `dinamica` fixes the stochasticity, the step limit per episode and the rewards:

```json
"dinamica": {
  "p_exito": 0.8,
  "limite_pasos": 400,
  "recompensas": { "objetivo": 100, "paso_por_coste": -1, "colision": -5 }
}
```

`p_exito` is the probability that the chosen action is the executed one, and `limite_pasos`
the maximum number of steps per episode (4 × rows × columns: 400 for S instances, 1,600 for
M); both are part of the dynamics. Among the rewards, `objetivo` is the reward for reaching
the destination, `paso_por_coste` the reward per unit of movement cost, and `colision` the
reward for hitting a wall.

### Validation

`cargar_instancia()` validates the whole document and fails with a message saying exactly
what is wrong (the messages are in Spanish):

```
conexiones[3]: la escotilla (1,4,7) une celdas no transitables; ambos extremos deben ser transitables
estacion.rejillas[0][3][5] = 7: el coste de celda debe ser un entero entre 0 (no transitable) y 3
consulta.origen: se esperaba [nivel, fila, columna], se recibió [2, 4]
```

---

## 2. Solutions

All three share the same header:

| Field | Meaning |
|:--|:--|
| `version` | `ssii-estacion/1` |
| `practica` | `PR1`, `PR2` or `PR3` |
| `instancia` | The `id` of the instance solved |
| `algoritmo` | Algorithm name, as required by the lab script |
| `autores` | List of authors of the submission |

### 2.1. Lab 1 — `camino`

```json
{
  "version": "ssii-estacion/1", "practica": "PR1", "instancia": "PR1-S-01",
  "algoritmo": "a_estrella_h2", "autores": ["...", "..."],
  "heuristica": "h2_manhattan_conexiones",
  "encontrada": true,
  "coste": 18,
  "longitud": 13,
  "camino": [[0,8,6],[0,7,6],[0,7,7],[1,7,7], ..., [1,3,1]],
  "acciones": ["NORTE","ESTE","SUBIR","OESTE", ..., "NORTE"],
  "estadisticas": {
    "nodos_generados": 254, "nodos_explorados": 81, "nodos_expandidos": 76,
    "max_frontera": 21, "max_alcanzados": 82
  },
  "tiempo_s": 0.000431
}
```

`encontrada` means "found", `coste` the cost, `longitud` the number of steps, `camino` the
path and `acciones` the actions. What is checked: the path starts at the origin and ends at
the destination, every step joins positions that really are adjacent and traversable,
`coste` matches the recomputed cost, it is optimal when the algorithm guarantees it, and
the five counters satisfy `expandidos ≤ explorados ≤ generados` and match the reference
ones. `acciones` always has one entry fewer than `camino`.

### 2.2. Lab 2 — `politica`

```json
{
  "practica": "PR2", "instancia": "PR2-S-01", "algoritmo": "q_learning",
  "hiperparametros": { "alpha": 0.2, "gamma": 0.95, "eps0": 1.0,
                       "eps_min": 0.05, "episodios": 3000, "semilla": 1 },
  "politica": { "1,6,8": "OESTE", "1,5,7": "NORTE", "...": "..." },
  "entrenamiento": { "episodios": 3000, "ventana": 100,
                     "curva": [-1104.6, ..., 63.78],
                     "tiempo_s": 0.9, "estados_visitados": 87 },
  "evaluacion": { "episodios": 200, "semilla": 12345, "tasa_exito": 1.0,
                  "recompensa_media": 66.22, "recompensa_desv": 9.51,
                  "pasos_medios": 16.79, "coste_medio": 27.95 }
}
```

The keys of `politica` are positions written as `"level,row,column"`, and the values are
one of the six actions. What is marked is the **behaviour of the policy**: it is run again
with the marking seed and the numbers declared under `evaluacion` (success rate, mean
reward and its standard deviation, mean steps, mean cost) have to come out again. The Q
table is not submitted.

### 2.3. Lab 3 — `recorrido`

```json
{
  "practica": "PR3", "instancia": "PR3-M-08p", "algoritmo": "colinas_2opt",
  "parametros": { "repeticiones": 10 },
  "presupuesto_evaluaciones": 5000,
  "orden": [3, 1, 7, 5, 8, 2, 6, 4],
  "coste": 126,
  "resumen": { "repeticiones": 10, "mejor": 126, "peor": 126,
               "media": 126.0, "desviacion": 0.0 },
  "ejecuciones": [ { "semilla": 100, "coste": 126, "evaluaciones": 5001 }, ... ],
  "convergencia": [188, 140, 126, ...]
}
```

`orden` holds the indices of the visit points **without the base**, which is always 0 and
goes at the start and at the end. `presupuesto_evaluaciones` is the evaluation budget,
`ejecuciones` the repetitions (each with its seed, cost and evaluations used), and
`resumen` the summary: repetitions, best, worst, mean and standard deviation. What is
checked: the order is a valid permutation, `coste` matches the cost recomputed over the
official matrix, no run exceeds the declared budget, there are at least two repetitions
with different seeds, and `resumen` agrees with `ejecuciones`.

### 2.4. Distance matrices (Lab 3)

They are provided ready-made, one per instance:

```json
{ "version": "ssii-estacion/1", "instancia": "PR3-M-08p",
  "puntos": [[1,10,13], [2,4,7], ...],
  "matriz": [[0, 5, 9, ...], [5, 0, 14, ...], ...] }
```

`puntos[0]` is the base. `matriz[i][j]` is the optimal cost of going from *i* to *j*,
computed with A\* over the station. The matrix is symmetric and satisfies the triangle
inequality, which is what makes the 2-opt operator valid.

---

## Appendix · Field names

| Spanish | English |
|:--|:--|
| `estacion`, `niveles`, `filas`, `columnas` | station, levels, rows, columns |
| `rejillas`, `conexiones` | grids, hatches |
| `consulta`, `origen`, `destino` | query, origin, destination |
| `base`, `puntos`, `orden` | base, visit points, visiting order |
| `camino`, `acciones`, `coste`, `longitud` | path, actions, cost, number of steps |
| `encontrada` | whether a solution was found |
| `politica`, `recompensas`, `p_exito` | policy, rewards, success probability |
| `tasa_exito`, `pasos_medios`, `coste_medio` | success rate, mean steps, mean cost |
| `presupuesto_evaluaciones`, `ejecuciones` | evaluation budget, runs |
| `resumen`, `mejor`, `peor`, `media`, `desviacion` | summary, best, worst, mean, std. deviation |
