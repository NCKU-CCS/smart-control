from sqlalchemy.dialects.postgresql import UUID

from config import db
from utils.base_models import SmartRoomBaseMixin


class LightControl(db.Model, SmartRoomBaseMixin):
    __tablename__ = "lightcontrol"
    # there are two lights in our control
    # command for the first one
    action_front = db.Column(db.String(80))
    # command for the second one
    action_back = db.Column(db.String(80))
    user_id = db.Column(UUID(), db.ForeignKey("user.uuid"), nullable=False)
    user = db.relationship("User")
