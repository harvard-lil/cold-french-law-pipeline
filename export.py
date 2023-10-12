"""
This export script:
- Pulls the latest LEGI dataset from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
- Decompresses it and recombines it (i.e: delete obsolete items)
- Extracts relevant XML files from it: currently applicable LEGIART
- Creates a CSV compiling relevant articles
"""
import re
import os

import requests

LEGI_BASE_URL = "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"
""" Base URL for the LEGI dataset. """

RAW_PATH = os.path.join(os.getcwd(), "raw")
""" Path in which to write .tar.gz files """


def download_latest_dataset() -> list:
    """
    Lists and downloads .tar.gz files to download from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
    """
    html = requests.get(LEGI_BASE_URL)
    filenames = re.findall("LEGI_[a-zA-Z0-9./?=_%:-]*.tar.gz", html.text)
    filenames = list(set(filenames))  # Deduping

    if not filenames:
        raise Exception("No LEGI_XXXXXXXX-XXXXXX.tar.gz file to download")

    for filename in filenames:
        filepath = os.path.join(RAW_PATH, filename)

        if os.path.isfile(filepath):
            print(f"{filename} already exists - skipping.")
            continue

        with open(filepath, "wb") as file:
            print(f"Downloading {filename}")
            response = requests.get(f"{LEGI_BASE_URL}{filename}", allow_redirects=True)
            file.write(response.content)


def export():
    """
    Orchestration function.
    """
    download_latest_dataset()


if __name__ == "__main__":
    export()
