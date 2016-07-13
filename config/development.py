from .default import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True
