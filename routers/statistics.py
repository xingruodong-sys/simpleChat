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

@router.get("/manual_efficiency")
def get_manual_statistics():
    data = redis.hgetall("FIRST_ANALYZE_HASH")
    results = []
    if data:
        for key, value in data.items():
            try:
                item = json.loads(value)
                results.append(item)
            except json.JSONDecodeError:
                continue
    return results

@router.get("/bert_correct")
def get_bert_correct_statistics():
    data = redis.hgetall("bert_correct_table")
    results = []
    if data:
        for key, value in data.items():
            try:
                item = json.loads(value)
                results.append(item)
            except json.JSONDecodeError:
                continue
    return results

@router.get("/bert_correct_history")
def get_bert_correct_history():
    data = redis.lrange("BERT_CORRECT_WEEKLY_STATS", 0, -1)
    results = []
    if data:
        for item in data:
            try:
                results.append(json.loads(item))
            except json.JSONDecodeError:
                continue
    return results
