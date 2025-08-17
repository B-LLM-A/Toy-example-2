import time
from graphlib import TopologicalSorter
import concurrent.futures
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from queue_consumer import interaction_queue, InteractionTask
from tasks import Task, LLMCall, WebSearch

# Define a DAG (dependencies: a -> b means a must run before b)
A = WebSearch("A", deps=[])
B = LLMCall("B", deps=[A])
C = LLMCall("C", deps=[A])
D = WebSearch("D", deps=[B, C])
nodes: List[Task] = [A, B, C, D]

graph = {x: x.deps for x in nodes}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def worker(task: Task):
    print(f"Starting [task description: {task.desc}]")
    print(f"with deps:[{', '.join([x.desc for x in graph[task]])}]")
    task.run()
    print(f"Finished {task.desc}")
    return task


def run_dag(graph):
    ts = TopologicalSorter(graph)
    ts.prepare()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {}
        while ts.is_active():
            time.sleep(0.5)
            # Get all ready-to-run nodes
            ready = ts.get_ready()
            for task in ready:
                futures[executor.submit(worker, task)] = task

            # Wait for one task to finish
            done, _ = concurrent.futures.wait(
                futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED
            )

            for fut in done:
                task = futures.pop(fut)
                try:
                    task.result = fut.result()
                    if isinstance(task, LLMCall):
                        print("The type of task is LLMCall")
                        interaction_queue.put(InteractionTask(task, lambda x: ts.done(x)))
                    else:
                        print(type(task))
                        ts.done(task)
                except Exception as e:
                    task.exception = e
                    ts.done(task)
