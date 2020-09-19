# Python SCOTUS Dataset

## Contents

- [Overview](#Overview)
- [Background](#Background)
- [Dependencies](#Dependencies)
- [Usage](#Usage)
- [Example](#Example)
- [License](#License)
- [Links](#Links)


## Overview

The Python SCOTUS Dataset is a repository for retrieving, processing, and maintaining structured data from the Supreme Court of the United States (SCOTUS). The Python functions in the repo can combine trial transcripts from the [SCOTUS website](https://www.supremecourt.gov/oral_arguments/argument_transcript/) with structured case data from the [Supreme Court Database](http://scdb.wustl.edu/) (SCDB) at the Washington University Law School to create comprehensive summaries of the most recent SCOTUS cases. The repo is primarily used for building systems that predict SCOTUS case decisions.

## Background

### SCOTUS decision prediction

Just as DeepMind’s AlphaZero chess AI has improved the game of human experts, so can highly performant algorithms provide insights that help predict SCOTUS behavior. Industry, academia, and the legal profession have long been interested in using such algorithms to improve domain outcomes.

For instance, lawyers can adjust variables and analyze features to determine which issues should be highlighted to win an argument. Models can show whether a single justice (or a constellation of justices) has a strong or atypical voting tendency on important issues such as taxes and civil rights. Would-be SCOTUS appellants can use algorithms to help determine whether a case appeal is practical based on the likelihood of a win. Investors, too, may find SCOTUS prediction useful by betting on companies that are likely to benefit most from a favorable ruling.

SCOTUS typically decides 70 to 90 cases annually, historically reversing approximately two thirds of those cases. While this reversal rate may seem high, it understandably stems from the court’s selection bias in favor of cases the court regards as meriting review. Furthermore, unanimous decisions occur about half the time — far more often than might be suggested by the ideological biases of the justices that critics point out.

Important cognitive biases must therefore be identified to better understand the nuances at play in SCOTUS decision making. Often, achieving optimal performance in machine learning applications requires a high degree of domain knowledge and custom feature engineering. Such complexities challenge both machine and human performance and make the problem of accurate SCOTUS prediction an open research question. Python Scotus Dataset serves as a starting point for addressing that question.

### Structured data from the SCDB

The SCDB, developed by Harold Spaeth, is a widely used database for SCOTUS outcome prediction. The SCDB contains 247 variables for each case. The variables are divided into six categories, given below with examples of SCDB variables in parentheses:

1.	Identification (LEXIS Citation, Docket Number)
2.	Background (Origin of Case, Source of Case, Reason for Granting Cert)
3.	Chronological (Date of Decision, Term of Court, Natural Court)
4.	Substantive (Legal Provisions Considered by the Court, Issue, Decision Direction)
5.	Outcome (Disposition of Case, Winning Party, Formal Alteration of Precedent, Declaration of Unconstitutionality)
6.	Voting & Opinion (Direction of the Individual Justice's Votes, Opinion, Majority and Minority Voting by Justice)

Python SCOTUS Dataset includes a local copy of the SCDB case data for analysis.


### Unstructured SCOTUS transcripts

On its [official website](https://www.supremecourt.gov/oral_arguments/argument_transcript/), SCOTUS publishes full transcripts of oral arguments the day the arguments are heard. As a significant amount of time typically elapses between oral arguments and a SCOTUS ruling, the transcripts provide context for outcome prediction. The transcripts contain exchanges between all relevant parties (including attorneys and justices), are generally around 60 pages, and require significant preprocessing — for example, PDF-to-text conversion and manual featurization. Engineers who find that language use yields clues to the justices’ leanings will want to capture associated features from the transcript corpus.

How a justice questions lawyers can signal what that justice is thinking; swing-vote justices are often a focal point, especially since those justices tend to receive more attention from lawyers. The very act of questioning can also have important implications. [FiveThirtyEight](https://fivethirtyeight.com/features/how-to-read-the-mind-of-a-supreme-court-justice/) author Oliver Roeder observes as follows:

>When a justice asks questions of a lawyer, it’s bad for his chances — it means the justice is skeptical and is trying to poke holes. If justices interrupt a lawyer, it’s really bad for his chances — they’re so skeptical they just can’t wait to poke holes. A Ginsburg interruption is worst of all.

Research further supports a correlation between lawyers’ language use and case outcomes; perceived attributes such as confidence, intelligence, trustworthiness, and aggressiveness that are conveyed through a lawyer’s statements can affect the likelihood that justices will side with the lawyer. Python Scotus Dataset provides a starting point for predicting language use in relation to case outcomes.

## Dependencies

Python SCOTUS Dataset requires the following libraries:

- [`pdfminer`](https://pypi.org/project/pdfminer/)
- [`peewee`](http://docs.peewee-orm.com/en/latest/)
- [`pandas`](https://pandas.pydata.org/)
- [`numpy`](https://numpy.org/)

Install these libraries using `pip` and requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

The Python SCOTUS Dataset `recon` module exports two public functions for compiling data reconciliation.

### compile_data()

The `compile_data()` function does the following:
1. It iterates over the transcript PDFs in the data directory, parses them, and saves the extracted transcript data in the database.
2. It loads and parses the SCDB data saved as a CSV in the data directory, and saves the extracted case data in the database.
3. Maps the transcripts to their associated cases.

Upon completion, the database will contain a full set of case objects with associated SCDB data and transcripts.

### print_coverage_stats()

The `print_coverage_stats()` function prints statistics describing the data compiled in the database.

## Example

The code below compiles all case data and then prints statistics describing the data in the database:

```bash
from recon import compile_data, print_coverage_stats

compile_data()
print_coverage_stats()
```

This example provides the basic code needed to integrate Python SCOTUS Dataset with language-use analysis and case-outcome prediction.

## License

Python SCOTUS Dataset is licensed under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).


## Links

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [FiveThirtyEight](https://fivethirtyeight.com/features/how-to-read-the-mind-of-a-supreme-court-justice/)
- [NumPy](https://numpy.org/)
- [pandas](https://pandas.pydata.org/)
- [PDFMiner](https://pypi.org/project/pdfminer/)
- [peewee](http://docs.peewee-orm.com/en/latest/)
- [SCOTUS transcripts website](https://www.supremecourt.gov/oral_arguments/argument_transcript/)
- [Supreme Court Database](http://scdb.wustl.edu/)
