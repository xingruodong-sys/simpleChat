import argparse
import importlib
import sys
import pkgutil
import src.task
import asyncio
import inspect

def main():
    parser = argparse.ArgumentParser(description="Run a specific task in src.task")
    parser.add_argument("-t", "--task", required=True, help="Task name to run (e.g. monitor)")
    args, unknown = parser.parse_known_args()

    task_name = args.task
    package = src.task
    available_tasks = [name for _, name, is_pkg in pkgutil.iter_modules(package.__path__) if not is_pkg]

    if task_name not in available_tasks:
        print(f"❌ Task '{task_name}' not found.")
        print(f"Available tasks: {', '.join(available_tasks)}")
        sys.exit(1)

    try:
        module = importlib.import_module(f"{package.__name__}.{task_name}")
        if hasattr(module, "main") and callable(module.main):
            main_func = module.main
            if inspect.iscoroutinefunction(main_func):
                asyncio.run(main_func(unknown))
            else:
                main_func(unknown)
        else:
            print(f"⚠️ Task '{task_name}' does not define a callable 'main()' function.")
            sys.exit(1)
    except ModuleNotFoundError as e:
        print(f"⚠️ Missing dependency: {e.name}")
        print(f"👉 Try installing it with:\n   pip install {e.name}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running task '{task_name}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
