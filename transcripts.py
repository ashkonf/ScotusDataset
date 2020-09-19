import os
import re
import sys
from io import StringIO
import logging
import re

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

from settings import TRANSCRIPTS_DIR_PATH, VERBOSE
from models import Transcript, Statement, Case


## General utility functions #########################################################################################################################

def __list_dir(dirPath):
    std = []
    for name in os.listdir(dirPath):
        if not __file_hidden(name):
            std.append(os.path.join(dirPath, name))
    return std

def __file_hidden(path):
    return path.find(".") == 0

def __convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()

    return text


## Transcript preprocessing ##########################################################################################################################

def __process_red_flag(message, red_flags):
    red_flags.append(message)
    logging.info("RED FLAG: %s" % message)


BS_LINES = [
    "ALDERSON REPORTING COMPANY, INC.",
    "1111 FOURTEENTH STREET, N.W.",
    "SUITE 400",
    "WASHINGTON, D.C. 20005",
    "(202)289-2260",
    "(800) FOR DEPO",
    "Alderson Reporting Company",
    "Official"
]
LOOSE_BS_REGEX = "(?:%s)" % ("|".join("(?:%s)" % re.escape(line) for line in BS_LINES),)
STRICT_BS_REGEX = "^%s$" % (LOOSE_BS_REGEX,)

START_LINES = [
    "P R O C E E D I N G S",
    "P R O C E D I N G S",
    "P  R  O  C  E  E  D  I  N  G  S",
    "P  R  O  C  E  D  I  N  G  S",
]
START_LINE_REGEX = "(?:%s)" % ("|".join("(?:%s)" % line for line in START_LINES),)


def __extract_lines(text):
    # Extract and Clean Meaningful Lines:

    red_flags = []

    text = text.replace("\xc2\xa0\xc2\xad\xc2\xad", " -- ")
    text = text.replace("\xc2", " ").replace("\xa0", "").replace("\xad", "").replace("\x0c", "").replace("\xe2\x80\x99",
                                                                                                         "'").replace(
        "\\'", "'")
    lines = text.split("\n")

    reached_proceedings = False
    index = 0
    new_lines = []
    while index < len(lines):
        line = lines[index]
        if re.search(START_LINE_REGEX, line):
            reached_proceedings = True
            index += 2
        elif reached_proceedings:
            if len(line) > 0:
                if not re.match(STRICT_BS_REGEX, line.strip(), flags=re.IGNORECASE):
                    if not re.match("^ *\d+ *$", line):
                        if not re.match("\(\d?\d:\d\d (?:a|p)\.m\.\)", line.strip()):
                            new_lines.append(re.sub("^ *\d+    ", "", line))
        index += 1

    if not reached_proceedings:
        __process_red_flag("Didn't hit start phrase.", red_flags)

    in_petitioner_section = False
    petitioner_lines = []
    in_respondent_section = False
    respondent_lines = []
    hit_end_phrase = False
    # Lots of tolerance for observed types of misspellings:
    ARGUMENTS_END_REGEX_1 = " *[\(\[] ?Where?u?pon,?  ?at  ?\d\d?[\:\;]\d\d(?:  ?o'clock)?(?:  ?(?:(?:[ap]\.m\.?)|(?:noon)))? ?,?  ?the"
    ARGUMENTS_END_REGEX_2 = " *[\(\[] ?Where?u?pon,?  ?at  ?the  ?case  ?was  ?submitted"
    ARGUMENTS_END_REGEX_3 = " *[\(\[] ?Where?u?pon,?  ?the  ?case  ?in  ?the  ?above-(?:en)?titled"
    for line in new_lines:
        if re.search("ON  ?BEHALF  ?OF  ?(?:THE  ?)?(?:(?:PETITIONER)|(?:APPELANT))S?", line):
            in_petitioner_section = True
            in_respondent_section = False
        elif re.search("ON  ?BEHALF  ?OF  ?(?:THE  ?)?RES?PONDENTS?", line):  # we accomodate spelling errors
            in_respondent_section = True
            in_petitioner_section = False
        elif re.search(ARGUMENTS_END_REGEX_1, line) or re.search(ARGUMENTS_END_REGEX_2, line) or re.search(
                ARGUMENTS_END_REGEX_3, line):
            hit_end_phrase = True
            break
        elif not re.match("^[A-Z \.]+$", line):  # exclude lines declaring sections
            if in_petitioner_section:
                petitioner_lines.append(line)
            elif in_respondent_section:
                respondent_lines.append(line)

    if not hit_end_phrase:
        __process_red_flag("Didn't hit end phrase.", red_flags)

    return petitioner_lines, respondent_lines, red_flags


SPEAKER_REGEX = "^ *([A-Z\. ]+)\:"


def __starts_with_whitespace(string):
    # Checks to see if a string starts with whitespace:
    return string.lstrip() != string

    
def __append_trailing_space_if_necessary(line):
    # Appends whitespace to the end of a sentence fragment if appropriate:
    if line.endswith("-"):
        if len(line) > 1 and line[-2] == " ":
            line += " "
    else:
        line += " "
    return line


def __coalesce_paragraphs(lines):

    paragraphs = []
    current_paragraph = None
    for line in lines:
        if __starts_with_whitespace(line) or current_paragraph is None or re.match(SPEAKER_REGEX, line):
            if current_paragraph is not None:
                paragraphs.append(current_paragraph)
            current_paragraph = line.strip()
        else:
            current_paragraph = __append_trailing_space_if_necessary(current_paragraph)
            current_paragraph += line.strip()

    if current_paragraph is not None:
        paragraphs.append(current_paragraph)

    paragraphs = [re.sub(" +", " ", paragraph) for paragraph in
                  paragraphs]  # condense multiple consecutive spaces into a single space

    red_flags = []
    for paragraph in paragraphs:
        if re.match(LOOSE_BS_REGEX, paragraph, flags=re.IGNORECASE):
            __process_red_flag("BS line %s found in paragraph." % (paragraph,), red_flags)

    return paragraphs, red_flags


def __coalesce_statements(paragraphs):
    statements = []
    current_statement = None
    prev_paragraph = None
    for paragraph in paragraphs:
        speaker_match = re.match(SPEAKER_REGEX, paragraph)
        if speaker_match:
            # Wrap up the the statement and append it to the list:
            if current_statement is not None:
                # Infer attributes signaled by the end of the statement:
                if prev_paragraph is not None:
                    if prev_paragraph.strip().endswith(" --"):
                        current_statement.ended_by_interruption = True
                    elif prev_paragraph.strip().endswith("?"):
                        current_statement.ends_with_question = True
                statements.append(current_statement)

            # Create a new current statement:
            speaker = speaker_match.group(1)
            paragraph = re.sub(SPEAKER_REGEX, "", paragraph).strip()
            current_statement = Statement(speaker=speaker, ended_by_interruption=False, includes_laughter=False,
                                                 ends_with_question=False, speaker_is_petitioner=False,
                                                 speaker_is_respondent=False)
            current_statement.temp_paragraphs = []
            current_statement.temp_paragraphs.append(paragraph)

        elif current_statement is not None:
            if paragraph == "(Laughter.)":
                current_statement.includes_laughter = True
            else:
                current_statement.temp_paragraphs.append(paragraph)

        prev_paragraph = paragraph

    if current_statement is not None:
        statements.append(current_statement)

    return statements


def __extract_statements(file_path):
    raw_text = __convert_pdf_to_txt(file_path)
    if not raw_text: raw_text = ""
    petitioner_lines, respondent_lines, red_flags = __extract_lines(raw_text)

    if len(petitioner_lines) < 25:
        __process_red_flag("Only %s petitioner lines." % (len(petitioner_lines),), red_flags)

    if len(respondent_lines) < 25:
        __process_red_flag("Only %s respondent lines." % (len(respondent_lines),), red_flags)

    petitioner_paragraphs, new_red_flags = __coalesce_paragraphs(petitioner_lines)
    red_flags += new_red_flags
    petitioner_statements = __coalesce_statements(petitioner_paragraphs)

    respondent_paragraphs, new_red_flags = __coalesce_paragraphs(respondent_lines)
    red_flags += new_red_flags
    respondent_statements = __coalesce_statements(respondent_paragraphs)

    return petitioner_statements, respondent_statements, raw_text, red_flags


def __preprocess_transcript(file_path):
    dir_path, file_name = os.path.split(file_path)
    meta_dir_path, dir_name = os.path.split(dir_path)
    term = int(dir_name)

    docket = None
    FILE_PATH_REGEX = "(\d\d\-\d+)(?:_[^\.]+)?(?:\[Reargued\])?\.pdf"
    matches = re.findall(FILE_PATH_REGEX, file_name)
    if len(matches) == 0:
        logging.info("Regex didn't match file name: %s." % file_name)
    elif len(matches) == 1:
        docket = matches[0]
    else:
        docket = matches[0]
        logging.info("Regex matched file name more than once: %s." % file_name)

    petitioner_statements, respondent_statements, raw_text, red_flags = __extract_statements(file_path)
    transcript = Transcript(raw_text=raw_text, term=term, docket=docket, file_name=file_name)
    transcript = transcript.get_or_create()

    for statement in petitioner_statements:
        paragraphs = statement.temp_paragraphs[:]
        statement.transcript = transcript
        statement.speaker_is_petitioner = True
        statement = statement.get_or_create()
        for paragraph in paragraphs:
            statement.add_paragraph(paragraph)

    for statement in respondent_statements:
        paragraphs = statement.temp_paragraphs[:]
        statement.transcript = transcript
        statement.speaker_is_respondent = True
        statement = statement.get_or_create()
        for paragraph in paragraphs:
            statement.add_paragraph(paragraph)

    for gloss in red_flags:
        transcript.add_red_flag(gloss)

    return transcript


def preprocess_all_transcripts():
    for dir_path in __list_dir(TRANSCRIPTS_DIR_PATH):
        term = dir_path[-4:]

        if VERBOSE: logging.info("Preprocessing term %s ..." % term)
        transcript_count = 0

        for file_path in __list_dir(dir_path):
            file_name = os.path.basename(file_path)
            if Transcript.get_or_none(Transcript.file_name == file_name) is None:
                if VERBOSE: logging.info("Preprocessing document %s/%s ..." % (term, file_name))
                transcript = __preprocess_transcript(file_path)

                if VERBOSE: logging.info(
                    "Done preprocessing document %s/%s. Parsed %s petitioner statements and %s repondent statements." % (
                    term, file_name, len(transcript.petitioner_statements()), len(transcript.respondent_statements())))

            transcript_count += 1

        if VERBOSE: logging.info("Done preprocessing term %s. Parsed %s transcripts." % (term, transcript_count))
