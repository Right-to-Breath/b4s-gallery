import shlex
import subprocess
import urllib.parse
import random
from copy import deepcopy

import env
from lib import storage, thread


def generate_nft_metadata(__breath):
    metadata = deepcopy(env.METADATA_FILE)
    metadata['name'] = metadata['name'].format(__breath["id"])
    metadata['image'] = metadata['image'].format(env.METADATA_DOMAIN, env.COLLECTION, __breath["id"])
    x = lambda a: 0 if a else 1
    y = lambda b, c: (abs(b) / c + 3) / 1000
    AR165213 = metadata['attributes'][0]['value']
    lat = float(__breath["data"]["coord"]["latitude"])
    lon = float(__breath["data"]["coord"]["longitude"])
    metadata['attributes'][0]['value'] = AR165213[x(random.random() < y(lat + lon, 100))]
    GO422134 = metadata['attributes'][1]['value']
    co2 = __breath["data"]["breath"]["CO2"]
    metadata['attributes'][1]['value'] = GO422134[x(random.random() < y(co2, 1000))]
    IW122409 = metadata['attributes'][2]['value']
    temp = __breath["data"]["breath"]["temp"]
    metadata['attributes'][2]['value'] = IW122409[x(random.random() < y(temp, 10))]
    PM040103 = metadata['attributes'][3]['value']
    ethanol = __breath["data"]["breath"]["ethanol"]
    metadata['attributes'][3]['value'] = PM040103[x(random.random() < y(ethanol, 10000))]
    ATP10040 = metadata['attributes'][4]['value']
    humidity = __breath["data"]["breath"]["hum"]
    metadata['attributes'][4]['value'] = ATP10040[x(random.random() < y(humidity, 100))]
    return metadata


def gen_url_response(breath, token_count):
    params = urllib.parse.urlencode({
        "cid": env.COLLECTION,
        "tid": token_count,
    })
    url = f"https://{env.DOMAIN}/?%s" % params
    response = {
        "hash": breath["hash"],
        "url": url
    }
    return response


def handle_nft_sell(__os_sell_cb, message):
    b_hash = message.payload.decode("utf-8", "ignore")
    __state = storage.state(env.STATE_PATH)
    os_cmds = shlex.split(env.OS_CMD.format(env.NODE_PATH, __state[b_hash]["id"]))
    thread.async_subprocess(cmds=os_cmds, callback=__os_sell_cb,
                            cb_kwargs={"b_hash": __state[b_hash]["data"]["hash"]},
                            cwd=env.OS_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            start_new_session=True)