import os

LEGI_BASE_URL = "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"
""" Base URL for the LEGI dataset. """

DATA_PATH = os.path.join(os.getcwd(), "data")
""" Path to the data folder. """

LEGI_TAR_PATH = os.path.join(DATA_PATH, "legi_tar")
""" Path in which original .tar.gz files from the LEGI dataset will be written. """

LEGI_UNPACKED_PATH = os.path.join(DATA_PATH, "legi_unpacked")
""" Path in which the original LEGI .tar.gz files will be unpacked. """

COLD_CSV_PATH = os.path.join(DATA_PATH, "cold_csv")
""" Path in which the filtered CSV file will be written. """
