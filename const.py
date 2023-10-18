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

COLD_JSON_PATH = os.path.join(DATA_PATH, "cold_json")
""" Folder in which JSON files will be saved when exporting collection to JSON. """
