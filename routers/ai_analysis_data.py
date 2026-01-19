from fastapi import APIRouter, HTTPException
from src.helper.Redis import redis
import json

router = APIRouter()

@router.get("/ai_analysis_data")
def get_ai_analysis_data():
    try:
        data = redis.hgetall('CHANGE_NAME_TO_TEAM_TABLE')
        result = []
        for key, value in data.items():
            try:
                row = json.loads(value)
                result.append(row)
            except json.JSONDecodeError:
                continue  # 跳过无效的 JSON
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))