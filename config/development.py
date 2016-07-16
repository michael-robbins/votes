import re

from .default import BaseConfig


class DevelopmentConfig(BaseConfig):
    SECRET_KEY = "totally-not-rigged-123"
    EVERYONE_CAN_CREATE_VOTES = True
