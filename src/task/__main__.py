import argparse
import importlib
import sys
import pkgutil
import src.task  # 关键：显式导入包本身

def main():
    parser = argparse.ArgumentParser(description="Run a specific task in src.task")
    parser.add_argument("-t", "--task", required=True, help="Task name to run (e.g. readCpp)")
    args, unknown = parser.parse_known_args()

    task_name = args.task

    # ✅ 从 src.task 包中列出所有模块
    package = src.task
    available_tasks = [name for _, name, is_pkg in pkgutil.iter_modules(package.__path__) if not is_pkg]

    if task_name not in available_tasks:
        print(f"❌ Task '{task_name}' not found.")
        print(f"Available tasks: {', '.join(available_tasks)}")
        sys.exit(1)

    try:
        module = importlib.import_module(f"{package.__name__}.{task_name}")
        if hasattr(module, "main") and callable(module.main):
            module.main(unknown)  # 把其他参数传进去
        else:
            print(f"⚠️ Task '{task_name}' does not define a callable 'main()' function.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error running task '{task_name}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
