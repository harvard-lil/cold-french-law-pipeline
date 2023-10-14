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
    Lists and downloads .tar.gz files from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
    - Saves files in "RAW_PATH"
    - Will not download file if already present locally
    """
    os.makedirs(RAW_PATH, exist_ok=True)

    html = requests.get(LEGI_BASE_URL)
    filenames = re.findall("([\w\_\-]+.tar.gz)", html.text)
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
    Decompresses the .tar.gz present in "RAW_PATH".
    - Only extracts LEGIARTI files from "xyz/legi/global/code_et_TNC_en_vigueur"
    - Uses "liste_suppression_legi.dat" to delete obsolete LEGIARTI entries
    - Saves files in "DECOMPRESSED_PATH"
    """
    os.makedirs(DECOMPRESSED_PATH, exist_ok=True)

    to_delete = set()
    filepaths = glob.glob(f"{RAW_PATH}/*.tar.gz")
    filepaths.sort()

    # Decompress and filter files
    for i in range(0, len(filepaths)):
        filepath = filepaths[i]
        print(f"Decompressing file {i+1} of {len(filepaths)}")

        with tarfile.open(filepath) as tar:
            for member in tar.getmembers():
                # List and extract LEGIARTI files from the "code_et_TNC_en_vigueur" folder
                if "code_et_TNC_en_vigueur" in member.name:
                    filename = member.name.split("/")[-1]  # Extract filename

                    if not filename.startswith("LEGIARTI"):
                        continue

                    output = os.path.join(DECOMPRESSED_PATH, filename)

                    raw = tar.extractfile(member).read()

                    with open(output, "wb") as file:
                        file.write(raw)

                # List entries from "liste_suppression_legi.dat":
                # - This file is used to indicate which entries need to be deleted from the corpus.
                # - We only keep trace of the filename, which is a unique identifier.
                if member.name.endswith("liste_suppression_legi.dat"):
                    raw = tar.extractfile(member).read()
                    lines = str(raw, encoding="utf-8").split("\n")

                    for line in lines:
                        identifier = line.split("/")[-1]

                        if identifier and identifier.startswith("LEGIARTI"):
                            to_delete.add(identifier)

    # Clear up LEGIARTI files marked for deletion in "liste_suppression_legi.dat" files
    print(f"{len(to_delete)} obsolete entries were marked for deletion.")

    to_delete_found = 0

    for identifier in to_delete:
        for found in glob.glob(f"{DECOMPRESSED_PATH}/{identifier}.xml"):
            to_delete_found += 1
            os.unlink(found)

    print(f"{to_delete_found} obsolete entries were found and deleted.")

    return True


def xml_to_csv() -> bool:
    """
    Reads through decompressed/*.xml and extracts relevant contents into CSV files
    - Saves files under "CSV_PATH"
    """
    os.makedirs(CSV_PATH, exist_ok=True)

    xmls = glob.glob(f"{DECOMPRESSED_PATH}/*.xml")
    total = len(xmls)
    read = 0
    skipped = 0
    print(f"{total} XML files to process.")

    for xml in xmls:
        print(f"Parsing file {read+1} of {total}.")

        doc = minidom.parse(xml)
        read += 1

        output = {
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
        output["article_identifier"] = doc.getElementsByTagName("ID")[0].firstChild.wholeText

        try:
            output["article_num"] = doc.getElementsByTagName("NUM")[0].firstChild.wholeText
        except Exception:
            pass

        try:
            date_debut = doc.getElementsByTagName("DATE_DEBUT")
            output["article_date_debut"] = date_debut[0].firstChild.wholeText
        except Exception:
            pass

        try:
            date_fin = doc.getElementsByTagName("DATE_FIN")
            output["article_date_fin"] = date_fin[0].firstChild.wholeText
        except Exception:
            pass

        try:
            output["article_etat"] = doc.getElementsByTagName("ETAT")[0].firstChild.wholeText
        except Exception:
            pass

        # Skip entries that are not in "VIGUEUR"
        if len(output["article_etat"]) > 0 and output["article_etat"] != "VIGUEUR":
            skipped += 1
            continue

        # Pull "texte" metadata
        output["texte_nature"] = texte_ref.getAttribute("nature")
        output["texte_ministere"] = texte_ref.getAttribute("ministere")
        output["texte_num"] = texte_ref.getAttribute("nor")
        output["texte_nor"] = texte_ref.getAttribute("nor")
        output["texte_num_parution_jo"] = texte_ref.getAttribute("num_parution_jo")
        output["texte_titre_court"] = titre_txt_ref.getAttribute("c_titre_court")
        output["texte_titre"] = titre_txt_ref.firstChild.wholeText

        # Pull "texte" context
        for ref in titre_tm_ref:
            section = ref.firstChild.wholeText
            if section:
                output["texte_contexte"] += section.strip() + "\n"

        # Pull textual contents for article
        for contenu in doc.getElementsByTagName("CONTENU"):
            try:
                parsed = html2text.html2text(contenu.toxml())
                output["article_contenu"] += parsed
            except Exception:
                pass

        output["article_contenu"] = output["article_contenu"].strip()

        # Determine CSV output path based on the article's "nature"
        csv_filename = os.path.join(CSV_PATH, "MISC.csv")

        if output["texte_nature"] == "CODE":
            code = (
                output["texte_titre"]
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
        elif output["texte_nature"]:
            nature_to_filename = output["texte_nature"].replace(".", "").replace("/", "")

            if nature_to_filename[-1] != "S" and nature_to_filename != "LOI_CONSTIT":
                nature_to_filename += "S"

            csv_filename = os.path.join(CSV_PATH, f"{nature_to_filename}.csv")

        # Write to CSV
        csv_file_exists = False

        if os.path.isfile(csv_filename):
            csv_file_exists = True

        with open(csv_filename, "a", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=output.keys())

            if not csv_file_exists:  # Only write header once
                writer.writeheader()

            writer.writerow(output)

    print(f"{skipped} of {read} article files skipped.")
    print(f"{read - skipped} article files written to CSVs.")
    return True


def export():
    """
    Orchestration function: runs the entire export script
    """
    print(80 * "-")
    print(f"Downloading latest archives from {LEGI_BASE_URL}")
    print(80 * "-")
    download_latest()

    print(80 * "-")
    print("Unpacking (relevant) XML files from archives.")
    print(80 * "-")
    tar_to_xml()

    print(80 * "-")
    print("Parsing XML and saving current entries into CSVs.")
    print(80 * "-")
    xml_to_csv()


if __name__ == "__main__":
    export()
