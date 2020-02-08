import os


class Config:
    """Parent configuration class."""

    DEBUG = False
    CSRF_ENABLED = True
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_DATABASE_URI = os.environ.get(
    #     "DB_URL", "postgresql://postgres:12345678@localhost:5432/udc"
    # )

    CAPTURE_PATH = os.environ.get("CAPTURE_PATH")


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
