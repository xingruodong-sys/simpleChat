import importlib
import importlib.util
import sys
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

# Add the project root to the python path to allow absolute imports from the router
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

router = APIRouter()

def run_task_in_background(task_name: str):
    """
    Wrapper function to dynamically import and run a task.
    This is what will be executed by BackgroundTasks.
    """
    try:
        module_path = f"src.task.{task_name}"
        task_module = importlib.import_module(module_path)
        
        if hasattr(task_module, 'run'):
            print(f"Starting background task: {task_name}")
            task_module.run()
            print(f"Background task '{task_name}' finished.")
        else:
            # Log this error, as we cannot return an HTTP response from a background task
            print(f"Error: Task module '{task_name}' does not have a 'run' function.", file=sys.stderr)
            
    except ModuleNotFoundError:
        print(f"Error: Task module '{task_name}' not found.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred in background task '{task_name}': {e}", file=sys.stderr)

@router.post("/tasks/run/{task_name}", tags=["tasks"], status_code=status.HTTP_202_ACCEPTED)
async def start_task(
    task_name: str,
    background_tasks: BackgroundTasks
):
    """
    Starts a task in the background.

    - **task_name**: The name of the task module to run (e.g., 'readCpp').
    """
    # Check if the task module exists before starting it
    module_spec = importlib.util.find_spec(f"src.task.{task_name}")
    if module_spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_name}' not found."
        )

    background_tasks.add_task(run_task_in_background, task_name)
    
    return {"message": f"Task '{task_name}' has been started in the background."}
