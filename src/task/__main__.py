from src.task import monitor
import asyncio

asyncio.run(monitor.check_stuck_tasks_main())
