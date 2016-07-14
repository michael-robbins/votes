import json

from flask import render_template, redirect, request, session

from .forms import *
from .models import *
from .vote_helper import *


@app.route("/")
@app.route("/index")
@app.route("/votes")
@app.route("/votes/")
def index():
    voter_email = session.get("email")
    voter, message = get_voter(voter_email)

    if not voter:
        # TODO: Flash 'message'
        return redirect(LOGIN_THX)

    visible_votes = list()
    owned_votes = list()

    now = datetime.datetime.now()
    for vote in Vote.query.filter(Vote.start_time < now, Vote.end_time > now).all():
        vote.participated_in = user_has_participated(voter, vote)

        template = "{days}d, {hours}h and {minutes}m until closed!"
        vote.closes_in = string_format_delta((vote.end_time - now), template)

        visible_votes.append(vote)

        if is_vote_owner(vote, voter):
            owned_votes.append(vote)

    context = {
        "name": voter_email,
        "voter": voter,
        "company": app.config["COMPANY_NAME"],
        "visible_votes": visible_votes,
        "owned_votes": owned_votes,
    }

    return render_template("index.html", **context)


@app.route("/logout")
def logout():
    session["email"] = ""
    return redirect(LOGIN_THOUGHTS)


@app.route("/login", methods=["GET", "POST"])
def login():
    email = request.args.get("email")

    if email is None:
        # Present the form asking for the users email
        login_form = EmailForm()

        if login_form.validate_on_submit():
            voter = Voter.query.filter_by(email=login_form.email.data).first()
            send_voter_email(voter)
            return redirect(LOGIN_EMAIL.format(voter.email))

        template = "email.html"
        title = "Enter your email"
    else:
        # TODO: Hack, remove this later, saves having to log in each time, as each reload deletes the old login cookie!
        if email in app.config["ADMIN_EMAILS"]:
            session["email"] = email
            return redirect(INDEX_LOGIN)

        # Present the form asking for the users passcode
        login_form = AuthForm()

        if login_form.validate_on_submit():
            session["email"] = email
            return redirect(INDEX_LOGIN)

        template = "auth.html"
        title = "Enter your passcode"
        login_form.email.data = email

    context = {
        "company": app.config["COMPANY_NAME"],
        "title": title,
        "form": login_form
    }

    return render_template(template, **context)


@app.route("/votes/new", methods=["GET", "POST"])
def vote_new():
    voter_email = session.get("email")
    voter, message = get_voter(voter_email)

    if not voter:
        # TODO: Flash 'message'
        return redirect(LOGIN_THX)

    new_vote_form = VoteForm()
    # Remove the delete button, as nothing exists yet!
    delattr(new_vote_form, "delete")

    if new_vote_form.validate_on_submit():
        vote = Vote(
            title=new_vote_form.data.get("title"),
            owner=voter,
            vote_type=new_vote_form.data.get("vote_type"),
            start_time=new_vote_form.data.get("start_time"),
            end_time=new_vote_form.data.get("end_time")
        )

        db.session.add(vote)

        for question in new_vote_form.questions:
            vote_question = VoteQuestion(
                vote=vote,
                question_type=question.question_type.data,
                question_type_max=question.question_type_max.data,
                question=question.question.data
            )

            db.session.add(vote_question)

            for choice in question.choices:
                vote_choice = VoteChoice(question=vote_question, choice=choice.choice.data)
                db.session.add(vote_choice)

        db.session.commit()
        return redirect(INDEX_SUBMITTED)

    context = {
        "company": app.config["COMPANY_NAME"],
        "form": new_vote_form,
        "header": "New Vote",
        "post_url": "/votes/new",
    }

    return render_template("vote_crud.html", **context)


@app.route("/votes/edit/<int:vote_id>", methods=["GET", "POST"])
def vote_edit(vote_id):
    voter_email = session.get("email")
    voter, message = get_voter(voter_email)

    if not voter:
        # TODO: Flash 'message'
        return redirect(LOGIN_THX)

    vote = Vote.query.filter_by(id=vote_id).first()

    if not vote:
        # TODO: Flash "Vote doesn't exist"
        return redirect(INDEX_EXISTENCE)

    if not is_vote_owner(vote, voter):
        # TODO: Flash "You are not the owner of vote: VOTE_TITLE"
        return redirect(INDEX_CHEATER)

    vote_form = VoteForm()

    if vote_form.is_submitted() and vote_form.data.get("delete"):
        vote_id = vote_form.data.get("id")

        if vote_id:
            vote = Vote.query.get(vote_id)

            if vote:
                if not is_vote_owner(vote, voter):
                    return redirect(INDEX_CHEATER)

                delete_vote(vote)

                # TODO: Flash 'Vote' deleted
                return redirect(INDEX_RMRF)
            else:
                return redirect(INDEX_BAD_VOTE_ID)
        else:
            return redirect(INDEX_EXISTENCE)

    if vote_form.validate_on_submit():
        if vote_form.id.data:
            vote = Vote.query.get(vote_form.id.data)

            if vote:
                # Double check the user isn't cheating by changing the Vote ID on us in the form's hidden field
                if not is_vote_owner(vote, voter):
                    return redirect(INDEX_CHEATER)

                # Update all the attributes, if the user changed the Vote ID to something else they own, bad luck!
                vote.title = vote_form.title.data
                vote.start_time = vote_form.start_time.data
                vote.end_time = vote_form.end_time.data
                vote.vote_type = vote_form.vote_type.data
                vote.disabled = vote_form.vote_type.data
            else:
                return redirect(INDEX_BAD_VOTE_ID)
        else:
            # TODO: Figure out why we would allow this logic to occur?
            vote = Vote(
                title=vote_form.title.data,
                owner=voter,
                vote_type=vote_form.vote_type.data,
                start_time=vote_form.start_time.data,
                end_time=vote_form.end_time.data
            )

        db.session.add(vote)

        existing_questions = {question.id: question for question in VoteQuestion.query.filter_by(vote=vote).all()}

        for question in vote_form.questions:
            question_id = question.data.get("id")

            if question_id:
                vote_question = VoteQuestion.query.get(question_id)

                if vote_question:
                    if vote_question.vote != vote:
                        # User's submitting a vote question that doesn't belong to this vote?
                        # TODO: Flash "User submitted a vote question not belonging to the vote?"
                        return redirect(INDEX_CHEATER)

                    vote_question.question_type = question.question_type.data
                    vote_question.question_type_max = question.question_type_max.data
                    vote_question.question = question.question.data
                else:
                    # User submitted a question that doesn't exist
                    return redirect(INDEX_BAD_QUESTION_ID)
            else:
                vote_question = VoteQuestion(
                    vote=vote,
                    question_type=question.question_type.data,
                    question_type_max=question.question_type_max.data,
                    question=question.question.data
                )

            existing_questions.pop(vote_question.id)
            db.session.add(vote_question)

            for choice in question.choices:
                choice_id = choice.data.get("id")

                if choice_id:
                    vote_choice = VoteChoice.query.get(choice_id)

                    if vote_choice:
                        if vote_choice.question != vote_question:
                            # Users submitting a choice to a different question
                            # TODO: Flash "User submitted for a choice to a different question"
                            return redirect(INDEX_CHEATER)

                        vote_choice.choice = choice.choice.data
                    else:
                        # User submitted for a choice that doesn't exist?
                        return redirect(INDEX_BAD_CHOICE_ID)
                else:
                    vote_choice = VoteChoice(question=vote_question, choice=choice.choice.data)

                db.session.add(vote_choice)

        # All questions left in 'existing questions' have been deleted
        for question in existing_questions.values():
            db.session.delete(question)

        db.session.commit()
        return redirect(INDEX_SUBMITTED)
    else:
        # If it's not valid and it hasn't been submitted, then overwrite it with the model requested in the GET
        if not vote_form.is_submitted():
            vote_form = VoteForm(obj=vote)
            vote_form.submit.label.text = "Update"
        else:
            # If it has been submitted, then pass it through with all the errors
            pass

    context = {
        "company": app.config["COMPANY_NAME"],
        "form": vote_form,
        "header": "Edit Vote",
        "post_url": "/votes/edit/{0}".format(vote.id),
    }

    return render_template("vote_crud.html", **context)


@app.route("/votes/cast/<int:vote_id>", methods=["GET", "POST"])
def vote_cast_crud(vote_id):
    voter_email = session.get("email")
    voter, message = get_voter(voter_email)

    # Ensure both the voter and the vote exist, bail if they're missing
    if not voter:
        # TODO: Flash "You're not logged in"
        return redirect(LOGIN_THX)

    vote = Vote.query.filter_by(id=vote_id).first()

    if not vote:
        # TODO: Flash "Vote doesn't exist"
        return redirect(INDEX_EXISTENCE)

    if not vote_is_live(vote):
        # They should only have gotten here by messing with the URL!
        return redirect(INDEX_CHEATER)

    # Do not let the user vote again if we're in anonymous mode and they've participated already
    if vote.vote_type == VOTE_ANONYMOUS and user_has_participated(voter, vote):
        # TODO: Flash "You've already participated in this vote!"
        return redirect(INDEX_ALREADY_VOTED)

    # If the user is here, that means they are in TrackedBallot mode, or have not voted already for this vote
    # Force the resolution of the questions
    questions = list(vote.questions)

    # Build the dynamic form class based of the questions/choices for this vote
    form_class = build_form_for_questions(questions)
    vote_form = form_class()

    # Handle the user attempting to delete their already cast vote
    if vote_form.is_submitted() and vote_form.data.get("delete"):
        for question, answer in questions_and_answers_from_form(vote_form):
            delete_actions(voter, question)

        # TODO: Flash 'Vote submission' deleted
        return redirect(INDEX_RMRF)

    # The user is attempting to submit their vote, we must deal with it
    if vote_form.validate_on_submit():
        error_parsing = False

        for question, answer in questions_and_answers_from_form(vote_form, vote=vote):
            field = "q_{0}".format(question.id)

            action = VoterAction.query.filter_by(vote=vote, voter=voter, question=question).first()

            if not action:
                # If anonymous mode is deleted, then we need to Null out the 'voter' and 'submitted' fields
                if vote.vote_type == VOTE_ANONYMOUS:
                    unix_epoch = datetime.datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0)
                    action = VoterAction(vote=vote, voter=None, question=question, choices="", submitted=unix_epoch,
                                         updated=unix_epoch)
                else:
                    action = VoterAction(vote=vote, voter=voter, question=question, choices="")
            else:
                # Update the actions 'updated' column
                action.updated = datetime.datetime.now()

            if question.question_type == QUESTION_FREETEXT:
                # There's nothing to validate as there are no choices!
                # The format for a 'MultipleChoice' field is just plain text passed through
                action.choices = str(answer)
            elif question.question_type == QUESTION_SINGLECHOICE:
                # Attempt to find the choice object and validate it's associated correctly
                try:
                    choice = VoteChoice.query.get(int(answer))
                except ValueError:
                    getattr(vote_form, field).errors.append("Choice ID {0} is malformed?".format(answer))
                    error_parsing = True
                    break

                if choice.question != question:
                    message = "Choice ID {0} is not associated to this Question?"
                    getattr(vote_form, field).errors.append(message.format(answer))
                    error_parsing = True
                    break

                # The format for a 'SingleChoice' field is a single char string representing the choice_id selected
                action.choices = str(answer)
            elif question.question_type == QUESTION_MULTIPLECHOICE:
                # Attempt to find the choice object(s) and validate they're associated correctly
                for choice_id in answer:
                    try:
                        choice = VoteChoice.query.get(int(choice_id))
                    except ValueError:
                        getattr(vote_form, field).errors.append("Choice ID {0} is malformed?".format(choice_id))
                        error_parsing = True
                        break

                    if choice.question != question:
                        message = "Choice ID {0} is not associated to this Question?"
                        getattr(vote_form, field).errors.append(message.format(choice_id))
                        error_parsing = True
                        break

                # The format for a 'MultiChoice' field is a CSV of all choice_id's selected
                action.choices = ",".join(answer)

            elif question.question_type == QUESTION_RANKED:
                # Attempt to find the choice object(s) and validate they're associated correctly
                for choice_id in answer:
                    try:
                        choice = VoteChoice.query.get(int(choice_id))
                    except ValueError:
                        message = "Choice ID {0} is malformed?"
                        getattr(vote_form, field).errors.append(message.format(choice_id))
                        error_parsing = True
                        break

                    if choice.question != question:
                        message = "Choice ID {0} is not associated to this Question?"
                        getattr(vote_form, field).errors.append(message.format(choice_id))
                        error_parsing = True
                        break

                try:
                    action.choices = json.dumps({key: value for key, value in answer.items()})
                except ValueError as e:
                    message = "Value ID is malformed? {0}"
                    getattr(vote_form, field).errors.append(message.format(e))
                    error_parsing = True
                    break

            db.session.add(action)

        if error_parsing:
            # We failed to save the form, render the vote and the users choices along with any new errors from above
            # TODO: Flash "Vote not saved"?
            delattr(vote_form, "delete")
        else:
            # Record the participation of that voter for that vote
            participation = VoterParticipation(vote, voter)
            db.session.add(participation)

            # 'cast' the vote by committing!
            db.session.commit()

            # TODO: Flash "Vote Recorded"
            return redirect(INDEX_SUBMITTED)

    # The user is attempting to 'view' their ballot, show them their existing vote, or a blank one!
    elif not vote_form.is_submitted():
        # Given a form can only be populated by an object, we dynamically create one
        class DynamicQuestionData(object):
            pass

        question_data = DynamicQuestionData()
        have_data = False

        # Loop over each question on the form, checking to see if the user has any actions
        for question in questions:
            field_name = "q_{0}".format(question.id)
            previous_action = VoterAction.query.filter_by(vote=vote, voter=voter, question=question).first()

            if not previous_action:
                # There has been no previous entry for this question
                continue

            # Check which question type it is, an de-serialise the data form the DB
            if question.question_type == QUESTION_FREETEXT:
                setattr(question_data, field_name, previous_action.choices)
                have_data = True
            elif question.question_type == QUESTION_SINGLECHOICE:
                setattr(question_data, field_name, previous_action.choices)
                have_data = True
            elif question.question_type == QUESTION_MULTIPLECHOICE:
                setattr(question_data, field_name, previous_action.choices.split(","))
                have_data = True
            elif question.question_type == QUESTION_RANKED:
                old_choices = json.loads(previous_action.choices)
                setattr(question_data, field_name, old_choices)

        if have_data:
            # User is reviewing their cast vote, change 'Submit' to 'Update' to better reflect the situation
            form_class.submit.kwargs["label"] = "Update"

            # Create a new form instantiated with our previously entered data
            vote_form = form_class(obj=question_data)
        else:
            # It's a new vote submission, don't provide an option to delete (as there's not actions to delete)
            delattr(form_class, "delete")

    context = {
        "company": app.config["COMPANY_NAME"],
        "vote": vote,
        "form": vote_form
    }

    return render_template("vote_cast.html", **context)
