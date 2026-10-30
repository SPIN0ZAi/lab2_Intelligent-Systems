# Intelligent Systems labs — academic year 2026-27

University of Castilla-La Mancha · School of Computer Science, Albacete
Computer Engineering, 3rd year

The labs are released **one at a time, as each one starts**. They all go into the same
folder, `SSII-practicas-26-27/`, which grows during the course. This README describes the
**complete** folder, as it will be at the end: if you cannot see some of the folders
below yet, that lab has not been released.

## Structure of the lab folder

```
SSII-practicas-26-27/
├── ssii_estacion/      Support package, shared by the three labs.
│                       Provided by the teaching staff; do NOT modify it
├── catalogo/           The instances of each lab, in JSON
│   ├── pr1/            State space search
│   ├── pr2/            Reinforcement learning
│   └── pr3/            Metaheuristics, with the distance matrices
├── PR1/                State space search
│   ├── Lab1_26-27_ES.ipynb · Lab1_26-27_EN.ipynb
│   └── pruebas/        Public tests
├── PR2/                Reinforcement learning (same structure)
├── PR3/                Metaheuristics (same structure)
├── json-format-EN.md   Format of instances and solutions
├── README.md · README-EN.md
└── requirements.txt
```

Each lab comes in **Spanish** (`_ES`) and **English** (`_EN`): use the one for your group.
They are the same lab.

## The first time

Unzip the `.zip` wherever you like and always work inside the folder it creates: the
notebook paths are relative and assume this structure. You need Python 3.10 or later.
From the `SSII-practicas-26-27/` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate        # on Windows:  .venv\Scripts\activate
pip install -r requirements.txt
```

And to open the notebook of the lab:

```bash
cd PR1
jupyter notebook Lab1_26-27_EN.ipynb
```

VS Code, PyCharm or Colab work too, but on Colab you have to upload the whole folder so
that the notebook can find the package and the catalogue.

## When a new lab is released

The `.zip` of each new lab contains its `PRn/` folder, its part of the catalogue and the
latest version of the `ssii_estacion/` package. **It does not contain the previous labs**,
so it cannot overwrite your work. To add it:

1. Unzip the `.zip` somewhere **else** (not on top of your folder: depending on your
   system, you would get a duplicate folder or a question for every file).
2. Copy the new `PRn/` folder and the `catalogo/prn/` folder into your
   `SSII-practicas-26-27/`.
3. **Replace** your `ssii_estacion/` with the new one, and the `README` files and
   `requirements.txt` too. Since the package is never modified, you lose nothing.
4. If `requirements.txt` has changed, run `pip install -r requirements.txt` again with your
   environment activated.

## The public tests

Every lab ships a battery of tests you can run yourself, as often as you like, to check
that your implementation does what is expected. From the `SSII-practicas-26-27/` folder:

```bash
SSII_ENTREGA=PR1/Lab1_26-27_EN.ipynb python3 -m pytest PR1/pruebas -q
```

The notebook does not need to have been run: only the cells that define functions are
executed. **Passing them is the minimum, not the mark**: marking runs further tests you do
not see. Each `pruebas/` folder has a `README-EN.md` with the details.

## What you submit

The completed notebook and the JSON solution files it produces, as explained in the
submission section of each lab script.

## Common problems

* **`ModuleNotFoundError: ssii_estacion`**: you are running the notebook from another
  folder. Open it from `PRn/`, where the first cell adds the parent folder to `sys.path`.
* **Results that do not add up after editing a cell**: restart the kernel and run
  everything top to bottom (*Kernel → Restart & Run All*). Half of the odd errors are
  stale state.
* **Figures do not show**: check that `matplotlib` is installed in the environment you
  started Jupyter from.

Any questions, come to office hours or use the course forum on Campus Virtual.
