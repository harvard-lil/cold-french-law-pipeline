"""
This export script:
- Pulls the latest LEGI dataset from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
- Decompresses it and extract only currently applicable LEGIARTI files
- Creates CSV files split by "nature"

More info on the upstream dataset:
https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/
"""
import re
import os
import tarfile
import glob

import requests

LEGI_BASE_URL = "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"
""" Base URL for the LEGI dataset. """

RAW_PATH = os.path.join(os.getcwd(), "raw")
""" Path in which to write .tar.gz files. """

DECOMPRESSED_PATH = os.path.join(os.getcwd(), "decompressed")
""" Path in which the .tar.gz files will be decompressed. """


def download_latest_dataset() -> bool:
    """
    Lists and downloads .tar.gz files to download from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
    """
    os.makedirs(RAW_PATH, exist_ok=True)

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

    return True


def decompress_and_filter() -> bool:
    """
    Decompresses the .tar.gz files downloaded previously and:
    - Only LEGIARTI files from "xyz/legi/global/code_et_TNC_en_vigueur"
    - Uses "liste_suppression_legi.dat" to delete obsolete LEGIARTI entries.
    """
    os.makedirs(DECOMPRESSED_PATH, exist_ok=True)

    to_delete = set()

    filepaths = glob.glob(f"{RAW_PATH}/LEGI_*.tar.gz")

    #
    # Decompress and filter files
    #
    for i in range(0, len(filepaths)):
        filepath = filepaths[i]
        print(f"Decompressing file {i+1} of {len(filepaths)}")

        with tarfile.open(filepath) as tar:
            #
            # Create a tar-specific directory
            #
            root_dir = os.path.join(DECOMPRESSED_PATH, tar.members[0].name)
            os.makedirs(root_dir, exist_ok=True)

            #
            # Filter files from tar
            #
            for member in tar.getmembers():
                # List entries from `liste_suppression_legi.dat`:
                # This file is used to indicate which entries need to be deleted from the corpus.
                # We only keep trace of the filename, which is a unique identifier.
                if member.name.endswith("liste_suppression_legi.dat"):
                    raw = tar.extractfile(member).read()
                    lines = str(raw, encoding="utf-8").split("\n")

                    for line in lines:
                        identifier = line.split("/")[-1]

                        if identifier and identifier.startswith("LEGIARTI"):
                            to_delete.add(identifier)

                # List and extract LEGIARTI files from "code_et_TNC_en_vigueur"
                if "code_et_TNC_en_vigueur" in member.name:
                    filename = member.name.split("/")[-1]  # Extract filename

                    if not filename.startswith("LEGIARTI"):
                        continue

                    output = os.path.join(DECOMPRESSED_PATH, root_dir, filename)

                    raw = tar.extractfile(member).read()
                    with open(output, "wb") as file:
                        file.write(raw)

    #
    # Clear up LEGIARTI files marked for deletion
    #
    for identifier in to_delete:
        for found in glob.glob(f"{DECOMPRESSED_PATH}/*/{identifier}.xml"):
            print(f"{found.split('/')[-1]} was marked as repealed - deleting")
            os.unlink(found)

    return True


def export():
    """
    Orchestration function.
    """
    decompress_and_filter()


if __name__ == "__main__":
    export()
