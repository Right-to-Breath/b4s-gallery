import os
import pickle


STATE_PATH = "./storage.pkl"


def state():
    _state = pickle.load(open(STATE_PATH, 'rb'))
    return _state


def sync(_state):
    pickle.dump(_state, open(STATE_PATH, 'wb'))


def __init():
    if not os.path.exists(STATE_PATH):
        dirs, file = os.path.split(STATE_PATH)
        if len(dirs) > 1 and not os.path.exists(dirs):
            os.makedirs(dirs)
        _state = {"count": 0}
        sync(_state)
    state()


__init()
