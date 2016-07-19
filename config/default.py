import os
import re
import random
import string

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    DEBUG = False
    TESTING = False

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    SECRET_KEY = ''.join([random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase +
                                                       string.ascii_letters + string.punctuation) for i in range(50)])

    # SQL Alchemy
    SQLALCHEMY_DATABASE_URI = "sqlite:///{database}".format(database=os.path.join(basedir, "../votes.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Compiled regex that all user emails must conform to
    VALID_EMAIL_REGEX = re.compile(r".*")

    # The Mail Exchange server and credentials that passcode emails will be sent to
    MX_SERVER = "localhost"
    MX_PORT = ""
    MX_USER = ""
    MX_PASSWORD = ""

    # Branding options
    COMPANY_NAME = "DefaultCompany"
    COMPANY_IMAGE = ""  # URL to your company's image

    # Passcode settings
    PASSCODE_LENGTH = 8
    PASSCODE_POOL = string.ascii_uppercase + string.digits
    PASSCODE_EMAIL_SUBJECT = "{0} Votes - Passcode Request".format(COMPANY_NAME)

    # Available template variables:
    # email: The users email address
    # passcode: The generated passcode
    # generated: The time the passcode was generated
    # company: The name of the company as set above
    PASSCODE_EMAIL_BODY = """
Hi {email},

Here's your single-use passcode you can use to log into the {company} voting system.
Passcode: {passcode}
Generated at: {generated}

You only have 5 minutes to use the above passcode.
After this you will need to generate a new one after that (by logging in again).

Warm Regards,
{company}
"""

    # Iterable of email addresses that will be treated like vote owners for vote editing purposes
    ADMIN_EMAILS = list()

    # Do we allow non-admin users to create votes
    EVERYONE_CAN_CREATE_VOTES = False

    # Restrict certain email addresses from submitting rankings to certain choices
    # The idea behind this was to stop 'teams' voting for themselves in a RankedField
    RANKED_FIELD_RESTRICTIONS = {
        "Team #1": [
            "team-1-member-1@company.com",
            "team-1-member-2@company.com",
        ],
        "Team #2": [
            "team-2-member-1@company.com",
            "team-2-member-2@company.com"
        ],
    }
