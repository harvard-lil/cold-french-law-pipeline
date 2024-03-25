# cold-french-law-pipeline

CLI pipeline for generating, storing and transforming the [COLD French Law dataset](https://huggingface.co/datasets/harvard-lil/cold-french-law).

The COLD French Law dataset is a collection of currently applicable law articles filtered from [France's LEGI dataset](https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/). 

English translations generated by OpenAI's GPT-4 are available for ~800K articles, provided by [Casetext](https://casetext.com/).

> ⚠️ This process is transformative and, while data is sourced from [France's LEGI dataset](https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/):
> - The accuracy of the data going in and out of this pipeline cannot be guaranteed.  
> - This pipeline and resulting dataset are unofficial and experimental

---

## Usage

This pipeline requires [Python 3.11+](https://www.python.org/) and [Python Poetry](https://python-poetry.org/).

Pulling and pushing data from [HuggingFace](https://huggingface.co/) may require the [HuggingFace CLI](https://huggingface.co/docs/huggingface_hub/en/guides/cli) and [valid authentication](https://huggingface.co/docs/huggingface_hub/en/guides/cli#huggingface-cli-login).

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
# See: build.py --help for a list of available options
poetry run python build.py
```

See output under `data/cold_csv`.

### 4. Upload to HuggingFace (optional)
Will attempt to upload the resulting CSV file to `harvard-lil/cold-french-law`

```
poetry run python upload.py
```