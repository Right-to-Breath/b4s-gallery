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

from lib import storage, thread

BANNER = "[SERVER]"
MQTT_BROKER = 'one-dollar-breath.cloud.shiftr.io', 1883
CREDENTIALS = 'one-dollar-breath', 'public'

"""
json - where the breath json arrives 
url - awaits for the server to reply the NFT url
get_url - request a url by sending the hash of the json
"""
TOPICS = {
    'json': 'one_dollar_breath/json',
    'url': 'one_dollar_breath/url',
    'get_url': 'one_dollar_breath/geturl',
    'image': 'one_dollar_breath/image',
    'error': 'one_dollar_breath/error',
}

DOMAIN = "art.breath4.sale"
COLLECTION = "PH_8747"
DEV = True
if DEV:
    PATH_TO_COLLECTION = f"/Users/jeanpaulruizdepraz/Documents/software/sni/breath_py/collections/{COLLECTION}"
    NODE_PATH = "/Users/paul/.nvm/versions/node/v16.14.2/bin/node"
    IG_PATH = "./scripts/image"
    IG_CMD = "{} generate.js -b {}/breath/{}.json -w 2000 -h 2000 -p {}/images/{}"
else:
    PATH_TO_COLLECTION = f"/home/admin/nft-collection-api/collections/{COLLECTION}"
    NODE_PATH = "/home/admin/.nvm/versions/node/v16.14.2/bin/node"
    IG_PATH = "/home/admin/breath_machine-master/scripts/image"
    IG_CMD = "{} generate.js -b {}/breath/{}.json -w 2000 -h 2000 -p {}/images/{}"

STATE_PATH = "./state.pkl"
storage.init(STATE_PATH, {"count": -1})


METADATA_DOMAIN = 'api.breath4.sale'
METADATA_FILE = {
  "name": "Breath#{}",
  "description": "A right, not a privilege.",
  "image": "https://{}/{}/images/{}.png",
  "attributes": [
    {
      "trait_type": "Warmth",
      "value": "Hot"
    },
    {
      "trait_type": "Alcohol",
      "value": "Inebriated"
    },
    {
      "trait_type": "Co2",
      "value": "Planet killer"
    },
  ]
}
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
    header = f"{BANNER}[{message.topic}]"

    def __image_gen_cb(image_gen_res, b_hash):
        p_res = json.loads(image_gen_res)
        if p_res["success"]:
            __state = storage.state(STATE_PATH)
            __state[b_hash]["image"] = True
            storage.sync(STATE_PATH, __state)
        else:
            client.publish(TOPICS['error'], f"[E]{header} Error processing image and metadata. Error: {p_res['error']}")
    try:
        #
        # GET_URL REQUEST HANDLER
        if message.topic == TOPICS["get_url"]:
            breath_hash = message.payload.decode("utf-8", "ignore")
            u_state = storage.state(STATE_PATH)
            response = __gen_url_response(u_state[breath_hash]["data"], u_state['id'])
            reason_code, mid = client.publish(TOPICS['url'], json.dumps(response))
            if reason_code == 0:
                u_state[breath_hash]["requested"] = True
                storage.sync(STATE_PATH, u_state)
            else:
                client.publish(TOPICS['error'], f"[E]{header} Failed to send NFT URL on topic {TOPICS['url']}")
        #
        # JSON REQUEST HANDLER
        elif message.topic == TOPICS['json']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            _state = storage.state(STATE_PATH)
            _state[breath["hash"]] = {
                "data": breath,
                "sent": True,
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
