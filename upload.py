import os

import click
from huggingface_hub import HfApi

from const import (
    COLD_CSV_FILE,
    HF_REPO_ID,
)


@click.command()
def upload_to_hf() -> None:
    """
    Uploads the COLD_CSV_FILE to HuggingFace
    """
    api = HfApi()

    try:
        assert os.path.exists(COLD_CSV_FILE)
    except Exception:
        click.echo("{filepath} does not exist.")
        exit(1)

    api.upload_file(
        path_or_fileobj=COLD_CSV_FILE,
        path_in_repo=os.path.basename(COLD_CSV_FILE),
        repo_id=HF_REPO_ID,
        repo_type="dataset",
    )


if __name__ == "__main__":
    upload_to_hf()
