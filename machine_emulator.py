"""
Breath for sale
===============
## Goal
MQTT Publisher that emulates the "BreathMachine"

## Concerns
- Send synthetic breath data to the json topic with fail-safe and retry
- Receive NFT urls for existing NFTs and NFTs that were just minted
- Request NFT urls for existing NFTs
- Maintain in-memory state for each breath.
"""
import json
import random
import time
import zlib

from paho.mqtt import client as mqtt

BANNER = "[MACHINE]"
BREATH_SPAM_SECONDS = 10
URL_SPAM_SECONDS = 5

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
MQTT_TOPIC_URL = 'one_dollar_breath/url'
MQTT_TOPIC_GETURL = 'one_dollar_breath/geturl'

# In memory state tracking existing NFTs that were already minted
state = {}


def gen_breath_sample():
    data_sample = {
        "rfid": random.randbytes(4).hex(),
       "date_t": "2022-27-03T19:26:57",
        "lat": "42.36114",
        "lon": "-71.05708",
       "ref1": {
            # random.normalvariate(mu, sigma)
           "CO2": random.randrange(300, 450), # 400 300-5000
           "eCO2": random.randrange(300, 450), # 400 300-14000
           "tvoc": random.randrange(0, 50), # 0 0-2000
           "ethanol": random.randrange(16100, 17000), # 18666 16000-20000
           "h2": random.randrange(12000, 14000), # 13626 10000-14000
           "temp": float(random.randrange(1700, 2800)/100), # 24 -5.00-50.00
           "hum": float(random.randrange(1700, 2800)/100)}, # 31 20-100
       "breath": {
           "CO2": random.randrange(1200, 5000),  # 400 300-5000
           "eCO2": random.randrange(8000, 14000),  # 400 300-14000
           "tvoc": random.randrange(100, 300),  # 0 0-2000
           "ethanol": random.randrange(17000, 20000),  # 18666 16000-20000
           "h2": random.randrange(11000, 14000),  # 13626 10000-14000
           "temp": float(random.randrange(2400, 3700) / 100),  # 24 -5.00-50.00
           "hum": float(random.randrange(4100, 10000) / 100),  # 31 20-100
       }
    }
    crc32hash = hex(zlib.crc32(json.dumps(data_sample).encode()))
    # crc32hash = reduce(lambda x, y: x ^ y, [hash(item) for item in data_sample.items()])
    # data_sample["hash"] = hex(zlib.crc32(b''data_sample) & 0xffffffff)
    data_sample["hash"] = crc32hash
    return data_sample


def connect_callback(client, userdata, flags, reasonCode):
    """Connection handler"""
    logger = f"{BANNER}[MQTT CLIENT]"
    if not reasonCode:
        print(f"[!]{logger} Connected.")
        client.subscribe(TOPICS['url'])
        print(f"[!]{logger}[{TOPICS['url']}] Subscribed.")
    else:
        print(f"[E]{logger} Failed to connect.")


def json_publisher(client):
    """Simulates breathMachine breathing in"""
    logger = f"{BANNER}[PUBLISHER][{TOPICS['json']}]"
    global state
    try:
        # Retrieves the latest breath generated and checks if it was successful
        if len(STATE.keys()) and (not STATE[list(STATE)[-1]]["sent"] or not STATE[list(STATE)[-1]]["nft"]):
            breath = STATE[list(STATE)[-1]]["data"]
            msg = json.dumps(breath)
            print(f"[!]{logger} Resending previous breath on topic {TOPICS['json']}")
        # Collects a new synthetic breath
        else:
            breath = gen_breath_sample()
            STATE[breath["hash"]] = {
                "data": breath,
                "sent": False,
                "nft": False,
                "requested": False,
            }
            msg = json.dumps(breath)
            print(f"[.]{logger} Trying to send breath {breath['hash']} to topic {TOPICS['json']}")
        reasonCode, mid = client.publish(TOPICS['json'], msg)
        if reasonCode == 0:
            STATE[breath["hash"]]["sent"] = True
            print(f"[.]{logger} Successfully sent breath on topic {TOPICS['json']}")
            return STATE[breath["hash"]]
        else:
            print(f"[E]{logger} Failed to send breath on topic {TOPICS['json']}")
            raise Exception("Failed to post.")

    except BaseException as err:
        print(f"[E]{logger} Unexpected {err=}, {type(err)=}")


def get_url_publisher(client):
    """Simulates breathMachine user requesting url for a certain json"""
    logger = f"{BANNER}[PUBLISHER][{TOPICS['get_url']}]"
    global state
    try:
        # Retrieves the latest breath generated that already has a NFT URL.
        if len(STATE.keys()) and (STATE[list(STATE)[-1]]["sent"] and STATE[list(STATE)[-1]]["nft"] and
                                  not STATE[list(STATE)[-1]]["requested"]):
            breath_sample_hash = STATE[list(STATE)[-1]]["data"]["hash"]
            # msg = json.dumps({"hash": breath_sample_hash})
            msg = breath_sample_hash
            print(f"[.]{logger} Trying to request URL for breath {breath_sample_hash} on topic {TOPICS['get_url']}")
            reasonCode, mid = client.publish(TOPICS['get_url'], msg)
            if reasonCode == 0:
                STATE[breath_sample_hash]["requested"] = True
                print(f"[.]{logger} Successfully sent to topic {TOPICS['get_url']}")
                return STATE[breath_sample_hash]
            else:
                print(f"[E]{logger} Failed to request URL on topic {TOPICS['get_url']}")
                raise Exception("Failed to retrieve")

    except BaseException as err:
        print(f"[E]{logger} Unexpected {err=}, {type(err)=}")


def on_message_callback(client, userdata, message):
    """Message handler"""
    logger = f"{BANNER}[MSG HANDLER][{message.topic}]"
    global state
    try:
        # URL RESPONSE HANDLER
        if message.topic == TOPICS['url']:
            decoded_url_msg = json.loads(message.payload.decode("utf-8", "ignore"))
            print(f"[.]{logger} Successfully processed NFT URL for {decoded_url_msg['hash']}")
            print(f"[.]{logger} NFT URL: {decoded_url_msg['url']}")
            print(f"[.]{logger} Breath data: {STATE[decoded_url_msg['hash']]}")
            STATE[decoded_url_msg["hash"]]["nft"] = True
            if STATE[decoded_url_msg["hash"]]["requested"]:
                # Deletes state to save memory
                del STATE[decoded_url_msg["hash"]]
        else:
            print(f"[!]{logger} No handler for this topic.")

    except BaseException as err:
        print(f"[E]{logger} Unexpected {err=}, {type(err)=}")


if __name__ == '__main__':
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(*CREDENTIALS)
    mqtt_client.on_connect = connect_callback
    mqtt_client.on_message = on_message_callback
    mqtt_client.connect(*MQTT_BROKER)
    mqtt_client.loop_start()
    while True:
        time.sleep(BREATH_SPAM_SECONDS)
        json_publisher(mqtt_client)
        time.sleep(URL_SPAM_SECONDS)
        get_url_publisher(mqtt_client)
