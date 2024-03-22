import os

LEGI_BASE_URL = "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"
""" Base URL for the LEGI dataset. """

DATA_PATH = os.path.join(os.getcwd(), "data")
""" Path to the data folder. """

LEGI_TAR_PATH = os.path.join(DATA_PATH, "legi_tar")
""" Folder in which .tar.gz files from the LEGI dataset will be downloaded. """

LEGI_UNPACKED_PATH = os.path.join(DATA_PATH, "legi_unpacked")
""" Folder in which pre-filtered XML files from the LEGI .tar.gz files will be unpacked. """

COLD_CSV_PATH = os.path.join(DATA_PATH, "cold_csv")
""" Folder in which the processed collection will be written into a CSV file. """

COLD_CSV_FILE = os.path.join(COLD_CSV_PATH, "cold-french-law.csv")
""" Folder in which the processed collection will be written into a CSV file. """

HF_REPO_ID = "harvard-lil/cold-french-law"
""" HuggingFace repo the English translations will be pulled from, and the merged data file will be uploaded to. """

HF_EN_TRANSLATIONS_FILE = "en_translations.tar.gz"
""" Name of the EN translations file on HuggingFace. """
