from sqlalchemy.orm import Session
from . import models

def get_core_data(db: Session, id: str):
    return db.query(models.CoreData).filter(models.CoreData.id == id).first()

def create_core_data(db: Session, core_data: models.CoreData):
    db.add(core_data)
    db.commit()
    db.refresh(core_data)
    return core_data

def update_core_data(db: Session, core_data: models.CoreData):
    db.commit()
    db.refresh(core_data)
    return core_data

def get_key_value(db: Session, category: str, key: str):
    return db.query(models.KeyValue).filter(models.KeyValue.category == category, models.KeyValue.key == key).first()

def set_key_value(db: Session, category: str, key: str, value: str):
    db_kv = get_key_value(db, category, key)
    if db_kv:
        db_kv.value = value
    else:
        db_kv = models.KeyValue(category=category, key=key, value=value)
        db.add(db_kv)
    db.commit()
    return db_kv

def get_all_by_category(db: Session, category: str):
    return db.query(models.KeyValue).filter(models.KeyValue.category == category).all()

def delete_key_value(db: Session, category: str, key: str):
    db_kv = get_key_value(db, category, key)
    if db_kv:
        db.delete(db_kv)
        db.commit()

def get_active_core_data(db: Session):
    return db.query(models.CoreData).filter(models.CoreData.status.not_in([99, 97, 98])).all()

def get_all_core_data(db: Session):
    return db.query(models.CoreData).all()

def get_core_data_by_date_range(db: Session, start_ts: float, end_ts: float):
    return db.query(models.CoreData).filter(models.CoreData.created_at >= start_ts, models.CoreData.created_at <= end_ts).all()
