from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func, text as sa_text
import sqlalchemy.types as types

from config import db


# pylint: disable=W0223
class UUID2STR(types.TypeDecorator):
    impl = UUID(as_uuid=True)

    def process_result_value(self, value, dialect):
        return str(value)


# pylint: enable=W0223


class SmartRoomBaseMixin:
    uuid = db.Column(
        UUID2STR,
        primary_key=True,
        unique=True,
        nullable=False,
        server_default=sa_text("uuid_generate_v4()"),
    )
    create_time = db.Column(db.DateTime, server_default=func.now())
    update_time = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    def add(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return self.uuid
