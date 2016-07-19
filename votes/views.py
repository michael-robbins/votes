import json

from collections import defaultdict, OrderedDict

from flask import render_template, redirect, request, flash

from .forms import *
from .models import *
from .vote_helper import *


@app.route("/")
@app.route("/index")
@app.route("/votes")
@app.route("/votes/")
def index():
    voter_email = session.get("email")
    voter = get_voter(voter_email)

    if not voter:
        return redirect(LOGIN)

    open_votes = list()
    closed_votes = list()
    owned_votes = list()

    now = datetime.datetime.now()
    for vote in Vote.query.all():
        vote.participated_in = user_has_participated(vote, voter)

        template = "{days}d, {hours}h and {minutes}m"
        vote.closes_in = string_format_delta((vote.end_time - now), template)

        if vote.start_time < now < vote.end_time:
            open_votes.append(vote)

        if vote.end_time <= now:
            closed_votes.append(vote)

        if is_vote_owner(vote, voter):
            owned_votes.append(vote)

    closed_votes.sort(key=lambda x: x.end_time, reverse=True)
    owned_votes.sort(key=lambda x: x.end_time, reverse=True)

    context = {
        "voter": voter,
        "title": "{0} Votes!".format(app.config["COMPANY_NAME"]),
        "open_votes": open_votes,
        "closed_votes": closed_votes,
        "owned_votes": owned_votes,
        "can_create_votes": app.config["EVERYONE_CAN_CREATE_VOTES"] or voter_email in app.config["ADMIN_EMAILS"],
        "quip": "Totally not rigged, promise.",
    }

    return render_template("index.html", **context)


@app.route("/logout")
def logout():
    session["email"] = ""
    flash("Logged out successfully", "success")
    return redirect(LOGIN)


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
    else:
        # Present the form asking for the users passcode
        login_form = AuthForm()

        if login_form.validate_on_submit():
            session["email"] = email
            flash("Successfully logged in as {0}!".format(email), "success")
            return redirect(INDEX_LOGIN)

        template = "auth.html"
        login_form.email.data = email

    context = {
        "company": app.config["COMPANY_NAME"],
        "title": "{0} Votes!".format(app.config["COMPANY_NAME"]),
        "form": login_form,
        "quip": "Totally not rigged, promise.",
    }

    return render_template(template, **context)


@app.route("/votes/new", methods=["GET", "POST"])
def vote_new():
    voter_email = session.get("email")
    voter = get_voter(voter_email)

    if not voter:
        flash("You're not logged in mate.", "danger")
        return redirect(LOGIN_THX)

    if not app.config["EVERYONE_CAN_CREATE_VOTES"] and voter_email not in app.config["ADMIN_EMAILS"]:
        flash("We're only allowing admins to create votes at the moment.", "warning")
        return redirect(INDEX)

    vote_form_class = VoteForm

    # Remove the delete button, as nothing exists yet!
    if hasattr(vote_form_class, "delete"):
        delattr(vote_form_class, "delete")

    new_vote_form = vote_form_class()

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
        flash("Successfully created your Vote!", "success")
        return redirect(INDEX_SUBMITTED)

    context = {
        "voter": voter,
        "form": new_vote_form,
        "header": "New Vote",
        "post_url": "/votes/new",
        "quip": "Totally not rigged, promise.",
    }

    return render_template("vote_crud.html", **context)


@app.route("/votes/<int:vote_id>/edit", methods=["GET", "POST"])
def vote_edit(vote_id):
    voter_email = session.get("email")
    voter = get_voter(voter_email)

    if not voter:
        flash("You're not logged in mate.", "danger")
        return redirect(LOGIN_THX)

    vote = Vote.query.get(vote_id)

    if not vote:
        flash("That vote doesn't exist.", "danger")
        return redirect(INDEX)

    if not is_vote_owner(vote, voter):
        flash("You're not the owner of this vote, so stop trying to hack things.", "danger")
        return redirect(INDEX)

    vote_form = VoteForm()

    if vote_form.is_submitted() and vote_form.data.get("delete"):
        vote_id = vote_form.data.get("id")

        if vote_id:
            vote = Vote.query.get(vote_id)

            if vote:
                if not is_vote_owner(vote, voter):
                    flash("You're not the owner of this vote, so stop trying to hack things.", "danger")
                    return redirect(INDEX)

                delete_vote(vote)

                flash("Vote has been successfully deleted.", "success")
                return redirect(INDEX)
            else:
                flash("The vote you're trying to delete doesn't exist? Stop hacking things.", "warning")
                return redirect(INDEX)
        else:
            flash("You're missing part of the submission form.", "danger")
            return redirect(INDEX)

    if vote_form.validate_on_submit():
        if vote_form.id.data:
            vote = Vote.query.get(vote_form.id.data)

            if vote:
                # Double check the user isn't cheating by changing the Vote ID on us in the form's hidden field
                if not is_vote_owner(vote, voter):
                    flash("You're not the owner of this vote, so stop trying to hack things.", "danger")
                    return redirect(INDEX)

                # Update all the attributes, if the user changed the Vote ID to something else they own, bad luck!
                vote.title = vote_form.title.data
                vote.start_time = vote_form.start_time.data
                vote.end_time = vote_form.end_time.data
                vote.vote_type = vote_form.vote_type.data
                vote.disabled = vote_form.disabled.data
            else:
                flash("You're missing part of the submission form.", "danger")
                return redirect(INDEX)
        else:
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
                        flash("You've submitted a question not belonging to this vote?", "warning")
                        return redirect(INDEX)

                    if vote_question.question_type != question.question_type.data:
                        # Delete all the actions for this question on the vote
                        # As we're changing how we interpret the underlying data
                        delete_actions(voter, vote_question)
                        flash("We deleted all user votes for question {0} as you changed it's type.".format(
                            question.question.data
                        ))

                    vote_question.question_type = question.question_type.data
                    vote_question.question_type_max = question.question_type_max.data
                    vote_question.question = question.question.data
                else:
                    # User submitted a question that doesn't exist
                    flash("One of the questions you submitted doesn't exist?", "warning")
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
                            flash("You've submitted a choice that belongs to a different question.", "warning")
                            return redirect(INDEX)

                        vote_choice.choice = choice.choice.data
                    else:
                        # User submitted for a choice that doesn't exist?
                        flash("One of the choices you submitted doesn't exist?", "danger")
                        return redirect(INDEX)
                else:
                    vote_choice = VoteChoice(question=vote_question, choice=choice.choice.data)

                db.session.add(vote_choice)

        # All questions left in 'existing questions' have been deleted
        for question in existing_questions.values():
            db.session.delete(question)

        db.session.commit()
        flash("Successfully submitted your vote! Thanks for participating!", "success")
        return redirect(INDEX)
    else:
        # If it's not valid and it hasn't been submitted, then overwrite it with the model requested in the GET
        if not vote_form.is_submitted():
            vote_form = VoteForm(obj=vote)
            vote_form.submit.label.text = "Update"
        else:
            # If it has been submitted, then pass it through with all the errors
            pass

    context = {
        "voter": voter,
        "form": vote_form,
        "header": "Edit Vote",
        "post_url": "/votes/{0}/edit".format(vote.id),
        "quip": "Totally not rigged, promise.",
    }

    return render_template("vote_crud.html", **context)


@app.route("/votes/<int:vote_id>/cast", methods=["GET", "POST"])
def vote_cast_crud(vote_id):
    voter_email = session.get("email")
    voter = get_voter(voter_email)

    # Ensure both the voter and the vote exist, bail if they're missing
    if not voter:
        flash("You're not logged in mate.", "danger")
        return redirect(LOGIN)

    vote = Vote.query.get(vote_id)

    if not vote:
        flash("That vote doesn't exist.", "danger")
        return redirect(INDEX)

    if not vote_is_live(vote):
        # They should only have gotten here by messing with the URL!
        flash("The vote is now closed, thank you for your participation.", "info")
        return redirect(INDEX)

    # Do not let the user vote again if we're in anonymous mode and they've participated already
    if vote.vote_type == VOTE_ANONYMOUS and user_has_participated(vote, voter):
        flash("Uhh, you've already participated in this vote.", "warning")
        return redirect(INDEX)

    # If the user is here, that means they are in TrackedBallot mode, or have not voted already for this vote
    # Force the resolution of the questions
    questions = list(vote.questions)

    # Build the dynamic form class based of the questions/choices for this vote
    form_class = build_form_for_questions(questions)
    vote_form = form_class()

    # Handle the user attempting to delete their already cast vote
    if vote_form.is_submitted() and vote_form.data.get("delete"):
        delete_participation(voter, vote)

        flash("Your submission has been deleted, please submit a new vote!", "success")
        return redirect(INDEX)

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
            flash("Your vote failed to submit for some reason, please review your entry and try again.", "warning")
            delattr(vote_form, "delete")
        else:
            # Record the participation of that voter for that vote
            if not user_has_participated(vote, voter):
                participation = VoterParticipation(vote, voter)
                db.session.add(participation)

            # 'cast' the vote by committing!
            db.session.commit()

            flash("Your vote has been recorded, thank you for participating!", "success")
            return redirect(INDEX)

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
                have_data = True

        if have_data:
            # User is reviewing their cast vote, change 'Submit' to 'Update' to better reflect the situation
            form_class.submit.kwargs["label"] = "Update"
        else:
            # It's a new vote submission, don't provide an option to delete (as there's not actions to delete)
            delattr(form_class, "delete")

        # Create a new form instantiated with our previously entered data (or empty object if there's no data)
        vote_form = form_class(obj=question_data)

    context = {
        "voter": voter,
        "vote": vote,
        "form": vote_form,
        "quip": "Totally not rigged, promise."
    }

    return render_template("vote_cast.html", **context)


@app.route("/votes/<int:vote_id>/results")
def vote_result(vote_id):
    voter_email = session.get("email")
    voter = get_voter(voter_email)

    # Ensure both the voter and the vote exist, bail if they're missing
    if not voter:
        flash("You're not logged in mate.", "danger")
        return redirect(LOGIN)

    vote = Vote.query.get(vote_id)

    if not vote:
        flash("That vote doesn't exist.", "danger")
        return redirect(INDEX)

    vote.is_live = vote_is_live(vote)

    questions = VoteQuestion.query.filter_by(vote=vote).all()
    results = defaultdict(dict)
    choice_names = dict()

    class ChoiceResults(object):
        pass

    for question in questions:
        actions = VoterAction.query.filter_by(vote=vote, question=question).all()
        choices = VoteChoice.query.filter_by(question=question).all()

        question_key = question.id

        # Set the default result for this question
        if question.question_type == QUESTION_FREETEXT:
            results[question_key] = list()

            if vote.is_live:
                results[question_key].append("Vote is live, so no results are available for FreeText questions yet.")
        else:
            # All other types will have their individual choices incremented according to the question_type
            for choice in choices:
                choice_id = int(choice.id)
                results[question_key][choice_id] = ChoiceResults()
                results[question_key][choice_id].name = VoteChoice.query.get(choice_id).choice
                results[question_key][choice_id].results = 0

        for action in actions:
            if question.question_type == QUESTION_FREETEXT:
                # We just append each persons text into the results list for this question, there's no counting
                if not vote.is_live:
                    results[question_key].append('"{0}"'.format(action.choices))

            elif question.question_type == QUESTION_MULTIPLECHOICE:
                # Each 'selected' choice in a multiple choice question increments the vote for that choice by 1
                for choice_id in str(action.choices).split(","):
                    choice_id = int(choice_id)
                    results[question_key][choice_id].results += 1

            elif question.question_type == QUESTION_SINGLECHOICE:
                # Each persons choice increments the vote for that choice by 1
                choice_id = int(action.choices)
                results[question_key][choice_id].results += 1

            elif question.question_type == QUESTION_RANKED:
                # Each choice gets incremented by the inverse of the rank chosen ((question_type_max + 1) - rank)
                for choice_id, rank in json.loads(action.choices).items():
                    if rank == "":
                        # There are no votes for this choice yet! Just skip calculating with it
                        continue

                    choice_id = int(choice_id)
                    results[question_key][choice_id].results += (int(question.question_type_max) + 1) - int(rank)

        # Sort the results by highest voted
        if question.question_type != QUESTION_FREETEXT:
            results[question_key] = OrderedDict(sorted(results[question_key].items(), key=lambda x: x[1].results,
                                                       reverse=True))

            if vote.is_live:
                # Used for when a Vote is live, and we want to mask the choice names
                # We handle up to 26 * 26 choices per question (let's hope we never get that many!
                next_choice = 65  # 'A'
                choice_prefix = ""

                for choice_id, result in results[question_key].items():
                    result.name = "Option {0}{1}".format(choice_prefix, chr(next_choice))

                    next_choice += 1
                    if next_choice > 90:
                        if not choice_prefix:
                            choice_prefix = "A"
                        else:
                            if ord(choice_prefix) > ord("Z"):
                                raise Exception("Too many choices!")

                            choice_prefix = chr(ord(choice_prefix) + 1)

                        # Reset the masked choice back to 'A' and repeat
                        next_choice = 65

    context = {
        "voter": voter,
        "vote": vote,
        "questions": questions,
        "choice_names": choice_names,
        "results": results,
        "quip": "Totally not rigged, promise.",
    }

    return render_template("vote_result.html", **context)
