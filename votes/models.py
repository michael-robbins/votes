import datetime

from . import app, db


class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    passcode = db.Column(db.String(app.config["PASSCODE_LENGTH"]), nullable=True)
    passcode_generated = db.Column(db.DateTime, default=datetime.datetime.now)
    passcode_used = db.Column(db.Boolean, default=False)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return "<User {0}>".format(self.email)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey(Voter.id))
    owner = db.relationship("Voter", backref=db.backref("votes", lazy="dynamic"))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    vote_type = db.Column(db.String)
    disabled = db.Column(db.Boolean, default=False)
    restrictions = db.Column(db.Text)

    def __init__(self, title, owner, vote_type, start_time=datetime.datetime.now(),
                 end_time=datetime.datetime.now() + datetime.timedelta(days=1), restrictions=""):
        self.title = title
        self.owner = owner
        self.vote_type = vote_type
        self.start_time = start_time
        self.end_time = end_time
        self.restrictions = restrictions

    def __repr__(self):
        return "<Vote '{0}'>".format(self.title)


class VoteQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vote_id = db.Column(db.Integer, db.ForeignKey(Vote.id))
    vote = db.relationship("Vote", backref=db.backref("questions", lazy="dynamic"))
    question_type = db.Column(db.String)
    question_type_max = db.Column(db.Integer)
    question = db.Column(db.Text)

    def __init__(self, vote, question_type, question_type_max, question):
        self.vote = vote
        self.question_type = question_type
        self.question_type_max = question_type_max
        self.question = question

    def __repr__(self):
        return "<VoteQuestion '{0}'>".format(self.question)


class VoteChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey(VoteQuestion.id))
    question = db.relationship("VoteQuestion", backref=db.backref("choices", lazy="dynamic"))
    choice = db.Column(db.Text)

    def __init__(self, question, choice):
        self.question = question
        self.choice = choice

    def __repr__(self):
        return "<VoteChoice '{0}'>".format(self.choice)


class VoterAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vote_id = db.Column(db.Integer, db.ForeignKey(Vote.id))
    vote = db.relationship("Vote", backref=db.backref("actions", lazy="dynamic"))
    voter_id = db.Column(db.Integer, db.ForeignKey(Voter.id), nullable=True)
    voter = db.relationship("Voter", backref=db.backref("actions", lazy="dynamic"))
    submitted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, default=datetime.datetime.now)
    question_id = db.Column(db.Integer, db.ForeignKey(VoteQuestion.id))
    question = db.relationship("VoteQuestion", backref=db.backref("actions", lazy="dynamic"))
    choices = db.Column(db.Text)

    one_vote_per_person = db.UniqueConstraint("vote", "voter", "question", name="OneVoteActionPerPerson")

    def __init__(self, vote, voter, question, choices, submitted=None, updated=None):
        self.vote = vote
        self.voter = voter
        self.question = question
        self.choices = choices

        if submitted:
            self.submitted = submitted

        if updated:
            self.updated = updated

    def __repr__(self):
        return "<VoterAction '{0}'>".format(self.choices)


class VoterParticipation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vote_id = db.Column(db.Integer, db.ForeignKey(Vote.id))
    vote = db.relationship("Vote", backref=db.backref("participants", lazy="dynamic"))
    voter_id = db.Column(db.Integer, db.ForeignKey(Voter.id))
    voter = db.relationship("Voter", backref=db.backref("participations", lazy="dynamic"))

    def __init__(self, vote, voter):
        self.vote = vote
        self.voter = voter

    def __repr__(self):
        return "<VoterParticipation '{0} -> {1}'>".format(self.voter, self.vote)
