import os
import json
import csv
import math
import sys

import click
from datasets import load_dataset

from const import COLD_CSV_PATH, COLD_TXT_PATH


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
def export_as_txt(source="hugging-face", limit=None):
    """
    Exports dataset as individual TXT files with subset of fields.
    """
    os.makedirs(COLD_TXT_PATH, exist_ok=True)

    if limit is None:
        limit = math.inf
    else:
        limit = int(limit)

    if source == "hugging-face":
        hf_to_txt(limit)
    elif source == "csv":
        csv_to_txt(limit)


def hf_to_txt(limit=None) -> bool:
    """
    Loads dataset from Hugging Face and exports entries as individual TXT files.
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

        write_txt(entry)

        i += 1

    click.echo(f"{i} JSON files written to disk.")
    return True


def csv_to_txt(limit=None):
    """
    Loads dataset from local CSV and exports entries as individual TXT files.
    """
    click.echo("Reading COLD French Law dataset from local CSV")

    csv.field_size_limit(sys.maxsize)

    i = 0

    with open(os.path.join(COLD_CSV_PATH, "cold-french-law.csv"), "r") as data:
        for entry in csv.DictReader(data):
            if i >= limit:
                click.echo(f"Limit reached ({limit})")
                break

            write_txt(entry)

            i += 1

    click.echo(f"{i} TXT files written to disk.")
    return True


def write_txt(entry: dict) -> bool:
    """
    Writes individual record as TXT file.
    """
    identifier = entry["article_identifier"]
    filename = ""
    grouping = "misc"
    sub_grouping = ""
    output = ""

    # Use "texte_nature" as grouping, and "texte_titre_court" or "texte_ministere" as sub grouping
    if entry["texte_nature"] == "CODE":
        grouping = "code"
        sub_grouping = entry["texte_titre_court"].lower()
    elif len(entry["texte_nature"]) > 0:
        grouping = entry["texte_nature"].lower()
        sub_grouping = entry["texte_ministere"].lower()

    os.makedirs(os.path.join(COLD_TXT_PATH, grouping), exist_ok=True)

    if sub_grouping:
        os.makedirs(os.path.join(COLD_TXT_PATH, grouping, sub_grouping), exist_ok=True)

    filename = os.path.join(COLD_TXT_PATH, grouping, sub_grouping, f"{identifier}.txt")

    # Assemble and write output
    if grouping == "code":
        output = f"Article {entry['article_num']} du {entry['texte_titre_court']}.\n"
        output += entry["article_contenu"].strip()
    else:
        output = f"{entry['texte_titre']}\n"
        output += entry["article_contenu"].strip()

    with open(filename, "w+") as file:
        click.echo(f"{identifier} exported as TXT.")
        file.write(output)

    return True


if __name__ == "__main__":
    export_as_txt()
