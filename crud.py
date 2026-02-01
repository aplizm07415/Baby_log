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
    event_data = event.model_dump()
    # If timestamp is not provided by client, remove it to use server_default
    if "timestamp" in event_data and event_data["timestamp"] is None:
        del event_data["timestamp"]

    db_event = models.Event(**event_data)
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

def get_next_milk_prediction(db: Session) -> schemas.MilkPrediction:
    recent_milk_events = db.query(models.Event).filter(
        models.Event.event_type.in_(["milk", "breastfeeding"]),
        models.Event.is_deleted == False
    ).order_by(models.Event.timestamp.desc()).limit(3).all()

    last_event = recent_milk_events[0] if recent_milk_events else None
    
    # Plan
    plan_time = (last_event.timestamp + timedelta(hours=3)) if last_event else None
    plan_message = f"計画（3時間後）では{plan_time.strftime('%H:%M')}頃です" if plan_time else "記録がまだなく計画を計算できません"

    # Prediction
    if len(recent_milk_events) < 2:
        if last_event:
            return schemas.MilkPrediction(message="データ不足のため、まずは計画を参考にしてください。", plan_time=plan_time, plan_message=plan_message)
        else:
             return schemas.MilkPrediction(message="まだ授乳の記録がありません。", plan_message=plan_message)

    intervals = [(recent_milk_events[i].timestamp - recent_milk_events[i+1].timestamp).total_seconds() for i in range(len(recent_milk_events) - 1)]
    avg_interval = sum(intervals) / len(intervals)
    predicted_next_time = recent_milk_events[0].timestamp + timedelta(seconds=avg_interval)

    return schemas.MilkPrediction(next_time=predicted_next_time, message=f"次の授乳は約{int(avg_interval / 60)}分後の予測です。", plan_time=plan_time, plan_message=plan_message)

def get_next_diaper_prediction(db: Session) -> schemas.DiaperPrediction:
    recent_diaper_events = db.query(models.Event).filter(
        models.Event.event_type == "diaper",
        models.Event.is_deleted == False
    ).order_by(models.Event.timestamp.desc()).limit(5).all()

    last_event = recent_diaper_events[0] if recent_diaper_events else None

    # Plan
    plan_time = (last_event.timestamp + timedelta(hours=2)) if last_event else None
    plan_message = f"計画（2時間後）では{plan_time.strftime('%H:%M')}頃です" if plan_time else "記録がまだなく計画を計算できません"

    # Prediction
    if len(recent_diaper_events) < 2:
        if last_event:
            return schemas.DiaperPrediction(message="データ不足のため、まずは計画を参考にしてください。", plan_time=plan_time, plan_message=plan_message)
        else:
            return schemas.DiaperPrediction(message="まだおむつの記録がありません。", plan_message=plan_message)

    intervals = [(recent_diaper_events[i].timestamp - recent_diaper_events[i+1].timestamp).total_seconds() for i in range(len(recent_diaper_events) - 1)]
    avg_interval = sum(intervals) / len(intervals)
    predicted_next_time = recent_diaper_events[0].timestamp + timedelta(seconds=avg_interval)

    return schemas.DiaperPrediction(next_time=predicted_next_time, message=f"次のおむつ交換は約{int(avg_interval / 60)}分後の予測です。", plan_time=plan_time, plan_message=plan_message)

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
