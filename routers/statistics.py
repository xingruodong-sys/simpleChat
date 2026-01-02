from fastapi import APIRouter
from src.helper.Redis import redis
import json

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)

@router.get("/effective_ip")
def get_effective_ip_statistics():
    data = redis.hgetall("analyze_effective_table")
    results = []
    if data:
        for key, value in data.items():
            try:
                item = json.loads(value)
                results.append(item)
            except json.JSONDecodeError:
                continue
    return results
