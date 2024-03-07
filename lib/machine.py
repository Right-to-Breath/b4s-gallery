import json
import shlex
import subprocess
import urllib.parse

import env
from lib import storage, thread
from refactor import logger


def get_url_handler(client, header, message):
    breath_hash = message.payload.decode("utf-8", "ignore")
    u_state = storage.state(env.STATE_PATH)
    if breath_hash in u_state:
        params = urllib.parse.urlencode({
            "cid": env.COLLECTION,
            "tid": u_state['id'],
        })
    else:
        params = urllib.parse.urlencode({
            "cid": env.COLLECTION,
            "tid": -1,
        })
    url = f"https://{env.DOMAIN}/?%s" % params
    response = {
        "hash": breath_hash,
        "url": url
    }
    _reason_code, mid = client.publish(env.TOPICS['url'], json.dumps(response))
    if not _reason_code == 0:
        msg = f"[E]{header} Failed to send NFT URL on topic {env.TOPICS['url']}"
        log_error(client, msg)


def handle_file_transfer(__scp_cb, message):
    req_dict: dict = json.loads(message.payload.decode("utf-8", "ignore"))
    cmd_str = env.SCP_CMD.format(env.SCP_PATH, req_dict['fp'], req_dict['rfp'])
    scp_cmds = shlex.split(cmd_str)
    logger.debug(scp_cmds)
    thread.async_subprocess(cmds=scp_cmds, callback=__scp_cb,
                            cb_kwargs={"rdy_to_sell": req_dict['rdy_to_sell'], "b_hash": req_dict['b_hash']},
                            cwd=env.SCP_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            start_new_session=True)


def log_error(client, msg):
    logger.error(msg)
    client.publish(env.TOPICS['error'], msg)