import queue
from typing import Callable

from tasks import LLMCall


class InteractionTask:
    def __init__(self, dag_task: LLMCall, on_finish: Callable):
        self.dag_task: LLMCall = dag_task
        self.on_finish: Callable = on_finish


# typed queue: only holds InteractionTask objects
interaction_queue: queue.Queue[InteractionTask] = queue.Queue()


def queue_consumer():
    while True:
        try:
            task: InteractionTask = interaction_queue.get(timeout=1)
            print(f"Got Task {task.dag_task.desc}")
            print(f"[UserNotifier] Interaction: {task.dag_task.interaction_text}")
            res = input()
            task.dag_task.result = res
            task.on_finish(task.dag_task)
            interaction_queue.task_done()
        except queue.Empty:
            continue
