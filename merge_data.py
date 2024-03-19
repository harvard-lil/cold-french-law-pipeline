import json
import pandas as pd
import tarfile
from huggingface_hub import hf_hub_download
from huggingface_hub import HfApi
import click
from const import COLD_CSV_PATH, MERGED_DATA_PATH, REPO_ID, MERGED_DATA_FILE


@click.command()
@click.option(
    "--upload-to-hf",
    is_flag=True,
    required=False,
    default=False,
    help="If set, uploads the merged data csv to HuggingFace.",
)
def merge(upload_to_hf: bool = False) -> None:
    """"
    Dataframe is merged with the French csv dataframe on the article_identifier column
    A new csv file is created with the merged dataframe
    Resulting csv is uploaded to HF if --upload-to-hf flag is passed
    """
    click.echo("Starting to prepare data.")
    prepared_data = prepare()

    # read the Fr csv into a dataframe and convert its NaN columns to empty string
    fr_df = pd.read_csv(f"{COLD_CSV_PATH}/cold-french-law.csv").fillna('')

    # merge and remove the article_identifier_en to avoid duplication of primary key
    click.echo("Starting to merge data.")
    merged_df = pd.merge(fr_df, prepared_data, left_on='article_identifier', right_on='article_identifier_en').drop(
        'article_identifier_en', axis=1)

    merged_df.to_csv(f"{MERGED_DATA_PATH}/{MERGED_DATA_FILE}")
    click.echo(f"Merge is complete.")

    if upload_to_hf is True:
        upload_csv_to_hf(f"{MERGED_DATA_PATH}/{MERGED_DATA_FILE}")
        click.echo(f"Upload to HF is complete.")


def prepare() -> pd.DataFrame:
    """
    Downloads the translations file from HuggingFace repo
    Creates a dataframe with valid json files that start with LEGIARTI
    Dataframe columns are filtered with columns we are interested in, and appended with _en
    """
    translations_path = hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename="translations.tar.gz")
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
                click.echo(f"Processing file {processing}")
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

        click.echo(f"Out of {processing} files, {malformed_json_count} were marked as malformed.")

    # convert the NaN columns to empty string
    combined_df = pd.concat(processed_dfs, ignore_index=True).fillna('')

    # append _en to columns to distinguish Eng columns from the Fr columns in the resulting csv
    combined_df.columns = [str(df_col) + '_en' for df_col in combined_df.columns]
    return combined_df


def upload_csv_to_hf(file):
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


if __name__ == "__main__":
    merge()
