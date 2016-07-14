import datetime

from wtforms import Field, StringField, HiddenField, SelectField, IntegerField, SubmitField, DateTimeField, FormField,\
    FieldList, BooleanField
from wtforms.widgets import Input, html_params, HTMLString
from wtforms.validators import DataRequired, Email
from wtforms.compat import text_type

from flask_wtf import Form  # This needs to go after the wtforms import (as that imports a 'Form' class itself)

from . import app, db
from .models import Voter


class SizedListWidget(object):
    """
    Basically the same as the 'ListWidget' but takes a 'subfield_size' and applies that to each subfield
    Currently wtforms ListWidget doesn't support this (afaik)
    """
    def __init__(self, html_tag="ul", prefix_label=True, subfield_size=20):
        assert html_tag in ("ol", "ul")
        self.html_tag = html_tag
        self.prefix_label = prefix_label
        self.subfield_size = subfield_size

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        html = ["<{0} {1}>".format(self.html_tag, html_params(**kwargs))]
        for subfield in field:
            if self.prefix_label:
                html.append("<li>{0} {1}</li>".format(subfield.label, subfield(size=self.subfield_size)))
            else:
                html.append("<li>{0} {1}</li>".format(subfield(size=self.subfield_size), subfield.label))
        html.append('</%s>' % self.html_tag)
        return HTMLString(''.join(html))


class RankedField(Field):
    """
    Class that will take an iterable of choices and render them all through the widget.
    Each choice will be rendered through the option_widget
    """
    widget = SizedListWidget(prefix_label=False, subfield_size=1)
    option_widget = Input(input_type="text")

    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        self.data = None
        super(RankedField, self).__init__(label, validators, **kwargs)

        self.coerce = int
        self.choices = choices

    def iter_choices(self):
        """
        Provides data for choice widget rendering. Must return a sequence or
        iterable of (value, label, date) tuples.
        """
        for value, label in self.choices:
            if not self.data:
                data = ""
            else:
                data = self.data.get(value, "")

            yield (value, label, data)

    def process_data(self, value):
        # What ever is passed in from the Field instantiation
        self.data = value

    def process_formdata(self, valuelist):
        self.data = {choice[0]: rank for (choice, rank) in zip(self.choices, valuelist)}

    def pre_validate(self, form):
        maximum_rank = len(self.choices)
        choice_ids = [int(choice[0]) for choice in self.choices]
        seen_ranks = set()

        for choice_id, rank in self.data.items():
            if rank == "":
                # Skip validation if the rank value field is left 'empty' as there's nothing to validate
                continue

            try:
                choice_id = int(choice_id)
            except ValueError:
                raise ValueError(self.gettext("Choice ID is not a valid number"))

            choice_name = None
            for choice in self.choices:
                if int(choice[0]) == choice_id:
                    choice_name = choice[1]

            if not choice_name:
                raise ValueError(self.gettext("Choice ID doesn't map to a sub-choice?"))

            try:
                rank = int(rank)
            except ValueError:
                raise ValueError(self.gettext("Ranking is not a valid number for option '{0}'".format(choice_name)))

            if choice_id not in choice_ids:
                raise ValueError(self.gettext("The ID for option '{0}' is invalid".format(choice_name)))

            if not 1 <= rank <= maximum_rank:
                raise ValueError(self.gettext("Only rankings between 1 and {0} are allowed for option '{1}'".format(
                    maximum_rank, choice_name)))

            if rank in seen_ranks:
                message = "Each ranking must be unique, you have more than one instance of the '{0}' rank"
                raise ValueError(self.gettext(message.format(rank)))
            else:
                seen_ranks.add(rank)

    def __iter__(self):
        opts = dict(widget=self.option_widget, _name=self.name, _form=None, _meta=self.meta)
        for i, (value, label, data) in enumerate(self.iter_choices()):
            opt = self._Option(label=label, id="{0}-{1}".format(self.id, i), **opts)
            opt.process(None, data)
            yield opt

    class _Option(Field):
        def _value(self):
            return text_type(self.data)


class EmailForm(Form):
    email = StringField("email", validators=[DataRequired(), Email()])

    def validate(self, extra_validators=None):
        if not Form.validate(self):
            return False

        email_regex = app.config["VALID_EMAIL_REGEX"]

        if not email_regex.match(self.email.data):
            self.email.errors.append("Invalid email address (Needs to be: {0})".format(email_regex.pattern))
            return False

        if not Voter.query.filter_by(email=self.email.data).first():
            new_voter = Voter(self.email.data)
            db.session.add(new_voter)
            db.session.commit()

        return True


class AuthForm(Form):
    email = StringField("email", validators=[DataRequired(), Email()])
    passcode = StringField("passcode", validators=[DataRequired()])

    def validate(self, extra_validators=None):
        if not Form.validate(self):
            return False

        voter = Voter.query.filter_by(email=self.email.data).first()

        if voter is None:
            self.email.errors.append("Unknown email address")
            return False

        # Check the user isn't recycling their passcode
        if voter.passcode_used:
            self.passcode.errors.append("Your passcode has already been used, please log in again from the start")
            return False

        # Check the user has 'just' got the email
        if voter.passcode_generated > datetime.datetime.now() + datetime.timedelta(minutes=5):
            self.passcode.errors.append("Your passcode has expired, please log in again")
            return False

        if voter.passcode != self.passcode.data:
            self.passcode.errors.append("Your passcode is incorrect")
            return False

        # Mark the passcode as used (since it's validated successfully)
        voter.passcode_used = True
        db.session.add(voter)
        db.session.commit()

        return True


class ChoiceForm(Form):
    id = HiddenField("ChoiceID")
    choice = StringField("Choice", validators=[DataRequired()])


class QuestionForm(Form):
    id = HiddenField("QuestionID")
    question = StringField("Question", validators=[DataRequired()])
    question_type = SelectField("Question Type", choices=[("SingleChoice", "Single Choice"),
                                                          ("MultipleChoice", "Multiple Choice"),
                                                          ("FreeText", "Free Text Field"),
                                                          ("Ranked", "Ranked Choices")],
                                validators=[DataRequired()])
    question_type_max = IntegerField("Maximum entries for a choice", default=1)
    # TODO: Enable support of min_entries=0 in the template/JS
    choices = FieldList(FormField(ChoiceForm), min_entries=1)


class VoteForm(Form):
    id = HiddenField("VoteID")
    title = StringField("Vote Title", validators=[DataRequired()])
    start_time = DateTimeField("Vote Opens")
    end_time = DateTimeField("Vote Closes")
    disabled = BooleanField(default=False)
    vote_type = SelectField("Vote Type", choices=[("TrackedBallot", "Tracked Ballot"),
                                                  ("AnonymousBallot", "Anonymous Ballot")], validators=[DataRequired()])
    questions = FieldList(FormField(QuestionForm), min_entries=1)
    submit = SubmitField(label="Save")
    delete = SubmitField(label="Delete")
