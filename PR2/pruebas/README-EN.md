# Public tests, Lab 2

They check the contract of `q_learning` and `politica_de` and that the agent learns in toy
environments with a known answer (a straight five-cell corridor, with and without
stochasticity). **Passing them is the minimum, not the mark**: marking runs further tests
you do not see, on the catalogue instances.

```bash
pip install pytest          # once
python3 -m pytest PR2/pruebas -q
```

By default they test `PR2/Lab2_26-27_ES.ipynb`; with `SSII_ENTREGA=...` you can test
another file, such as `PR2/Lab2_26-27_EN.ipynb`. Only the cells that define functions are
executed, so the notebook does not need to have been run.

What they check:

* `q_learning` returns `(Q, curva)`, with one entry per action in every state and one
  curve point per window of episodes.
* `politica_de` returns valid actions for every state of the table, and copes with an
  empty table.
* Two training runs with the same seed give the same curve.
* In a deterministic corridor the learnt policy always arrives, and in the minimum number
  of steps; with stochastic movement it arrives at least 90 % of the time.
* The learning curve improves between the start and the end.
* `iteracion_valores` returns `(V, historial)`, with one value per state, 0 at the
  destination, and a history that ends below the threshold.
* In the deterministic corridor, the value of the origin is the one computed by hand and
  the policy from `politica_desde_valores` is always to go EAST (also with slips).
* With slips, V satisfies the Bellman equation of the model, and changing gamma changes
  the values.

> The failure messages are in Spanish: the test suite is shared by all groups, so that
> everyone is marked with exactly the same checks.
