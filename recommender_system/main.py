from dag_processor import graph, run_dag
import threading
from queue_consumer import interaction_queue, queue_consumer


def run_system():
    # Start queue consumer in a background thread
    consumer_thread = threading.Thread(target=queue_consumer, daemon=True)
    consumer_thread.start()

    # Run the DAG parallel executor
    run_dag(graph)

    # Optionally wait for queue to empty before finishing
    interaction_queue.join()


run_system()
