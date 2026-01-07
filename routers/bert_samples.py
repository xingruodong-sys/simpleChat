from fastapi import APIRouter, HTTPException, Query
from src.helper.Redis import redis
from src.helper.Redis import (
    BL_COMPONENTS_SEARCH_HASH,
    BL_COMPONENTS_HMI_HASH,
    BL_COMPONENTS_SYSTEM_HASH,
    BL_COMPONENTS_MAP_HASH,
    BL_COMPONENTS_DBU_POS_HASH,
    BL_COMPONENTS_ACTIVITION_HASH,
    BL_COMPONENTS_GUIDANCE_HASH,
    BL_COMPONENTS_ROUTE_HASH,
    BL_COMPONENTS_TI_HASH,
    BL_COMPONENTS_ACTIVITION_DBU_HASH,
    BL_COMPONENTS_HMI_VR_HASH,
    BL_COMPONENTS_PERFORMANCE_HASH,
    COMPONENTS_OTHER_HASH,
    SUMMARY,
    REALMODULE,
    COMMITMODULE,
    USER
)
import json
from typing import List, Dict, Any

router = APIRouter(
    prefix="/bert_samples",
    tags=["BERT Samples"],
)

# Key Mapping
COMPONENT_MAPPING = {
    'HMI': BL_COMPONENTS_HMI_HASH,
    'Search (DI_POI_SDS)': BL_COMPONENTS_SEARCH_HASH,
    'System': BL_COMPONENTS_SYSTEM_HASH,
    'MapViewer': BL_COMPONENTS_MAP_HASH,
    'DBU & Positioning': BL_COMPONENTS_DBU_POS_HASH,
    'Activation': BL_COMPONENTS_ACTIVITION_HASH,
    'Guidance': BL_COMPONENTS_GUIDANCE_HASH,
    'Route Calculation': BL_COMPONENTS_ROUTE_HASH,
    'TI': BL_COMPONENTS_TI_HASH,
    'Activation DBU': BL_COMPONENTS_ACTIVITION_DBU_HASH,
    'HMI VR': BL_COMPONENTS_HMI_VR_HASH,
    'Performance': BL_COMPONENTS_PERFORMANCE_HASH,
    'Other': COMPONENTS_OTHER_HASH
}

@router.get("/categories")
def get_categories() -> List[str]:
    """Returns the list of available component categories."""
    return list(COMPONENT_MAPPING.keys())

@router.get("/data")
def get_bert_samples(category: str = Query(..., description="The component category to fetch")) -> List[Dict[str, Any]]:
    """
    Fetches the BERT samples for a given category from Redis.
    """
    if category not in COMPONENT_MAPPING:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    redis_key = COMPONENT_MAPPING[category]
    try:
        data = redis.hgetall(redis_key)
        parsed_data = []
        for issue_key, json_str in data.items():
            try:
                if isinstance(json_str, bytes):
                    json_str = json_str.decode('utf-8')
                
                item = json.loads(json_str)
                parsed_data.append({
                    "Issue Key": issue_key,
                    "Summary": item.get(SUMMARY, ""),
                    "Real Module": item.get(REALMODULE, ""),
                    "Commit Module": item.get(COMMITMODULE, ""),
                    "User": item.get(USER, "")
                })
            except json.JSONDecodeError:
                continue
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
