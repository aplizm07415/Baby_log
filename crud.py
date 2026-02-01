from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import models, schemas
import uuid

# --- Event CRUD ---

def get_event(db: Session, event_id: uuid.UUID) -> Optional[models.Event]:
    return db.query(models.Event).filter(models.Event.id == event_id, models.Event.is_deleted == False).first()

def get_events(db: Session, skip: int = 0, limit: int = 100, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[models.Event]:
    query = db.query(models.Event).filter(models.Event.is_deleted == False)
    if start_date:
        query = query.filter(models.Event.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Event.timestamp <= end_date)
    return query.order_by(models.Event.timestamp.desc()).offset(skip).limit(limit).all()

def create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    db_event = models.Event(**event.model_dump())
    if event.timestamp is None:
        db_event.timestamp = datetime.utcnow()
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def update_event(db: Session, event_id: uuid.UUID, event_data: schemas.EventUpdate) -> Optional[models.Event]:
    db_event = get_event(db, event_id)
    if db_event:
        update_data = event_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_event, key, value)
        db.commit()
        db.refresh(db_event)
    return db_event

def delete_event(db: Session, event_id: uuid.UUID) -> Optional[models.Event]:
    db_event = get_event(db, event_id)
    if db_event:
        db_event.is_deleted = True
        db.commit()
        db.refresh(db_event)
    return db_event

# --- Prediction Logic ---

def get_next_milk_prediction(db: Session) -> schemas.Prediction:
    # Get the last 3 milk events
    recent_milk_events = db.query(models.Event).filter(
        models.Event.event_type.in_(["milk", "breastfeeding"]),
        models.Event.is_deleted == False
    ).order_by(models.Event.timestamp.desc()).limit(3).all()

    if len(recent_milk_events) < 2:
        # Not enough data, use default interval (3 hours) from the last event if it exists
        last_event = recent_milk_events[0] if recent_milk_events else None
        if last_event:
            next_time = last_event.timestamp + timedelta(hours=3)
            return schemas.Prediction(next_milk_time=next_time, message="まだデータが少ないため、3時間後を目安にしています。")
        else:
             return schemas.Prediction(next_milk_time=None, message="まだミルクの記録がありません。")


    # Calculate the average interval
    intervals = []
    for i in range(len(recent_milk_events) - 1):
        interval = recent_milk_events[i].timestamp - recent_milk_events[i+1].timestamp
        intervals.append(interval.total_seconds())
    
    avg_interval_seconds = sum(intervals) / len(intervals)
    
    last_milk_time = recent_milk_events[0].timestamp
    predicted_next_time = last_milk_time + timedelta(seconds=avg_interval_seconds)

    return schemas.Prediction(next_milk_time=predicted_next_time, message=f"直近の平均授乳間隔は約{int(avg_interval_seconds / 60)}分です。")

# --- Settings CRUD (example) ---

def get_setting(db: Session, key: str) -> Optional[models.Setting]:
    return db.query(models.Setting).filter(models.Setting.key == key).first()

def create_or_update_setting(db: Session, setting: schemas.SettingCreate) -> models.Setting:
    db_setting = get_setting(db, setting.key)
    if db_setting:
        db_setting.value = setting.value
    else:
        db_setting = models.Setting(**setting.model_dump())
        db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting
