"""
Breath for sale
===============
## Goal
MQTT Consumer for breath messages

## Concerns
- Receive breath data with fail-safe and retry
- Send NFT urls for existing NFTs and NFTs that were just minted
- Maintain in-memory and store in disk the state for each breath.
"""
import json
import logging
import shlex
import subprocess
import urllib.parse
from copy import deepcopy

import paho.mqtt.client as mqtt

from env import METADATA_FILE, TOPICS, BANNER, MQTT_BROKER, CREDENTIALS, METADATA_DOMAIN, DOMAIN, COLLECTION, \
    PATH_TO_COLLECTION, NODE_PATH, IG_PATH, OS_PATH, IG_CMD, OS_CMD, STATE_PATH
from lib import storage, thread

storage.init(STATE_PATH, {"count": -1})

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def connect_callback(client, userdata, flags, reasonCode):
    """Connection handler"""
    header = f"{BANNER}[MQTT CLIENT]"
    if not reasonCode:
        client.subscribe(TOPICS['get_url'])
        client.subscribe(TOPICS['json'])
        client.subscribe(TOPICS['image'])
    else:
        logger.error(f"[E]{header} Failed to connect.")


def on_message_callback(client, userdata, message):
    """Message handler"""
    try:
        header = f"{BANNER}[{message.topic}]"

        def __os_sell_cb(os_res, b_hash):
            json_res = os_res.decode('utf-8').split('\n')[-2]
            p_res = json.loads(json_res)
            if p_res["success"]:
                __state = storage.state(STATE_PATH)
                __state[b_hash]["sold"] = True
                storage.sync(STATE_PATH, __state)
            else:
                client.publish(TOPICS['error'], f"[E] Error selling NFT on OpenSea. Error: {p_res['message']}")

        def __image_gen_cb(image_gen_res, b_hash):
            p_res = json.loads(image_gen_res)
            if p_res["success"]:
                __state = storage.state(STATE_PATH)
                __state[b_hash]["image"] = True
                storage.sync(STATE_PATH, __state)
                os_cmds = shlex.split(OS_CMD.format(NODE_PATH, breath["id"]))
                thread.async_subprocess(cmds=os_cmds, callback=__os_sell_cb,
                                        cb_kwargs={"b_hash": breath["data"]["hash"]},
                                        cwd=OS_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        start_new_session=True)
            else:
                client.publish(TOPICS['error'], f"[E] Error processing image and metadata. Error: {p_res['error']}")
        #
        # GET_URL REQUEST HANDLER
        if message.topic == TOPICS["get_url"]:
            breath_hash = message.payload.decode("utf-8", "ignore")
            u_state = storage.state(STATE_PATH)
            if breath_hash in u_state:
                params = urllib.parse.urlencode({
                    "cid": COLLECTION,
                    "tid": u_state['id'],
                })
            else:
                params = urllib.parse.urlencode({
                    "cid": COLLECTION,
                    "tid": -1,
                })
            url = f"https://{DOMAIN}/?%s" % params
            response = {
                "hash": breath_hash,
                "url": url
            }
            reason_code, mid = client.publish(TOPICS['url'], json.dumps(response))
            if not reason_code == 0:
                client.publish(TOPICS['error'], f"[E]{header} Failed to send NFT URL on topic {TOPICS['url']}")
        #
        # JSON REQUEST HANDLER
        elif message.topic == TOPICS['json']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            _state = storage.state(STATE_PATH)
            _state[breath["hash"]] = {
                "data": breath,
                "nft": False,
                "image": False,
                "id": _state["count"] + 1
            }
            response = __gen_url_response(breath, _state["count"] + 1)
            reason_code, mid = client.publish(TOPICS['url'], json.dumps(response))
            if reason_code == 0:
                _state["count"] += 1
                _state[breath["hash"]]["nft"] = response
                storage.sync(STATE_PATH, _state)
                # WRITE JSON FILE WITH BREATH DATA
                thread.async_write_json(fp=f'{PATH_TO_COLLECTION}/breath/{_state["count"]}.json',
                                        data=_state[breath["hash"]], encoding='utf-8')
                # WRITE METADATA FILE
                metadata = deepcopy(METADATA_FILE)
                metadata['name'] = metadata['name'].format(_state["count"])
                metadata['image'] = metadata['image'].format(METADATA_DOMAIN, COLLECTION, _state["count"])
                __breath = _state[breath["hash"]]
                AR165213 = metadata['attributes'][0]['value']
                lat = int(__breath["data"]["coord"]["latitude"])
                lon = int(__breath["data"]["coord"]["longitude"])
                metadata['attributes'][0]['value'] = AR165213[abs(lat+lon) % len(AR165213)]
                GO422134 = metadata['attributes'][1]['value']
                co2 = int(__breath["data"]["breath"]["CO2"])
                metadata['attributes'][1]['value'] = GO422134[co2 % len(GO422134)]
                IW122409 = metadata['attributes'][2]['value']
                temp = __breath["data"]["breath"]["temp"]
                metadata['attributes'][2]['value'] = IW122409[abs(int(temp)) % len(IW122409)]
                PM040103 = metadata['attributes'][3]['value']
                ethanol = __breath["data"]["breath"]["ethanol"]
                metadata['attributes'][3]['value'] = PM040103[abs(int(ethanol)) % len(PM040103)]
                ATP10040 = metadata['attributes'][4]['value']
                humidity = __breath["data"]["breath"]["hum"]
                metadata['attributes'][4]['value'] = ATP10040[abs(int(humidity)) % len(ATP10040)]
                thread.async_write_json(fp=f'{PATH_TO_COLLECTION}/metadata/{_state["count"]}',
                                        data=metadata, encoding='utf-8')
                # SEND NFT TO BE GENERATED
                reason_code2, mid = client.publish(TOPICS['image'], json.dumps(_state[breath["hash"]]))
                if not reason_code2 == 0:
                    client.publish(TOPICS['error'], f"[E]{header} Failed to send NFT on topic {TOPICS['image']}")
            else:
                client.publish(TOPICS['error'], f"[E]{header} Failed to send NFT URL on topic {TOPICS['url']}")
        #
        # IMAGE REQUEST HANDLER
        elif message.topic == TOPICS['image']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            cmds = shlex.split(IG_CMD.format(NODE_PATH, PATH_TO_COLLECTION, breath["id"],
                                             PATH_TO_COLLECTION, breath["id"]))
            thread.async_subprocess(cmds=cmds, callback=__image_gen_cb, cb_kwargs={"b_hash": breath["data"]["hash"]},
                                    cwd=IG_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    start_new_session=True)

    except Exception as err:
        client.publish(TOPICS['error'], f"[E]{header} Unexpected {err=}, {type(err)=}")


def __gen_url_response(breath, token_count):
    params = urllib.parse.urlencode({
        "cid": COLLECTION,
        "tid": token_count,
    })
    url = f"https://{DOMAIN}/?%s" % params
    response = {
        "hash": breath["hash"],
        "url": url
    }
    return response


if __name__ == '__main__':
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(*CREDENTIALS)
    mqtt_client.on_connect = connect_callback
    mqtt_client.on_message = on_message_callback
    mqtt_client.connect(*MQTT_BROKER)
    mqtt_client.loop_forever()

