import os
import re
import sys
import pandas as pd
from io import StringIO
import logging

from settings import TRANSCRIPTS_DIR_PATH, SCDB_FILE_PATH, VERBOSE


def __build_case(row):
    case_obj = Case()
    case_obj.decision_label = row.decisionType
    case_obj.vote_id = row.voteId
    case_obj.term = row.term
    case_obj.docket = row.docket
    case_obj.justice_name = row.chief
    date = row.dateDecision.split('/')
    case_obj.day = date[1]
    case_obj.month = date[0]

    return case_obj


def load_cases():
    case_df = pd.read_csv(SCDB_FILE_PATH, engine='python')
    for index, row in case_df.iterrows():
        if VERBOSE: logging.info("processing case %d ..." % index)

        if Case.get_or_none(Case.vote_id == row.voteId) is None:
            case = __build_case(row)
            transcript = None
            case.transcript = transcript
            case = case.get_or_create()

            if VERBOSE: logging.info("Loading case , Vote ID %s ..." % (case.vote_id))
