import queue
from typing import List

event_queues: List[queue.Queue] = []


def notify_new_plate(case_id: int) -> None:
    msg = f'data: {{"case_id": {case_id}}}\n\n'
    for q in event_queues:
        try:
            q.put_nowait(msg)
        except queue.Full:
            pass
