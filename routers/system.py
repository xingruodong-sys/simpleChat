import os
import sys
import time
from fastapi import APIRouter, BackgroundTasks

# --- Router Initialization ---
router = APIRouter(
    prefix="/system",
    tags=["System"],
)

def delayed_exit():
    """Waits a moment then exits the process."""
    time.sleep(1)
    # sys.exit(0)
    os._exit(0)  # 或 raise SystemExit

# --- API Endpoints ---

@router.post("/restart")
async def restart_server(background_tasks: BackgroundTasks):
    """
    Triggers a server restart.
    The server process will exit after a short delay.
    A process manager (like Gunicorn, systemd, Docker) is expected to restart it.
    """
    background_tasks.add_task(delayed_exit)
    return {"message": "Server is restarting..."}
