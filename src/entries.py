import threading

# Global state dictionary
state = {}

# Lock for thread safety
_lock = threading.Lock()


def set_entry(key, value):
    with _lock:
        state[key] = value


def get_entry(key):
    with _lock:
        return state.get(key)
