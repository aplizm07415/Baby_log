from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

# --- Event Schemas ---
class EventBase(BaseModel):
    event_type: str
    is_pee: Optional[bool] = False
    is_poop: Optional[bool] = False
    amount: Optional[int] = None
    side: Optional[str] = None
    condition_code: Optional[str] = None
    note: Optional[str] = None

class EventCreate(EventBase):
    timestamp: Optional[datetime] = None

class EventUpdate(EventBase):
    pass

class Event(EventBase):
    id: uuid.UUID
    timestamp: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

# --- Setting Schemas ---
class SettingBase(BaseModel):
    key: str
    value: str

class SettingCreate(SettingBase):
    pass

class SettingUpdate(SettingBase):
    pass

class Setting(SettingBase):
    class Config:
        from_attributes = True

# --- Prediction Schema ---
class Prediction(BaseModel):
    next_milk_time: Optional[datetime]
    message: str
