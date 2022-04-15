import json
import threading
import subprocess


def async_subprocess(cmds, callback=None, cb_kwargs=None, **kwargs):
    """
    Run subprocess in parallel and maintain the state on a callback.
    Builds the subprocess with given Popen args and kwargs
    Builds callback with cb_kwargs
    """
    def builder(_cmds, _callback, _cb_kwargs, _kwargs):
        """
        Builds the subprocess with given Popen args and kwargs
        """
        proc = subprocess.Popen(_cmds, **_kwargs)
        proc.wait()
        if _callback:
            _callback(proc.stdout.read(), **cb_kwargs)
        return

    thread = threading.Thread(target=builder, args=(cmds, callback, cb_kwargs, kwargs))
    thread.start()
    return thread


def async_write_file(fp, data, callback=None, cb_kwargs=None,  **kwargs):
    """
    Run subprocess in parallel and maintain the state on a callback.
    Builds the subprocess with given open args and kwargs
    """
    def builder(_fp, _data, _callback, _cb_kwargs, _kwargs):
        """
        Builds the subprocess with given open args and kwargs
        """
        f = open(_fp, "w", **_kwargs)
        f.write(_data)
        f.close()
        if _callback:
            _callback(**_cb_kwargs)
        return

    thread = threading.Thread(target=builder, args=(fp, data, callback, cb_kwargs, kwargs))
    thread.start()
    return thread


def async_write_json(fp, data, callback=None, cb_kwargs=None, **kwargs):
    """
    Run subprocess in parallel and maintain the state on a callback.
    Builds the subprocess with given open args and kwargs
    """
    def builder(_fp, _data, _callback, _cb_kwargs, _kwargs):
        """
        Builds the subprocess with given open args and kwargs
        """
        json.dump(_data, open(_fp, 'w', **_kwargs))
        if _callback:
            _callback(**_cb_kwargs)
        return

    thread = threading.Thread(target=builder, args=(fp, data, callback, cb_kwargs, kwargs))
    thread.start()
    return thread
