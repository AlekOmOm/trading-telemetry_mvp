import asyncio
import logging
from typing import Dict

class TaskManager:
    """Minimal task manager for coordinating async operations"""
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.stop_signal = asyncio.Event()
        self.logger = logging.getLogger(__name__)

    def add_task(self, coro, name: str) -> asyncio.Task:
        """Add a task to the task manager.
        
        Args:
            coro: The coroutine to run.
            name: The name of the task.

        Returns:
            The task.
        """
        task = asyncio.create_task(coro) 
        self.tasks[name] = task
        self.logger.info(f"Added task: {name}")
        return task

    def cancel_all_tasks(self):
        """Cancel all managed tasks"""
        for name, task in self.tasks.items():
            if not task.done():
                self.logger.info(f"Cancelling task: {name}")
                task.cancel()

    async def catch_breaking_errors(self):
        """Monitor for any unhandled exceptions in tasks"""
        try:
            """ Monitor for stop signal and any unhandled exceptions in tasks """
            while not self.stop_signal.is_set():
                await asyncio.sleep(1)
                # Check for failed tasks
                for name, task in self.tasks.items():
                    if task.done() and not task.cancelled():
                        try:
                            task.result()  # This will raise if task failed
                        except Exception as e:
                            self.logger.error(f"Task {name} failed: {e}")
                            self.stop_signal.set()
                            return
        except asyncio.CancelledError:
            pass