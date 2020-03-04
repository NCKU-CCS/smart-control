import os

from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

load_dotenv()


class Config:
    """Parent configuration class."""

    DEBUG = False
    CSRF_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DB_URL", "postgresql://postgres:12345678@localhost:5432/postgres"
    )
    CAPTURE_PATH = os.environ.get("CAPTURE_PATH")
    SCHEDULER_API_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


class StagingConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


APP_CONFIG = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
}

# pylint: disable=C0103
db = SQLAlchemy()
# pylint: enable=C0103
