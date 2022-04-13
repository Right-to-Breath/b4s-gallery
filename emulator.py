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

BANNER = "[SIMULATOR]"

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
        client.subscribe(TOPICS['json'])
        print(f"[!]{logger}[{TOPICS['json']}] Subscribed.")
    else:
        print(f"[E]{logger} Failed to connect.")
        raise Exception("Failed to connect to MQTT server.")


def json_publisher(client, state):
    """Simulates breathMachine breathing in"""
    breath = gen_breath_sample()
    state[breath["hash"]] = {
        "data": breath,
        "sent": False,
        "nft": False,
        "requested": False,
    }
    msg = json.dumps(breath)
    reason_code, mid = client.publish(TOPICS['json'], msg)
    if reason_code == 0:
        state[breath["hash"]]["sent"] = True
        return state[breath["hash"]]
    else:
        raise Exception("Failed to send breath to Server.")


def get_url_publisher(client, state, breath_sample_hash):
    """Simulates breathMachine user requesting url for a certain json"""
    logger = f"{BANNER}[PUBLISHER][{TOPICS['get_url']}]"
    msg = breath_sample_hash
    print(f"[.]{logger} Trying to request URL for breath {breath_sample_hash} on topic {TOPICS['get_url']}")
    reason_code, mid = client.publish(TOPICS['get_url'], msg)
    if reason_code == 0:
        state[breath_sample_hash]["requested"] = True
        print(f"[.]{logger} Successfully sent to topic {TOPICS['get_url']}")
        return state[breath_sample_hash]
    else:
        print(f"[E]{logger} Failed to request URL on topic {TOPICS['get_url']}")
        raise Exception("Failed to retrieve url from Server.")
