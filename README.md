# cold-french-law-export

> 🚧 Work in progress

Exports currently applicable law articles from [France's LEGI dataset](https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/) into a single CSV file.

---

## How to
Requires [Python 3.11+](https://www.python.org/) and [Poetry](https://python-poetry.org/).

1. Install project dependencies with `poetry install`
2. Run pipeline with `poetry run python export.py`
3. Export will be under `./csv/LEGI.csv`

We recommend clearing up the `decompressed` and `csv` folders in between runs. 
- The former is used by the script extract relevant `.xml` files from the LEGI dataset for processing
- The latter contains the CSV output of the pipeline.
