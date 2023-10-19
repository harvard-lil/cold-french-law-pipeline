import os
import json
import csv
import math

import click
from datasets import load_dataset

from const import COLD_CSV_PATH, COLD_JSON_PATH


@click.command()
@click.option(
    "--source",
    type=click.Choice(["hugging-face", "csv"], case_sensitive=False),
    default="hugging-face",
    help="Source from which entries will be loaded from.",
)
@click.option(
    "--limit", default=None, help="If set, will export up to X entries. Helpful for testing."
)
def export_to_json(source="hugging-face", limit=None):
    """
    Exports dataset as individual JSON files with subset of fields.

    Exported fields:
    - article_identifier
    - article_num
    - texte_num
    - texte_nature
    - texte_ministere
    - texte_titre
    - texte_titre_court
    - texte_contexte
    - article_contenu
    """
    os.makedirs(COLD_JSON_PATH, exist_ok=True)

    if limit is None:
        limit = math.inf
    else:
        limit = int(limit)

    if source == "hugging-face":
        hf_to_json(limit)
    elif source == "csv":
        csv_to_json(limit)


def hf_to_json(limit=None) -> bool:
    """
    Loads dataset from Hugging Face and exports entries as individual JSON files.
    """
    click.echo("Reading COLD French Law dataset from Hugging Face")

    dataset = load_dataset(
        "harvard-lil/cold-french-law",
        data_files="cold-french-law.csv",
        split="train",
        streaming=True,
    )

    i = 0

    for entry in dataset:
        if i >= limit:
            click.echo(f"Limit reached ({limit})")
            break

        write_json(entry)

        i += 1

    click.echo(f"{i} JSON files written to disk.")
    return True


def csv_to_json(limit=None):
    """
    Loads dataset from local CSV and exports entries as individual JSON files.
    """
    click.echo("Reading COLD French Law dataset from local CSV")

    i = 0

    with open(os.path.join(COLD_CSV_PATH, "cold-french-law.csv"), "r") as data:
        for entry in csv.DictReader(data):
            if i >= limit:
                click.echo(f"Limit reached ({limit})")
                break

            print(entry)

            write_json(entry)

            i += 1

    click.echo(f"{i} JSON files written to disk.")
    return True


def write_json(entry: dict) -> bool:
    """
    Writes and individual record to JSON.
    """
    identifier = entry["article_identifier"]

    # Use the first 15 chars of each file as directory
    grouping = identifier[0:15]
    os.makedirs(os.path.join(COLD_JSON_PATH, grouping), exist_ok=True)

    filename = os.path.join(COLD_JSON_PATH, grouping, f"{identifier}.json")

    output = {
        "article_identifier": entry["article_identifier"],
        "article_num": entry["article_num"],
        "texte_num": entry["texte_num"],
        "texte_nature": entry["texte_nature"],
        "texte_ministere": entry["texte_ministere"],
        "texte_titre": entry["texte_titre"],
        "texte_titre_court": entry["texte_titre_court"],
        "texte_contexte": entry["texte_contexte"],
        "article_contenu": entry["article_contenu"],
    }

    with open(filename, "w+") as file:
        click.echo(f"{identifier} exported as JSON.")
        json.dump(output, file, ensure_ascii=False)

    return True


if __name__ == "__main__":
    export_to_json()
