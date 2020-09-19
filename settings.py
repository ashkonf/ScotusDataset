import os
import sys

DATA_DIR_PATH = os.path.join(os.path.dirname(__file__), "data")
TRANSCRIPTS_DIR_PATH = os.path.join(DATA_DIR_PATH, "transcripts")
SCDB_FILE_PATH = os.path.join(DATA_DIR_PATH, "SCDB_2019_01_caseCentered_Docket.csv")
DATABASE_FILE_PATH = os.path.join(DATA_DIR_PATH, "db.sqlite")
VERBOSE = os.environ.get("VERBOSE", True)
