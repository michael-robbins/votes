import re
import random
import datetime

from . import app, db
from .models import VoterAction, VoteQuestion, Voter
from .forms import RankedField

from flask_wtf import Form
from wtforms.validators import DataRequired
from wtforms import TextAreaField, RadioField, SelectMultipleField, SubmitField


QUESTION_FREETEXT = "FreeText"
QUESTION_SINGLECHOICE = "SingleChoice"
QUESTION_MULTIPLECHOICE = "MultipleChoice"
QUESTION_RANKED = "Ranked"


def get_voter(email):
    """
    Returns the voter for the provided email
    :param email:
    :return (Voter, message):
    """
    if not email:
        # TODO: Flash "Not logged in"
        return None, "Not logged in"

    voter = Voter.query.filter_by(email=email).first()

    if not voter:
        # TODO: Flash "Bad Email"
        return None, "Bad email"

    return voter, "Success"


def build_form_for_questions(questions):
    """
    Builds a 'Form' object that contains the required fields for each question
    :param questions:
    :return DynamicForm:
    """

    class DynamicQuestionForm(Form):
        pass

    for question in questions:
        field_name = "q_{0}".format(question.id)
        if question.question_type == QUESTION_FREETEXT:
            field = TextAreaField(question.question, validators=[DataRequired()])
            setattr(DynamicQuestionForm, field_name, field)
        elif question.question_type == QUESTION_SINGLECHOICE:
            choices = [(str(choice.id), choice.choice) for choice in list(question.choices)]
            field = RadioField(question.question, choices=choices, validators=[DataRequired()])
            setattr(DynamicQuestionForm, field_name, field)
        elif question.question_type == QUESTION_MULTIPLECHOICE:
            choices = [(str(choice.id), choice.choice) for choice in list(question.choices)]
            field = SelectMultipleField(question.question, choices=choices, validators=[DataRequired()])
            setattr(DynamicQuestionForm, field_name, field)
        elif question.question_type == QUESTION_RANKED:
            choices = [(str(choice.id), choice.choice) for choice in list(question.choices)]
            field = RankedField(question.question, choices=choices, validators=[DataRequired()])
            setattr(DynamicQuestionForm, field_name, field)

    field = SubmitField(label="Submit")
    setattr(DynamicQuestionForm, "submit", field)

    field = SubmitField(label="Delete")
    setattr(DynamicQuestionForm, "delete", field)

    # Attach the validate function
    def validate(self):
        if not Form.validate(self):
            return False

        print(self.data)

        question_field_regex = re.compile("^q_([0-9]+)$")

        for form_field in self.data:
            regex_matched = question_field_regex.match(form_field)

            if regex_matched:
                question_id = regex_matched.group(1)
                question_obj = VoteQuestion.query.get(question_id)

                if not question:
                    getattr(self, form_field).errors.append("Question ID doesn't exist")
                    return False

                question_type = question_obj.question_type
                question_type_max = int(question_obj.question_type_max)

                if question_type == QUESTION_SINGLECHOICE:
                    # There's nothing to check here, they can only submit one (afaik)
                    pass
                elif question_type == QUESTION_MULTIPLECHOICE:
                    # Ensure they are only passing in <= question_type_max choices
                    if len(self.data[form_field]) > question_type_max:
                        message = "Please only choose up to {0} options"
                        getattr(self, form_field).errors.append(message.format(question_type_max))
                        return False
                elif question_type == QUESTION_FREETEXT:
                    # There's nothing to check here, it's a text box
                    pass
                elif question_type == QUESTION_RANKED:
                    print("Validating QUESTION_RANKED, field length is <= {0}".format(question_type_max))
                    print(self.data[form_field])
                    ranks_submitted = set()

                    for key, value in self.data[form_field].items():
                        if value == "":
                            # Nothing to validate on an empty field
                            continue

                        if int(value) > question_type_max:
                            message = "You've entered a rank above the maximum allowed ({0}) for this question"
                            getattr(self, form_field).errors.append(message.format(question_type_max))
                            return False

                        if len(ranks_submitted) > question_type_max:
                            message = "You've entered too many rankings, the maximum allowed is {0} for this question"
                            getattr(self, form_field).errors.append(message.format(question_type_max))
                            return False

                        ranks_submitted.add(value)

                    print(ranks_submitted)

                    if len(ranks_submitted) < question_type_max:
                        message = "You need to enter {0} rankings, you've only entered {1}!"
                        getattr(self, form_field).errors.append(message.format(question_type_max, len(ranks_submitted)))
                        return False

        return True

    setattr(DynamicQuestionForm, "validate", validate)

    return DynamicQuestionForm


def delete_actions(voter, question):
    """
    Takes the vote, voter and question, and deletes all actions taken on that (vote, question) by the user
    :param voter:
    :param question:
    :return None:
    """
    actions = VoterAction.query.filter_by(voter=voter, question=question).all()

    if len(actions):
        for action in actions:
            db.session.delete(action)

        db.session.commit()


def delete_vote(vote):
    """
    Takes the vote and deletes all questions, choices and actions associated to the vote
    :param vote: Vote
    :return:
    """
    for question in vote.questions:
        for choice in question.choices:
            for action in VoterAction.query.filter_by(vote=vote, question=question).all():
                db.session.delete(action)
            db.session.delete(choice)
        db.session.delete(question)

    db.session.delete(vote)
    db.session.commit()


def questions_and_answers_from_form(form, vote=None):
    """
    Takes a form (and optional vote) and returns a list of all questions in the form (that match the optional vote)
    :param form:
    :param vote:
    :return list(Questions):
    """
    question_field_regex = re.compile("^q_([0-9]+)$")

    for field, value in form.data.items():
        regex_matched = question_field_regex.match(field)

        if regex_matched:
            question_id = regex_matched.group(1)
            if vote:
                question = VoteQuestion.query.filter_by(id=question_id, vote=vote).first()
            else:
                question = VoteQuestion.query.get(question_id)

            if not question:
                print("Question ID ({0}) doesnt exist".format(question_id))
                getattr(form, field).errors.append("Question ID doesn't exist?")
                continue

            yield (question, value)


def is_vote_owner(vote, voter):
    """
    Returns True if the voter owns the vote (or has permissions to own the vote)
    :param vote: Vote
    :param voter: Voter
    :return: Boolean
    """
    if vote.owner == voter:
        return True

    if vote.owner.email in app.config["ADMIN_EMAILS"]:
        return True

    return False


def update_voter_passcode(voter):
    """
    Takes a voter and gives them a new passcode
    :param voter:
    :return:
    """
    voter.passcode = ''.join(random.SystemRandom().choice(app.config["PASSCODE_POOL"])
                             for _ in range(app.config["PASSCODE_LENGTH"]))
    voter.passcode_used = False
    voter.passcode_generated = datetime.datetime.now()
    db.session.add(voter)
    db.session.commit()


def send_voter_email(voter):
    """
    Takes a voter, and sends out a new passcode email
    :param voter:
    :return:
    """
    update_voter_passcode(voter)

    email_subject = app.config["PASSCODE_EMAIL_SUBJECT"]
    email_body = app.config["PASSCODE_EMAIL_BODY"].format(email=voter.email, passcode=voter.passcode,
                                                          generated=voter.passcode_generated,
                                                          company=app.config["COMPANY_NAME"])

    # TODO: Import email library and send email
