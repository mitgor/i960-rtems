"""Retry only an explicitly rejected RX begin; retain the identical packet."""
import errno

def send_pending(send, frame):
    if frame is None:
        return None
    try:
        send(1, frame)
    except OSError as exc:
        if exc.errno != errno.EAGAIN:
            raise
        return frame
    return None
