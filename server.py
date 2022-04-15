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
import json
import shlex
import subprocess
import urllib.parse

import paho.mqtt.client as mqtt

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
IG_CMD = "{} generate.js -b ../collections/PH_8747/breath/{}.json -w 3000 -h 3000 -p ../collections/PH_8747/images/{}"

# In memory state tracking existing NFTs that were already minted
state = {}

token_count = 0


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
    global token_count
    try:
        # GET_URL REQUEST HANDLER
        if message.topic == TOPICS["get_url"]:
            breath_hash = message.payload.decode("utf-8", "ignore")
            breath = state[breath_hash]
            response = __gen_url_response(breath["data"])
            reason_code, mid = client.publish(TOPICS['url'], json.dumps(response))
            if reason_code == 0:
                state[breath["data"]["hash"]]["requested"] = True
                print(f"[.]{logger} Successfully sent NFT URL on topic {TOPICS['url']}")
            else:
                print(f"[E]{logger} Failed to send NFT URL on topic {TOPICS['url']}")
        # JSON REQUEST HANDLER
        elif message.topic == TOPICS['json']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            print(f"[.]{logger} Received breath {breath['hash']} on topic {TOPICS['json']}")
            state[breath["hash"]] = {
                "data": breath,
                "sent": True,
                "nft": False,
                "image": False,
                "id": token_count + 1
            }
            response = __gen_url_response(breath)
            reason_code, mid = client.publish(TOPICS['url'], json.dumps(response))
            if reason_code == 0:
                token_count += 1
                state[breath["hash"]]["nft"] = True
                # WRITE JSON FILE WITH BREATH DATA
                with open(f'{PATH_TO_COLLECTION}/breath/{token_count}.json', 'w', encoding='utf-8') as f:
                    json.dump(state[breath["hash"]], f, ensure_ascii=False, indent=4)
                # TODO: Create Metadata file with new traits
                print(f"[.]{logger} Successfully sent NFT URL on topic {TOPICS['url']}")
                # SEND NFT TO BE GENERATED
                reason_code2, mid = client.publish(TOPICS['rola'], json.dumps(state[breath["hash"]]))
                if reason_code2 == 0:
                    print(f"[.]{logger} Successfully sent NFT on topic {TOPICS['rola']}")
                else:
                    print(f"[E]{logger} Failed to send NFT on topic {TOPICS['rola']}")
            else:
                print(f"[E]{logger} Failed to send NFT URL on topic {TOPICS['url']}")
        # ROLA REQUEST HANDLER
        elif message.topic == TOPICS['rola']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            print(breath)
            cmds = shlex.split(IG_CMD.format(NODE_PATH, breath["id"], breath["id"]))
            # TODO: Make it async as it is locking the calls...
            p = subprocess.run(cmds, cwd=IG_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=True)
            print(p.stdout)
            p_res = json.loads(p.stdout)
            if p_res["success"]:
                data = state[breath["data"]["hash"]]
                data["image"] = True
                with open(f'{PATH_TO_COLLECTION}/breath/{breath["id"]}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            else:
                print(f"[E]{logger} Error processing image and metadata. Error: {p_res['error']}")

    except BaseException as err:
        print(f"[E]{logger} Unexpected {err=}, {type(err)=}")


def __gen_url_response(breath):
    global token_count
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


if __name__ == '__main__':
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(*CREDENTIALS)
    mqtt_client.on_connect = connect_callback
    mqtt_client.on_message = on_message_callback
    mqtt_client.connect(*MQTT_BROKER)
    mqtt_client.loop_forever()
