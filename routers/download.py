import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from src.utils import settings


router = APIRouter()

@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    logPath = settings.get_llm_monitoring_settings()
    full_path = os.path.join(logPath.analyzedLogPath, file_path)

    if not os.path.exists(full_path):
        return {"error": "File or directory not found"}

    if os.path.isdir(full_path):
        files = os.listdir(full_path)
        links = [
            f'<li><a href="/download/{file_path}/{f}">{f}</a></li>' for f in files
        ]
        html_content = "<ul>" + "".join(links) + "</ul>"
        return HTMLResponse(content=html_content, status_code=200)

    return FileResponse(path=full_path, filename=os.path.basename(full_path))
