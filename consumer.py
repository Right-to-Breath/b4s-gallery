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
import os.path
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
}

# In memory state tracking existing NFTs that were already minted
STATE = {}

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
            breath = STATE[breath_hash]
            response = gen_url_response(breath["data"])
            reasonCode, mid = client.publish(TOPICS['url'], json.dumps(response))
            if reasonCode == 0:
                STATE[breath["data"]["hash"]]["requested"] = True
                print(f"[.]{logger} Successfully sent NFT URL on topic {TOPICS['url']}")
            else:
                print(f"[E]{logger} Failed to send NFT URL on topic {TOPICS['url']}")


        # JSON REQUEST HANDLER
        elif message.topic == TOPICS['json']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            print(f"[.]{logger} Received breath {breath['hash']} on topic {TOPICS['json']}")
            STATE[breath["hash"]] = {
                "data": breath,
                "sent": True,
                "nft": False,
                "requested": False,
            }
            response = gen_url_response(breath)
            reasonCode, mid = client.publish(TOPICS['url'], json.dumps(response))
            if reasonCode == 0:
                token_count += 1
                STATE[breath["hash"]]["nft"] = True
                print(f"[.]{logger} Successfully sent NFT URL on topic {TOPICS['url']}")
            else:
                print(f"[E]{logger} Failed to send NFT URL on topic {TOPICS['url']}")

    except BaseException as err:
        print(f"[E]{logger} Unexpected {err=}, {type(err)=}")


def gen_url_response(breath):
    global token_count
    params = urllib.parse.urlencode({
        "hs": breath["hash"],
        "dt": breath["date_t"],
        "ln": breath["lon"],
        "lt": breath["lat"],
        "co": breath["ref1"]["CO2"],
        "ec": breath["ref1"]["eCO2"],
        "tv": breath["ref1"]["tvoc"],
        "et": breath["ref1"]["ethanol"],
        "h2": breath["ref1"]["h2"],
        "tp": breath["ref1"]["temp"],
        "hm": breath["ref1"]["hum"],
        "id": token_count,
    })
    url = "https://breath4sale.com/nft#?%s" % params
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
