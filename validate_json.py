import os
import json
import glob

import click

from const import JSON_EXPORT_KEYS


@click.command()
@click.argument("path")
def validate_json(path):
    """
    Checks that a set of JSON files are in a format that matches what export_as_json generates.
    """
    if not path.endswith(".json"):
        click.echo("Provided path must target .json files.")
        exit(1)

    files_to_check = glob.glob(path)

    if len(files_to_check) < 1:
        click.echo("No files to check.")
        return

    checked = 0
    valid = 0
    invalid = 0
    for filepath in files_to_check:
        try:
            checked += 1

            with open(filepath, "r") as file:
                entry = json.load(file)

            for key in JSON_EXPORT_KEYS:
                assert key in entry

            valid += 1
        except Exception:
            click.echo(f"{filepath} is invalid")
            invalid += 1

    click.echo(f"{checked} files checked, {valid} valid, {invalid} invalid.")


if __name__ == "__main__":
    validate_json()
