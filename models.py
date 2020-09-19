import os
from peewee import SqliteDatabase, Model, ForeignKeyField, BooleanField, CharField, TextField, IntegerField, DateTimeField

from settings import DATABASE_FILE_PATH

## Constants ##################################################################################################################################

DATABASE = SqliteDatabase(DATABASE_FILE_PATH)


## Utility functions ##########################################################################################################################

def aggressively_sanitize_string(string):
    return "".join([char if ord(char) < 128 else "" for char in string])


## Models #####################################################################################################################################

class Transcript(Model):
    raw_text = TextField()
    term = IntegerField()
    docket = CharField(null=True)
    file_name = CharField()

    class Meta:
        database = DATABASE

        indexes = (
            (("term", "docket", "file_name"), True),
        )

    def equivalent(self):
        return self.__class__.select().where(
            (self.__class__.term == self.term)
            & (self.__class__.docket == self.docket)
            & (self.__class__.file_name == self.file_name)
        )

    def is_well_formed(self):
        return not self.has_red_flags()

    def petitioner_statements(self):
        return [statement for statement in self.statements if statement.speaker_is_petitioner]

    def respondent_statements(self):
        return [statement for statement in self.statements if statement.speaker_is_respondent]

    def add_red_flag(self, gloss):
        red_flag = RedFlag(transcript=self, gloss=gloss)
        return red_flag.get_or_create()

    def has_red_flags(self):
        return RedFlag.select().where(RedFlag.transcript == self).count() > 0

    def red_flags(self):
        return [red_flag.gloss for red_flag in self.red_flags_]

    def full_text(self):
        statements = [statement.full_text() for statement in self.petitioner_statements]
        statements += [statement.full_text() for statement in self.respondent_statements]
        return "\n\n".join(statements)

    def exists(self):
        return self.equivalent().count() > 0

    def get_or_create(self):
        if self.exists():
            return self.equivalent().get()
        else:
            self.save()
            return self


class Case(Model):
    decision_label = IntegerField()
    vote_id = CharField()
    term = IntegerField()
    month = DateTimeField(null=True)
    day = DateTimeField(null=True)
    docket = CharField()
    justice_name = CharField()
    transcript = ForeignKeyField(Transcript, backref="cases", null=True)

    class Meta:
        database = DATABASE

        indexes = (
            (("decision_label", "vote_id", "term", "month",
              "day", "docket", "justice_name"), True),
        )

    def equivalent(self):
        return self.__class__.select().where(
            (self.__class__.vote_id == self.vote_id)
            & (self.__class__.term == self.term)
            & (self.__class__.month == self.month)
            & (self.__class__.day == self.day)
            & (self.__class__.docket == self.docket)
        )

    def is_well_formed(self):
        return (self.vote_id is not None) and (self.justice_id >= 0) and (self.day is not None)

    @classmethod
    def select_well_formed(cls, term=None, before_term=None, month=None, before_month=None, week=None, before_week=None,
                           day=None, before_day=None):
        params = [term, before_term, month, before_month, week, before_week, day, before_day]
        assert (sum((param is not None) for param in params) <= 1)

        well_formed_query = (cls.vote_id.is_null(False) & cls.justice_id.is_null(False) & cls.day.is_null(False))

        if term:
            query = (well_formed_query & (cls.term == term))
        elif before_term:
            query = (well_formed_query & (cls.term < before_term))
        elif month:
            query = (well_formed_query & (cls.month == month.date()))
        elif before_month:
            query = (well_formed_query & (cls.month < before_month.date()))
        elif week:
            query = (well_formed_query & (cls.week == week.date()))
        elif before_week:
            query = (well_formed_query & (cls.week < before_week.date()))
        elif day:
            query = (well_formed_query & (cls.day == day.date()))
        elif before_day:
            query = (well_formed_query & (cls.day < before_day.date()))
        else:
            query = well_formed_query

        return cls.select().where(query).order_by(cls.day)

    def has_transcript(self):
        return self.transcript is not None

    @classmethod
    def min_term(cls):
        return min(set(case.term for case in cls.select_well_formed()))

    @classmethod
    def max_term(cls):
        return max(set(case.term for case in cls.select_well_formed()))

    @classmethod
    def min_month(cls):
        return min(set(case.month for case in cls.select_well_formed()))

    @classmethod
    def max_month(cls):
        return max(set(case.month for case in cls.select_well_formed()))

    @classmethod
    def min_week(cls):
        return min(set(case.week for case in cls.select_well_formed()))

    @classmethod
    def max_week(cls):
        return max(set(case.week for case in cls.select_well_formed()))

    @classmethod
    def min_day(cls):
        return min(set(case.day for case in cls.select_well_formed()))

    @classmethod
    def max_day(cls):
        return max(set(case.day for case in cls.select_well_formed()))

    def exists(self):
        return self.equivalent().count() > 0

    def get_or_create(self):
        if self.exists():
            return self.equivalent().get()
        else:
            self.save()
            return self

class RedFlag(Model):
    transcript = ForeignKeyField(Transcript, backref="red_flags_")
    gloss = CharField()

    class Meta:
        database = DATABASE

    def equivalent(self):
        return self.__class__.select().where(
            (self.__class__.transcript == self.transcript)
            & (self.__class__.gloss == self.gloss)
        )

    def is_well_formed(self):
        return True

    def exists(self):
        return self.equivalent().count() > 0

    def get_or_create(self):
        if self.exists():
            return self.equivalent().get()
        else:
            self.save()
            return self


class Statement(Model):
    transcript = ForeignKeyField(Transcript, backref="statements")
    speaker = CharField()
    ended_by_interruption = BooleanField(default=False)
    includes_laughter = BooleanField(default=False)
    ends_with_question = BooleanField(default=False)
    speaker_is_petitioner = BooleanField(default=False)
    speaker_is_respondent = BooleanField(default=False)

    class Meta:
        database = DATABASE

    def equivalent(self):
        return self.__class__.select().where(
            (self.__class__.transcript == self.transcript)
            & (self.__class__.speaker == self.speaker)
            & (self.__class__.ended_by_interruption == self.ended_by_interruption)
            & (self.__class__.includes_laughter == self.includes_laughter)
            & (self.__class__.speaker_is_petitioner == self.speaker_is_petitioner)
            & (self.__class__.speaker_is_respondent == self.speaker_is_respondent)
        )

    def is_well_formed(self):
        return True

    def exists(self):
        return self.equivalent().count() > 0

    def get_or_create(self):
        if self.exists():
            return self.equivalent().get()
        else:
            self.save()
            return self

    def add_paragraph(self, paragraph):
        paragraph = aggressively_sanitize_string(paragraph).strip()
        paragraph = Paragraph(statement=self, gloss=paragraph)
        return paragraph.get_or_create()

    def paragraphs(self):
        return [paragraph.gloss for paragraph in self.paragraphs_]

    def speaker_is_justice(self):
        return self.speaker.startswith("JUSTICE") or self.speaker.startswith("CHIEF JUSTICE") or (
                    self.speaker == "QUESTION")

    def full_text(self):
        return "\n\n".join(self.paragraphs())


class Paragraph(Model):
    statement = ForeignKeyField(Statement, backref="paragraphs_")
    gloss = TextField()

    class Meta:
        database = DATABASE

        indexes = (
            (("statement", "gloss"), True),
        )

    def equivalent(self):
        return self.__class__.select().where(
            (self.__class__.statement == self.statement)
            & (self.__class__.gloss == self.gloss)
        )

    def is_well_formed(self):
        return True

    def exists(self):
        return self.equivalent().count() > 0

    def get_or_create(self):
        if self.exists():
            return self.equivalent().get()
        else:
            self.save()
            return self


DATABASE.create_tables([
    Case,
    Transcript,
    RedFlag,
    Statement,
    Paragraph,
])