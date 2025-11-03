
from fastapi import APIRouter, Depends
from typing import List, Optional
from src.utils.coreData import CoreData
from src.db.crud import get_all_core_data
from sqlalchemy.orm import Session
from src.db.database import get_db

router = APIRouter(
    prefix="/history",
    tags=["History"],
)

@router.get("/tasks", response_model=List[CoreData])
def get_all_history_tasks(db: Session = Depends(get_db)):
    tasks = get_all_core_data(db)
    tasks.sort(key=lambda x: x.created_at, reverse=True)
    return tasks
