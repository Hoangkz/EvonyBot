"""Thread-safe boss sightings and per-device wake-up events, grouped by server."""
import threading
import time


class BossBoard:
    def __init__(self, ttl=120, clock=time.monotonic):
        self._lock = threading.Lock()
        self._bosses = {}
        self._listeners = {}
        self._ttl = ttl
        self._clock = clock

    def register(self, serial, server, event):
        with self._lock:
            self._listeners[serial] = (str(server).strip(), event)

    def unregister(self, serial):
        with self._lock:
            self._listeners.pop(serial, None)

    def publish(self, serial, server, coords):
        server = str(server or "").strip()
        if not server:
            return False
        now = self._clock()
        # Without OCR coordinates, coalesce unidentified sightings briefly.
        key = (server, tuple(coords) if coords is not None else None)
        with self._lock:
            self._bosses = {k: v for k, v in self._bosses.items() if v > now}
            if key in self._bosses:
                return False
            self._bosses[key] = now + (self._ttl if coords is not None else 10)
            for target, (target_server, event) in self._listeners.items():
                if target != serial and target_server == server:
                    event.set()
            return True
