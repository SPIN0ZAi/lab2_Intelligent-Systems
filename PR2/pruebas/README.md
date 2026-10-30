# Pruebas públicas de la PR2

Comprueban el contrato de `q_learning` y `politica_de`, que el agente aprende
en entornos de juguete con respuesta conocida (un pasillo recto de cinco
celdas, con y sin estocasticidad) y que iteración de valores da los valores
óptimos en ese mismo pasillo. **Pasarlas es el mínimo, no la nota**: en la
corrección se ejecutan además otras pruebas que no ves, sobre las instancias
del catálogo.

```bash
pip install pytest          # una sola vez
python3 -m pytest PR2/pruebas -q
```

Por defecto prueban `PR2/Lab2_26-27_ES.ipynb`; con `SSII_ENTREGA=...` se prueba
otro fichero. De tu cuaderno se toman solo las celdas que definen funciones, así
que no hace falta que esté ejecutado.

Qué comprueban:

* `q_learning` devuelve `(Q, curva)`, con una entrada por acción en cada estado
  y un punto de curva por ventana de episodios.
* `politica_de` devuelve acciones válidas para todos los estados de la tabla, y
  aguanta una tabla vacía.
* Dos entrenamientos con la misma semilla dan la misma curva.
* En un pasillo determinista la política llega siempre y en el número mínimo de
  pasos; con movimiento estocástico, llega al menos el 90 % de las veces.
* La curva de aprendizaje mejora entre el principio y el final.
* `iteracion_valores` devuelve `(V, historial)`, con un valor por estado, 0 en el
  destino y un historial que acaba por debajo del umbral.
* En el pasillo determinista, el valor del origen es el que se calcula a mano y
  la política de `politica_desde_valores` es siempre ir al ESTE (también con
  resbalones).
* Con resbalones, V cumple la ecuación de Bellman del modelo, y cambiar gamma
  cambia los valores.
