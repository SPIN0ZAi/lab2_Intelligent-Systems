# Formato de los ficheros JSON

**Sistemas Inteligentes · 3.º Grado en Ingeniería Informática · ESII Albacete, UCLM · Curso 2026-27**

Todas las instancias y todas las soluciones de las tres prácticas usan el mismo esquema,
`ssii-estacion/1`. Este documento es la referencia: lo que aquí se dice es lo que el
validador comprueba.

Para leer y escribir estos ficheros no hace falta interpretar el formato a mano: el
paquete `ssii_estacion` trae `cargar_instancia`, `solucion_prN` y `guardar_solucion`.

---

## 1. Instancias

Una instancia describe la estación y la pregunta que se hace sobre ella.

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

| Campo | Significado |
|:--|:--|
| `version` | Siempre `ssii-estacion/1` |
| `id` | Identificador de la instancia; la solución tiene que repetirlo |
| `metadatos.perfil` | Tamaño: `S`, `M`, `L` o `XL` |
| `metadatos.estilo` | `diafana` (naves amplias) o `habitaciones` (recintos con puertas) |
| `metadatos.semilla` | Semilla del generador: la misma semilla da siempre la misma estación |
| `estacion.rejillas` | `rejillas[n][f][c]` es el **coste de ocupación** de la celda |
| `estacion.conexiones` | Escotillas: unen `(nivel, fila, col)` con `(nivel+1, fila, col)` |
| `consulta` | La pregunta; es lo único que cambia entre prácticas |

**Costes de celda**: `0` no transitable (mamparo, casco), `1` pasillo, `2` bahía de baja
gravedad, `3` conducto técnico. El perímetro de cada planta es siempre `0`.

**Coste de un paso horizontal**: `max(coste(u), coste(v))`, el máximo de las dos celdas.
Es simétrico: ir y volver cuesta lo mismo.

**Coste de un paso vertical**: el `coste` declarado por la escotilla, igual en los dos
sentidos. Solo hay tránsito vertical donde hay escotilla declarada.

### El bloque `consulta`

| `tipo` | Práctica | Campos |
|:--|:--|:--|
| `camino` | PR1 | `origen`, `destino` |
| `politica` | PR2 | `origen`, `destino`, `dinamica` |
| `recorrido` | PR3 | `base`, `puntos` |

Las posiciones son ternas `[nivel, fila, columna]`, con origen en la esquina superior
izquierda de cada planta.

Para PR2, `dinamica` fija la estocasticidad, el límite de pasos por episodio y las
recompensas:

```json
"dinamica": {
  "p_exito": 0.8,
  "limite_pasos": 400,
  "recompensas": { "objetivo": 100, "paso_por_coste": -1, "colision": -5 }
}
```

`p_exito` es la probabilidad de que se ejecute la acción elegida y `limite_pasos`, el número
máximo de pasos por episodio (4 × filas × columnas: 400 en las instancias S, 1 600 en las M);
los dos son parte de la dinámica. Entre las recompensas, `objetivo` es la de llegar al
destino, `paso_por_coste` la de cada unidad de coste del movimiento y `colision` la de chocar.

### Validación

`cargar_instancia()` valida el documento entero y falla con un mensaje que dice
exactamente qué está mal:

```
conexiones[3]: la escotilla (1,4,7) une celdas no transitables; ambos extremos deben ser transitables
estacion.rejillas[0][3][5] = 7: el coste de celda debe ser un entero entre 0 (no transitable) y 3
consulta.origen: se esperaba [nivel, fila, columna], se recibió [2, 4]
```

---

## 2. Soluciones

Las tres comparten la cabecera:

| Campo | Significado |
|:--|:--|
| `version` | `ssii-estacion/1` |
| `practica` | `PR1`, `PR2` o `PR3` |
| `instancia` | El `id` de la instancia resuelta |
| `algoritmo` | Nombre del algoritmo, tal como lo pide el enunciado |
| `autores` | Lista de autores de la entrega |

### 2.1. PR1 — `camino`

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

Se comprueba que el camino empieza en el origen y acaba en el destino, que cada paso une
posiciones realmente adyacentes y transitables, que `coste` coincide con el coste real
recalculado, que es el óptimo cuando el algoritmo lo garantiza, y que los cinco contadores
cumplen `expandidos ≤ explorados ≤ generados` y coinciden con los de referencia.
`acciones` tiene siempre una entrada menos que `camino`.

### 2.2. PR2 — `politica`

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

Las claves de `politica` son la posición como `"nivel,fila,columna"`, y el valor, una de
las seis acciones. Lo que se corrige es el **comportamiento de la política**: se vuelve a
ejecutar con la semilla de corrección y los números declarados en `evaluacion` tienen que
salir otra vez. La tabla Q no se entrega.

### 2.3. PR3 — `recorrido`

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

`orden` son los índices de los puntos de visita **sin la base**, que es siempre el 0 y va
al principio y al final. Se comprueba que es una permutación válida, que `coste` coincide
con el recalculado sobre la matriz oficial, que ninguna ejecución se pasa del presupuesto
declarado, que hay al menos dos repeticiones con semillas distintas y que `resumen` cuadra
con `ejecuciones`.

### 2.4. Matrices de distancias (PR3)

Se entregan ya calculadas, una por instancia:

```json
{ "version": "ssii-estacion/1", "instancia": "PR3-M-08p",
  "puntos": [[1,10,13], [2,4,7], ...],
  "matriz": [[0, 5, 9, ...], [5, 0, 14, ...], ...] }
```

`puntos[0]` es la base. `matriz[i][j]` es el coste óptimo de ir de *i* a *j*, calculado con
A\* sobre la estación. La matriz es simétrica y cumple la desigualdad triangular, que es lo
que hace válido el operador 2-opt.
