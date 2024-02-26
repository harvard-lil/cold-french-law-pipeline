# cold-french-law-pipeline

> 🚧 Work in progress

CLI pipeline for generating, storing and transforming the [COLD French Law dataset](https://huggingface.co/datasets/harvard-lil/cold-french-law).

The COLD French Law dataset is a collection of all currently applicable law articles compiled from [France's LEGI dataset](https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/).

---

## Usage

This pipeline requires [Python 3.11+](https://www.python.org/) and [Python Poetry](https://python-poetry.org/).

### 1. Clone this repository
```bash
git clone https://github.com/harvard-lil/cold-french-law-pipeline.git
```

### 2. Install dependencies
```bash
poetry install
```

### 3. Run the "build" script
See options with `--help`:
```
poetry run python build.py
```

See output under `data/legi_csv`.

