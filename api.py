import json
import traceback

import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from emulator import CREDENTIALS, MQTT_BROKER, TOPICS, connect_callback, json_publisher, get_url_publisher


# In memory state tracking existing NFTs that were already minted
state = {}


# Initialize FastAPI
breath_test = FastAPI()


@breath_test.get("/PH_8747/{item_id}")
async def get_collection_item(item_id: str):
    global state
    if item_id not in state.keys():
        raise HTTPException(status_code=404, detail="Item not found.")
    try:
        breath_state = get_url_publisher(client=mqtt_client, state=state, breath_sample_hash=item_id)
        state[item_id] = breath_state
        return {"data": breath_state}
    except Exception as err:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error {}".format(err))


@breath_test.post("/PH_8747")
async def put_new_collection_item():
    global state
    breath_state = json_publisher(client=mqtt_client, state=state)
    try:
        state[breath_state["data"]["hash"]] = breath_state
        return {"data": breath_state}
    except Exception as err:
        raise HTTPException(status_code=500, detail="Error {}".format(err))


def on_message_callback(client, userdata, message):
    """Message handler"""
    try:
        print(message.topic)
        global state
        # JSON REQUEST HANDLER
        if message.topic == TOPICS['json']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            state[breath["hash"]] = {
                "data": breath,
                "sent": True,
                "nft": False,
                "requested": False,
            }
            print(f"[!][MQTT HANDLER] {breath['hash']}")
    except BaseException as err:
        print(f"[E][MQTT HANDLER] Unexpected {err=}, {type(err)=}")


# Initialize MQTT
print('Connecting to MQTT broker {}:{}.'.format(*MQTT_BROKER), flush=True)
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(*CREDENTIALS)
mqtt_client.on_connect = connect_callback
mqtt_client.on_message = on_message_callback
mqtt_client.connect(*MQTT_BROKER)
mqtt_client.loop_start()