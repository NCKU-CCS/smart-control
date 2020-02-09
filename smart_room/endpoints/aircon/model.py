from sqlalchemy.dialects.postgresql import UUID

from config import db
from utils.base_models import SmartRoomBaseMixin


class Aircon(db.Model, SmartRoomBaseMixin):
    __tablename__ = "aircon"
    action = db.Column(db.String(80))
    time = db.Column(db.DateTime)
    user_id = db.Column(UUID(), db.ForeignKey("user.uuid"), nullable=False)
    user = db.relationship("User")
