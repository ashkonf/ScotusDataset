import os
import re
import sys
import logging

from settings import VERBOSE
from models import Transcript, Statement, Case
from transcripts import preprocess_all_transcripts
from scdb import load_cases


def preprocess_docket(docket):
    return re.sub(",? (?:ORIG|ORIG\.|Orig\.|Original|\(Original\)|M|orig\.|ORIG ORIG)$", "",
                  re.sub("^A-", "", docket.strip()))


def reconciliate_cases_and_transcripts():
    case_dockets = {}
    transcript_dockets = {}
    for case in Case.select():
        try:
            case_dockets[preprocess_docket(case.docket)] = case
        except:
            continue

    for transcript in Transcript.select():
        try:
            transcript_dockets[preprocess_docket(transcript.docket)] = transcript
        except:
            continue

    for docket in case_dockets:
        if docket in transcript_dockets:
            case = case_dockets[docket]
            case.transcript = transcript_dockets[docket]
            case.save()


def print_coverage_stats():
    total_count = Case.select().count()
    has_transcript_count = Case.select().where(Case.transcript.is_null(False)).count()
    coverage = float(has_transcript_count) / float(total_count)
    logging.info("There are %s cases and %s cases with transcripts, for a coverage of %s%s." % (
        total_count, has_transcript_count, round(coverage * 100.0, 2), "%"))
    total_count = Transcript.select().count()
    has_case_count = len([transcript for transcript in Transcript.select() if transcript.cases.count() > 0])
    coverage = float(has_case_count) / float(total_count)
    logging.info("There are %s transcripts and %s transcripts with cases, for a coverage of %s%s." % (
        total_count, has_case_count, round(coverage * 100.0, 2), "%"))



def compile_data():
    if VERBOSE: logging.info("Preprocessing transcripts ...")
    preprocess_all_transcripts()
    if VERBOSE: logging.info("Done processing transcripts.")

    if VERBOSE: logging.info("Loading SCDB cases from CSV ...")
    load_cases()
    if VERBOSE: logging.info("Done loading SCDB cases.")

    if VERBOSE: logging.info("Reconciliating cases and transcripts ...")
    reconciliate_cases_and_transcripts()
    if VERBOSE: logging.info("Done reconciliating cases and transcripts.")


if __name__ == "__main__":
    preprocess_all_transcripts()
