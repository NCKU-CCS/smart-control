from sqlalchemy.dialects.postgresql import UUID

from config import db
from utils.base_models import SmartRoomBaseMixin


class Rekognition(db.Model, SmartRoomBaseMixin):
    __tablename__ = "rekognition"
    image = db.Column(db.String(80))
    people_count = db.Column(db.Integer)
    rekognition_data = db.Column(db.String())  # Raw Data
    user_id = db.Column(UUID(), db.ForeignKey("user.uuid"), nullable=False)
    user = db.relationship("User")
