import queue


event_queues: list[queue.Queue[str]] = []


def notify_new_plate(case_id: int) -> None:
    message = f'data: {{"case_id": {case_id}}}\n\n'
    for event_queue in event_queues.copy():
        try:
            event_queue.put_nowait(message)
        except queue.Full:
            continue
