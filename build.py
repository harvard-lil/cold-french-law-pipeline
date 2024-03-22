import re
import os
import tarfile
import glob
import xml.dom.minidom as minidom
import csv

import requests
import html2text
from bs4 import BeautifulSoup
import click

import json
import pandas as pd
from huggingface_hub import hf_hub_download, HfApi

from const import LEGI_BASE_URL, LEGI_TAR_PATH, LEGI_UNPACKED_PATH, COLD_CSV_PATH, MERGED_DATA_PATH, REPO_ID, \
    MERGED_DATA_FILE


@click.command()
@click.option(
    "--skip-download",
    is_flag=True,
    required=False,
    default=False,
    help="If set, skips downloading latest archives from the LEGI dataset.",
)
@click.option(
    "--skip-unpack",
    is_flag=True,
    required=False,
    default=False,
    help="If set, skips unpacking XML files from archives.",
)
@click.option(
    "--skip-csv",
    is_flag=True,
    required=False,
    default=False,
    help="If set, skips generating cold-frenchlaw.csv.",
)
@click.option(
    "--skip-merge",
    is_flag=True,
    required=False,
    default=False,
    help="If set, skips merging french and english data.",
)
@click.option(
    "--upload-to-hf",
    is_flag=True,
    required=False,
    default=False,
    help="If set, uploads the merged data csv to HuggingFace.",
)
def build(skip_download=False, skip_unpack=False, skip_csv=False, skip_merge=False, upload_to_hf=False):
    """
    Builds the COLD French Law dataset:
    - Pulls the latest LEGI dataset from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
    - Decompresses it and extract only currently applicable LEGIARTI files
    - Outputs to filtered CSV (data/csv/cold-french-law.csv)

    More info on the upstream dataset:
    https://www.data.gouv.fr/fr/datasets/legi-codes-lois-et-reglements-consolides/
    """
    if skip_download is not True:
        click.echo(80 * "-")
        click.echo(f"Downloading latest archives from {LEGI_BASE_URL}")
        click.echo(80 * "-")
        download_latest()

    if skip_unpack is not True:
        click.echo(80 * "-")
        click.echo("Unpacking (relevant) XML files from archives.")
        click.echo(80 * "-")
        tar_to_xml()

    if skip_csv is not True:
        click.echo(80 * "-")
        click.echo("Parsing XML and saving current entries into CSVs.")
        click.echo(80 * "-")
        xml_to_csv()

    if skip_merge is not True:
        click.echo(80 * "-")
        click.echo("Starting to merge french data with english translations.")
        click.echo(80 * "-")
        merge(upload_to_hf)


def download_latest() -> bool:
    """
    Lists and downloads .tar.gz files from https://echanges.dila.gouv.fr/OPENDATA/LEGI/
    - Saves files in "LEGI_TAR_PATH"
    - Will not download file if already present locally
    """
    os.makedirs(LEGI_TAR_PATH, exist_ok=True)

    html = requests.get(LEGI_BASE_URL)
    filenames = re.findall("([\w\_\-]+.tar.gz)", html.text)
    filenames = list(set(filenames))  # Deduping

    if not filenames:
        raise Exception("No .tar.gz file to download")

    for filename in filenames:
        filepath = os.path.join(LEGI_TAR_PATH, filename)

        if os.path.isfile(filepath):
            click.echo(f"{filename} already exists - skipping.")
            continue

        with open(filepath, "wb") as file:
            click.echo(f"Downloading {filename}")
            response = requests.get(f"{LEGI_BASE_URL}{filename}", allow_redirects=True)
            file.write(response.content)

    return True


def tar_to_xml() -> bool:
    """
    Decompresses the .tar.gz present in "LEGI_TAR_PATH".
    - Only extracts LEGIARTI files from "xyz/legi/global/code_et_TNC_en_vigueur"
    - Uses "liste_suppression_legi.dat" to delete obsolete LEGIARTI entries
    - Saves files in "LEGI_UNPACKED_PATH"
    """
    os.makedirs(LEGI_UNPACKED_PATH, exist_ok=True)

    to_delete = set()
    filepaths = glob.glob(f"{LEGI_TAR_PATH}/*.tar.gz")
    filepaths.sort()

    # Decompress and filter files
    for i in range(0, len(filepaths)):
        filepath = filepaths[i]
        click.echo(f"Decompressing file {i+1} of {len(filepaths)}")

        with tarfile.open(filepath) as tar:
            for member in tar.getmembers():
                # List and extract LEGIARTI files from the "code_et_TNC_en_vigueur" folder
                if "code_et_TNC_en_vigueur" in member.name:
                    filename = member.name.split("/")[-1]  # Extract filename

                    if not filename.startswith("LEGIARTI"):
                        continue

                    # Use the first 15 chars of each file as directory
                    grouping = filename[0:15]
                    os.makedirs(os.path.join(LEGI_UNPACKED_PATH, grouping), exist_ok=True)

                    output = os.path.join(LEGI_UNPACKED_PATH, grouping, filename)

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
    click.echo(f"{len(to_delete)} obsolete entries were marked for deletion.")

    to_delete_found = 0

    for identifier in to_delete:
        filepath = f"{LEGI_UNPACKED_PATH}/{identifier[0:15]}/{identifier}.xml"
        if os.path.isfile(filepath):
            to_delete_found += 1
            os.unlink(filepath)

    click.echo(f"{to_delete_found} obsolete entries were found and deleted.")

    return True


def xml_to_csv() -> bool:
    """
    Reads through LEGI_UNPACKED_PATH/*/*.xml and extracts relevant contents into a CSV file.
    Saves file under "COLD_CSV_PATH"
    """
    os.makedirs(COLD_CSV_PATH, exist_ok=True)

    # List XML files to process
    xmls = glob.glob(f"{LEGI_UNPACKED_PATH}/*/*.xml")
    total = len(xmls)
    read = 0
    skipped = 0
    click.echo(f"{total} XML files to process.")

    output_format = {
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
        "article_contenu_markdown": "",
        "article_contenu_text": "",
    }

    # Initialize CSV
    csv_filename = os.path.join(COLD_CSV_PATH, "cold-french-law.csv")

    with open(csv_filename, "w+", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=output_format.keys())
        writer.writeheader()

    # Parse each XML file and collect relevant information.
    # Add to CSV on the fly.
    for xml in xmls:
        click.echo(f"Parsing file {read+1} of {total}.")

        doc = minidom.parse(xml)
        read += 1

        output = dict(output_format)

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
        output["texte_nature"] = "" + texte_ref.getAttribute("nature")
        output["texte_ministere"] = "" + texte_ref.getAttribute("ministere")
        output["texte_num"] = "" + texte_ref.getAttribute("num")
        output["texte_nor"] = "" + texte_ref.getAttribute("nor")
        output["texte_num_parution_jo"] = "" + texte_ref.getAttribute("num_parution_jo")
        output["texte_titre_court"] = "" + titre_txt_ref.getAttribute("c_titre_court")
        output["texte_titre"] = "" + titre_txt_ref.firstChild.wholeText

        # Pull "texte" context
        for ref in titre_tm_ref:
            section = ref.firstChild.wholeText
            if section:
                output["texte_contexte"] += section.strip() + "\n"

        # Pull textual contents for article:
        for contenu in doc.getElementsByTagName("CONTENU"):
            try:
                parsed_markdown = html2text.html2text(contenu.toxml())
                output["article_contenu_markdown"] += parsed_markdown

                parsed_text = "".join(
                    BeautifulSoup(contenu.toxml(), "html.parser").findAll(string=True)
                )
                output["article_contenu_text"] += parsed_text
            except Exception:
                pass

        output["article_contenu_markdown"] = output["article_contenu_markdown"].strip()
        output["article_contenu_text"] = output["article_contenu_text"].strip()

        # Write to CSV
        with open(csv_filename, "a", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=output.keys())
            writer.writerow(output)

    click.echo(f"{skipped} of {read} article files skipped.")
    click.echo(f"{read - skipped} articles written to CSV.")
    return True


def prepare() -> pd.DataFrame:
    """
    Downloads the translations file from HuggingFace repo
    Creates a dataframe with valid json files that start with LEGIARTI
    Dataframe columns are filtered with columns we are interested in, and appended with _en
    """
    translations_path = hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename="en_translations.tar.gz")
    processed_dfs = []
    malformed_json_count = 0
    processing = 0
    columns_to_keep = [
        "article_identifier",
        "texte_ministere",
        "texte_titre",
        "texte_titre_court",
        "texte_contexte",
        "article_contenu_markdown"
    ]

    with tarfile.open(translations_path) as tar:
        for member in tar.getmembers():
            file_name = member.name.split('/')[-1]

            if file_name.startswith('LEGIARTI'):
                file_content = tar.extractfile(member).read()
                processing += 1
                click.echo(f"Processing json file {processing}")
                try:
                    data_dict = json.loads(file_content)
                    filtered_dict = {k: data_dict[k] for k in columns_to_keep if k in data_dict}
                except TypeError:
                    malformed_json_count += 1
                    continue
                df = pd.DataFrame(filtered_dict, index=[0])

                # reindex df with selected columns, if col doesn't exist, it will be NaN in new df
                df = df.reindex(columns_to_keep, axis=1)
                processed_dfs.append(df)

        click.echo(f"Out of {processing} json files, {malformed_json_count} were marked as malformed.")

    # convert the NaN columns to empty string
    combined_df = pd.concat(processed_dfs, ignore_index=True).fillna('')

    # append _en to columns to distinguish Eng columns from the Fr columns in the resulting csv
    combined_df.columns = [str(df_col) + '_en' for df_col in combined_df.columns]
    return combined_df


def upload_csv_to_hf(file: str) -> None:
    """"
    Uploads the csv file to HuggingFace repo
    """
    api = HfApi()
    api.upload_file(
        path_or_fileobj=file,
        path_in_repo=MERGED_DATA_FILE,
        repo_id=REPO_ID,
        repo_type="dataset",
    )


def merge(upload_to_hf: bool = False) -> None:
    """"
    Dataframe is merged with the French csv dataframe on the article_identifier column
    A new csv file is created with the merged dataframe
    Resulting csv is uploaded to HF if --upload-to-hf flag is passed
    """
    prepared_data = prepare()

    # read the Fr csv into a dataframe and convert its NaN columns to empty string
    fr_df = pd.read_csv(f"{COLD_CSV_PATH}/cold-french-law.csv").fillna('')

    # merge and remove the article_identifier_en to avoid duplication of primary key
    merged_df = pd.merge(fr_df, prepared_data, how='left', left_on='article_identifier',
                         right_on='article_identifier_en').drop(
        'article_identifier_en', axis=1)

    merged_df.to_csv(f"{MERGED_DATA_PATH}/{MERGED_DATA_FILE}")
    click.echo(f"Merge is complete.")

    if upload_to_hf is True:
        upload_csv_to_hf(f"{MERGED_DATA_PATH}/{MERGED_DATA_FILE}")
        click.echo(f"Upload to HF is complete.")


if __name__ == "__main__":
    build()
