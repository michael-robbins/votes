from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object("config.development.DevelopmentConfig")
db = SQLAlchemy(app)

from . import views, models
