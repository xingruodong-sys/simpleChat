import os
import sys
import time
from fastapi import APIRouter, BackgroundTasks, HTTPException
from starlette.responses import FileResponse


# --- Router Initialization ---
router = APIRouter(
    tags=["System"],
)

def delayed_exit():
    """Waits a moment then exits the process."""
    time.sleep(1)
    # sys.exit(0)
    os._exit(0)  # 或 raise SystemExit

# --- API Endpoints ---

@router.post("/system/restart")
async def restart_server(background_tasks: BackgroundTasks):
    """
    Triggers a server restart.
    The server process will exit after a short delay.
    A process manager (like Gunicorn, systemd, Docker) is expected to restart it.
    """
    background_tasks.add_task(delayed_exit)
    return {"message": "Server is restarting..."}


LOG_DIR = "./Log"

@router.get("/system/logs/{filename}", summary="Download a system log file")
async def download_log_file(filename: str):
    """
    Downloads a system log file.
    Performs security checks to prevent directory traversal.
    """
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = os.path.join(LOG_DIR, filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename
    )
