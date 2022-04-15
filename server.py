"""
Breath for sale
===============
## Goal
MQTT Consumer for breath messages

## Concerns
- Receive breath data with fail-safe and retry
- Send NFT urls for existing NFTs and NFTs that were just minted
- Maintain in-memory and store in disk the state for each breath.
TODO: MongoDB connection
"""
import os
import json
import shlex
import subprocess
import urllib.parse

import paho.mqtt.client as mqtt

from lib import storage, thread

BANNER = "[CONSUMER]"
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
    'rola': 'one_dollar_breath/rola',
}

DOMAIN = "art.breath4.sale"
COLLECTION = "PH_8747"

PATH_TO_COLLECTION = f"./collections/{COLLECTION}/"
NODE_PATH = "/Users/paul/.nvm/versions/node/v16.14.2/bin/node"
IG_PATH = "./scripts"
IG_CMD = "{} generate.js -b ../collections/PH_8747/breath/{}.json -w 2000 -h 2000 -p ../collections/PH_8747/images/{}"


def connect_callback(client, userdata, flags, reasonCode):
    """Connection handler"""
    logger = f"{BANNER}[MQTT CLIENT]"
    if not reasonCode:
        print(f"[!]{logger} Connected.")
        client.subscribe(TOPICS['get_url'])
        print(f"[!]{logger}[{TOPICS['get_url']}] Subscribed.")
        client.subscribe(TOPICS['json'])
        print(f"[!]{logger}[{TOPICS['json']}] Subscribed.")
        client.subscribe(TOPICS['rola'])
        print(f"[!]{logger}[{TOPICS['rola']}] Subscribed.")
    else:
        print(f"[E]{logger} Failed to connect.")


def on_message_callback(client, userdata, message):
    """Message handler"""
    logger = f"{BANNER}[MSG HANDLER][{message.topic}]"
    try:
        #
        # GET_URL REQUEST HANDLER
        if message.topic == TOPICS["get_url"]:
            breath_hash = message.payload.decode("utf-8", "ignore")
            _state = storage.state()
            response = __gen_url_response(_state[breath_hash]["data"])
            reason_code, mid = client.publish(TOPICS['url'], json.dumps(response))
            if reason_code == 0:
                _state[breath_hash]["requested"] = True
                storage.sync(_state)
                print(f"[.]{logger} Successfully sent NFT URL on topic {TOPICS['url']}")
            else:
                print(f"[E]{logger} Failed to send NFT URL on topic {TOPICS['url']}")
        #
        # JSON REQUEST HANDLER
        elif message.topic == TOPICS['json']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            print(f"[.]{logger} Received breath {breath['hash']} on topic {TOPICS['json']}")
            _state = storage.state()
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
                _state[breath["hash"]]["nft"] = True
                storage.sync(_state)
                # WRITE JSON FILE WITH BREATH DATA
                thread.async_write_json(fp=f'{PATH_TO_COLLECTION}/breath/{_state["count"]}.json',
                                        data=_state[breath["hash"]],
                                        encoding='utf-8')
                # TODO: Create Metadata file with new traits
                # SEND NFT TO BE GENERATED
                reason_code2, mid = client.publish(TOPICS['rola'], json.dumps(_state[breath["hash"]]))
                if reason_code2 == 0:
                    print(f"[.]{logger} Successfully sent NFT on topic {TOPICS['rola']}")
                else:
                    print(f"[E]{logger} Failed to send NFT on topic {TOPICS['rola']}")
            else:
                print(f"[E]{logger} Failed to send NFT URL on topic {TOPICS['url']}")
        #
        # ROLA REQUEST HANDLER
        elif message.topic == TOPICS['rola']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            cmds = shlex.split(IG_CMD.format(NODE_PATH, breath["id"], breath["id"]))
            thread.async_subprocess(cmds=cmds, callback=__image_gen_cb, cb_kwargs={"b_hash": breath["data"]["hash"]},
                                    cwd=IG_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    start_new_session=True)

    except BaseException as err:
        print(f"[E]{logger} Unexpected {err=}, {type(err)=}")


def __gen_url_response(breath, token_count):
    params = urllib.parse.urlencode({
        "cid": COLLECTION,
        "tid": token_count,
    })
    url = f"https://{DOMAIN}/#?%s" % params
    response = {
        "hash": breath["hash"],
        "url": url
    }
    return response


def __image_gen_cb(image_gen_res, b_hash):
    p_res = json.loads(image_gen_res)
    if p_res["success"]:
        _state = storage.state()
        _state[b_hash]["image"] = True
        storage.sync(_state)
    else:
        print(f"[E] Error processing image and metadata. Error: {p_res['error']}")


if __name__ == '__main__':
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(*CREDENTIALS)
    mqtt_client.on_connect = connect_callback
    mqtt_client.on_message = on_message_callback
    mqtt_client.connect(*MQTT_BROKER)
    mqtt_client.loop_forever()
