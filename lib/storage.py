import os
import pickle


def state(fp: str):
    if os.path.getsize(fp) > 0:
        _state = pickle.load(open(fp, 'rb'))
        return _state
    else:
        return {}


def sync(fp: str, _state: dict):
    pickle.dump(_state, open(fp, 'wb'))


def init(fp: str):
    if not os.path.exists(fp):
        dirs, file = os.path.split(fp)
        if len(dirs) > 1 and not os.path.exists(dirs):
            os.makedirs(dirs)
        _state = {"count": 0}
        sync(fp, _state)
    state(fp)
