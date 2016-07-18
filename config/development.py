import re

from .default import BaseConfig


class DevelopmentConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "totally-not-rigged-123"
    EVERYONE_CAN_CREATE_VOTES = True
