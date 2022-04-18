import os
import pickle


def state(fp: str):
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        _state = pickle.load(open(fp, 'rb'))
        return _state
    else:
        return {}


def sync(fp: str, _state: dict):
    pickle.dump(_state, open(fp, 'wb'))


def init(fp: str, initial_state = None):
    if not os.path.exists(fp):
        dirs, file = os.path.split(fp)
        if len(dirs) > 1 and not os.path.exists(dirs):
            os.makedirs(dirs)
        if initial_state:
            _state = initial_state
            sync(fp, _state)
