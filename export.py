"""
[!] Work in progress

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
import xml.dom.minidom as minidom
import csv

import requests
import html2text

LEGI_BASE_URL = "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"
""" Base URL for the LEGI dataset. """

RAW_PATH = os.path.join(os.getcwd(), "raw")
""" Path in which to write .tar.gz files. """

DECOMPRESSED_PATH = os.path.join(os.getcwd(), "decompressed")
""" Path in which the .tar.gz files will be decompressed. """

CSV_PATH = os.path.join(os.getcwd(), "csv")
""" Path in which the CSV files will be written. """


def download_latest() -> bool:
    """
    Lists and downloads .tar.gz files to download from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
    """
    os.makedirs(RAW_PATH, exist_ok=True)

    html = requests.get(LEGI_BASE_URL)
    filenames = re.findall("*.tar.gz", html.text)
    filenames = list(set(filenames))  # Deduping

    if not filenames:
        raise Exception("No .tar.gz file to download")

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


def tar_to_xml() -> bool:
    """
    Decompresses the .tar.gz files downloaded previously and:
    - Only LEGIARTI files from "xyz/legi/global/code_et_TNC_en_vigueur"
    - Uses "liste_suppression_legi.dat" to delete obsolete LEGIARTI entries.
    """
    os.makedirs(DECOMPRESSED_PATH, exist_ok=True)

    to_delete = set()
    filepaths = glob.glob(f"{RAW_PATH}/*.tar.gz")
    filepaths.sort()

    #
    # Decompress and filter files
    #
    for i in range(0, len(filepaths)):
        filepath = filepaths[i]
        print(filepath)
        print(f"Decompressing file {i+1} of {len(filepaths)}")

        with tarfile.open(filepath) as tar:
            for member in tar.getmembers():
                # List and extract LEGIARTI files from "code_et_TNC_en_vigueur"
                if "code_et_TNC_en_vigueur" in member.name:
                    filename = member.name.split("/")[-1]  # Extract filename

                    if not filename.startswith("LEGIARTI"):
                        continue

                    output = os.path.join(DECOMPRESSED_PATH, filename)

                    raw = tar.extractfile(member).read()
                    with open(output, "wb") as file:
                        file.write(raw)

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

    #
    # Clear up LEGIARTI files marked for deletion
    #
    for identifier in to_delete:
        for found in glob.glob(f"{DECOMPRESSED_PATH}/{identifier}.xml"):
            print(f"{found.split('/')[-1]} was marked for deletion - deleting")
            os.unlink(found)

    return True


def xml_to_csv() -> bool:
    """
    Reads through decompressed/*/*.xml and extracts relevant contents into CSV files.
    """
    os.makedirs(CSV_PATH, exist_ok=True)

    xmls = glob.glob(f"{DECOMPRESSED_PATH}/*.xml")
    total = len(xmls)
    read = 0
    skipped = 0
    print(f"{total} XML files to process.")

    for xml in xmls:
        print(f"Parsing file {read+1} of {total}")

        doc = minidom.parse(xml)
        read += 1

        entry = {
            "article_identifier": "",
            "article_num": "",
            "article_etat": "",
            "article_date_debut": "",
            "article_date_fin": "",
            "texte_date_publi": "",
            "texte_date_signature": "",
            "texte_nature": "",
            "texte_ministere": "",
            "texte_num": "",
            "texte_nor": "",
            "texte_num_parution_jo": "",
            "texte_titre": "",
            "texte_titre_court": "",
            "texte_contexte": "",
            "article_contenu": "",
        }

        # References to XML nodes
        texte_ref = doc.getElementsByTagName("CONTEXTE")[0].getElementsByTagName("TEXTE")[0]
        titre_txt_ref = doc.getElementsByTagName("CONTEXTE")[0].getElementsByTagName("TITRE_TXT")[0]
        titre_tm_ref = doc.getElementsByTagName("CONTEXTE")[0].getElementsByTagName("TITRE_TM")

        # Pull "article" metadata
        entry["article_identifier"] = doc.getElementsByTagName("ID")[0].firstChild.wholeText

        try:
            entry["article_num"] = doc.getElementsByTagName("NUM")[0].firstChild.wholeText
        except Exception:
            pass

        try:
            date_debut = doc.getElementsByTagName("DATE_DEBUT")
            entry["article_date_debut"] = date_debut[0].firstChild.wholeText
        except Exception:
            print("A")
            pass

        try:
            date_fin = doc.getElementsByTagName("DATE_FIN")
            entry["article_date_fin"] = date_fin[0].firstChild.wholeText
        except Exception:
            print("B")
            pass

        try:
            entry["article_etat"] = doc.getElementsByTagName("ETAT")[0].firstChild.wholeText
        except Exception:
            pass

        # Skip entries that are not in "VIGUEUR"
        if len(entry["article_etat"]) > 0 and entry["article_etat"] != "VIGUEUR":
            skipped += 1
            continue

        # Pull "texte" metadata
        entry["texte_nature"] = texte_ref.getAttribute("nature")
        entry["texte_ministere"] = texte_ref.getAttribute("ministere")
        entry["texte_num"] = texte_ref.getAttribute("nor")
        entry["texte_nor"] = texte_ref.getAttribute("nor")
        entry["texte_num_parution_jo"] = texte_ref.getAttribute("num_parution_jo")
        entry["texte_titre_court"] = titre_txt_ref.getAttribute("c_titre_court")
        entry["texte_titre"] = titre_txt_ref.firstChild.wholeText

        # Pull "texte" context
        for ref in titre_tm_ref:
            section = ref.firstChild.wholeText
            if section:
                entry["texte_contexte"] += section.strip() + "\n"

        # Pull textual contents for article
        for contenu in doc.getElementsByTagName("CONTENU"):
            try:
                parsed = html2text.html2text(contenu.toxml())
                entry["article_contenu"] += parsed
            except Exception:
                pass

        entry["article_contenu"] = entry["article_contenu"].strip()

        # Determine CSV output path based on the article's "nature"
        csv_filename = os.path.join(CSV_PATH, "MISC.CSV")

        if entry["texte_nature"] == "CODE":
            code = (
                entry["texte_titre"]
                .upper()
                .replace(" ", "-")
                .replace("'", "-")
                .replace("_", "-")
                .replace(",", "")
                .replace(".", "")
                .replace("/", "")
                .replace("(", "")
                .replace(")", "")
            )
            csv_filename = os.path.join(CSV_PATH, f"{code}.csv")
        elif entry["texte_nature"]:
            nature_to_filename = entry["texte_nature"].replace(".", "").replace("/", "")

            if nature_to_filename[-1] != "S":
                nature_to_filename += "S"

            csv_filename = os.path.join(CSV_PATH, f"{nature_to_filename}.csv")

        # Write to CSV
        csv_file_exists = False

        if os.path.isfile(csv_filename):
            csv_file_exists = True

        with open(csv_filename, "a", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=entry.keys())

            if not csv_file_exists:  # Only write header once
                writer.writeheader()

            writer.writerow(entry)

    print(f"{skipped} of {read} entries skipped.")
    print(f"{read - skipped} written to CSVs.")
    return True


def export():
    """
    Orchestration function.
    """
    xml_to_csv()


if __name__ == "__main__":
    export()
