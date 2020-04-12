from config import db
from utils.base_models import SmartRoomBaseMixin


class User(db.Model, SmartRoomBaseMixin):
    __tablename__ = "user"
    account = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=False)  # Login Bearer Tag
