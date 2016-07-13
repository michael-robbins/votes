from votes.models import *

import json

db.drop_all()
db.create_all()

voter_1 = Voter("mrobbins@connexity.com")
db.session.add(voter_1)

vote_1 = Vote("Awesome Competition", voter_1)
db.session.add(vote_1)
db.session.commit()

vote_1_question_1 = VoteQuestion(vote_1, "SingleChoice", 1, "Is Michael awesome?")
vote_1_question_1_choice_1 = VoteChoice(vote_1_question_1, "Yes!")
vote_1_question_1_choice_2 = VoteChoice(vote_1_question_1, "No!")

db.session.add(vote_1_question_1)
db.session.add(vote_1_question_1_choice_1)
db.session.add(vote_1_question_1_choice_2)
db.session.commit()


vote_1_question_2 = VoteQuestion(vote_1, "MultipleChoice", 2, "Which 2 are awesome?")
vote_1_question_2_choice_1 = VoteChoice(vote_1_question_2, "Michael")
vote_1_question_2_choice_2 = VoteChoice(vote_1_question_2, "Andrew")
vote_1_question_2_choice_3 = VoteChoice(vote_1_question_2, "Tom")

db.session.add(vote_1_question_2)
db.session.add(vote_1_question_2_choice_1)
db.session.add(vote_1_question_2_choice_2)
db.session.add(vote_1_question_2_choice_3)
db.session.commit()

vote_1_question_3 = VoteQuestion(vote_1, "FreeText", 1, "Why should Michael win?")

db.session.add(vote_1_question_3)
db.session.commit()

vote_1_question_4 = VoteQuestion(vote_1, "Ranked", 3, "Rank the contestants!")
vote_1_question_4_choice_1 = VoteChoice(vote_1_question_4, "Michael")
vote_1_question_4_choice_2 = VoteChoice(vote_1_question_4, "Andrew")
vote_1_question_4_choice_3 = VoteChoice(vote_1_question_4, "Tom")

db.session.add(vote_1_question_4)
db.session.add(vote_1_question_4_choice_1)
db.session.add(vote_1_question_4_choice_2)
db.session.add(vote_1_question_4_choice_3)
db.session.commit()


single_choice_answer = vote_1_question_1_choice_1.id
multiple_choice_answer = "{0}".format(vote_1_question_2_choice_1.id)
freetext_answer = "Because he's awesome!"
ranked_choice_answer = {
    vote_1_question_4_choice_1.id: 1,
    vote_1_question_4_choice_2.id: 2,
    vote_1_question_4_choice_3.id: 3
}

vote_1_voter_1_action_1 = VoterAction(vote_1, voter_1, vote_1_question_1, vote_1_question_1_choice_1.id)
vote_1_voter_1_action_2 = VoterAction(vote_1, voter_1, vote_1_question_2, multiple_choice_answer)
vote_1_voter_1_action_3 = VoterAction(vote_1, voter_1, vote_1_question_3, freetext_answer)
vote_1_voter_1_action_4 = VoterAction(vote_1, voter_1, vote_1_question_4, json.dumps(ranked_choice_answer))

db.session.add(vote_1_voter_1_action_1)
db.session.add(vote_1_voter_1_action_2)
db.session.add(vote_1_voter_1_action_3)
db.session.add(vote_1_voter_1_action_4)
db.session.commit()
