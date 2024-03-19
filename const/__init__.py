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

MERGED_DATA_PATH = os.path.join(DATA_PATH, "fr_eng")
""" Folder in which merged data will be written into. """

MERGED_DATA_FILE = "cold-french-law-with-eng.csv"
""" Name of the file the merged data will be written into. """

REPO_ID = "harvard-lil/cold-french-law"
""" HuggingFace repo the English translations will be pulled from, and the merged data file will be uploaded to. """
