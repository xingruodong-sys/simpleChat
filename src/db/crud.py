from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models

def get_core_data_main(db: Session, id: str):
    return db.query(models.CoreDataMain).filter(models.CoreDataMain.id == id).first()

def create_core_data_main(db: Session, core_data: models.CoreDataMain):
    db.add(core_data)
    db.commit()
    db.refresh(core_data)
    return core_data

def update_core_data_main(db: Session, core_data: models.CoreDataMain):
    db.commit()
    db.refresh(core_data)
    return core_data

def get_core_data_sub(db: Session, id: int):
    return db.query(models.CoreDataSub).filter(models.CoreDataSub.id == id).first()

def create_core_data_sub(db: Session, core_data: models.CoreDataSub):
    db.add(core_data)
    db.commit()
    db.refresh(core_data)
    return core_data

def update_core_data_sub(db: Session, core_data: models.CoreDataSub):
    db.commit()
    db.refresh(core_data)
    return core_data

def get_latest_core_data_sub_by_main_id(db: Session, main_id: str) -> models.CoreDataSub | None:
    return (
        db.query(models.CoreDataSub)
        .filter(models.CoreDataSub.main_id == main_id)
        .order_by(desc(models.CoreDataSub.id))
        .offset(1)
        .first()
    )

def get_latest_core_data_sub_by_main_id_ex(db: Session, main_id: str) -> models.CoreDataSub | None:
    return (
        db.query(models.CoreDataSub)
        .filter(models.CoreDataSub.main_id == main_id)
        .order_by(desc(models.CoreDataSub.id))
        .first()
    )

def get_core_data_sub_by_main_id(db: Session, main_id: str) -> models.CoreDataSub | None:
    return (
        db.query(models.CoreDataSub)
        .filter(models.CoreDataSub.main_id == main_id)
        .order_by(desc(models.CoreDataSub.id))
        .all()
    )

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
    return db.query(models.CoreDataMain).filter(models.CoreDataMain.status.not_in([92, 93, 94, 95, 96, 99, 97, 98])).all()

def get_all_core_data(db: Session):
    return db.query(models.CoreDataMain).all()

def get_all_sub_core_data(db: Session):
    return db.query(models.CoreDataSub).all()

def get_core_data_by_date_range(db: Session, start_ts: float, end_ts: float):
    return db.query(models.CoreDataMain).filter(models.CoreDataMain.created_at >= start_ts, models.CoreDataMain.created_at <= end_ts).all()

def get_core_data_for_bert_correct(db: Session):
    return db.query(models.CoreDataMain).filter(models.CoreDataMain.bert_correct == 0).all()

def get_core_data_berted(db: Session):
    return db.query(models.CoreDataMain).filter(models.CoreDataMain.bert_component != "").all()