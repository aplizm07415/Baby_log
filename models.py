import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, index=True, nullable=False)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    is_pee = Column(Boolean, default=False)
    is_poop = Column(Boolean, default=False)
    amount = Column(Integer, nullable=True)  # ml or minutes
    side = Column(String, nullable=True) # "left", "right"
    condition_code = Column(String, nullable=True) # "normal", "soft", "diarrhea"
    note = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
