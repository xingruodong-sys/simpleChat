from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.db.crud import get_active_core_data
from src.utils.coreData import CoreDataMain

# --- Router Initialization ---
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)

@router.get("/tasks", response_model=List[CoreDataMain])
def get_all_monitoring_tasks(db: Session = Depends(get_db)):
    tasks = get_active_core_data(db)
    tasks.sort(key=lambda x: x.created_at, reverse=True)
    return tasks
