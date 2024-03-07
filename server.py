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
import random

import paho.mqtt.client as mqtt

import env
from lib import storage, thread

storage.init(env.STATE_PATH, {"count": -1})

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=env.LOG_LEVEL
)

logger = logging.getLogger(__name__)


def connect_callback(client, userdata, flags, reasonCode):
    """Connection handler"""
    header = f"{env.BANNER}[MQTT CLIENT]"
    if not reasonCode:
        client.subscribe(env.TOPICS['get_url'])
        client.subscribe(env.TOPICS['json'])
        client.subscribe(env.TOPICS['image'])
        client.subscribe(env.TOPICS['sell'])
        client.subscribe(env.TOPICS['transfer'])
    else:
        logger.error(f"[E]{header} Failed to connect.")


def on_message_callback(client, userdata, message):
    """Message handler"""
    try:
        header = f"{env.BANNER}[{message.topic}]"

        def __scp_cb(scp_res, rdy_to_sell, b_hash):
            raw_res = scp_res.decode('utf-8').split('\n')
            parsed_res = False
            for t in raw_res:
                if "success" in t:
                    parsed_res = t
            if not parsed_res:
                msg = f"[E]__scp_cb Error with scp script response message."
                logger.debug(msg)
                logger.debug(scp_res)
                client.publish(env.TOPICS['error'], msg)
                return
            p_res = json.loads(parsed_res)
            if not p_res["success"]:
                msg = f"[E]__scp_cb Error copying files to the frontend. Error: {p_res['message']}"
                logger.debug(scp_res)
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)
                return
            if rdy_to_sell:
                # Request NFT Sell
                _reason_code, mid = client.publish(env.TOPICS['sell'], b_hash)
                if not _reason_code == 0:
                    msg = f"[E]__scp_cb Failed to send transfer message on topic {env.TOPICS['sell']}"
                    logger.debug(scp_res)
                    logger.debug(msg)
                    client.publish(env.TOPICS['error'], msg)

        def __file_created_cb(fp, rfp, rdy_to_sell=False, b_hash="0x"):
            transfer_msg = {
                "fp": fp,
                "rfp": rfp,
                "rdy_to_sell": rdy_to_sell,
                "b_hash": b_hash
            }
            _reason_code, mid = client.publish(env.TOPICS['transfer'], json.dumps(transfer_msg))
            if not _reason_code == 0:
                msg = f"[E]__file_created_cb Failed to send transfer message on topic {env.TOPICS['transfer']}"
                logger.debug(fp, rfp, rdy_to_sell, b_hash)
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)

        def __os_sell_cb(os_res, b_hash):
            raw_res = os_res.decode('utf-8').split('\n')
            parsed_res = False
            for t in raw_res:
                if "success" in t:
                    parsed_res = t
            if not parsed_res:
                msg = f"[E]__os_sell_cb Error with os_sell script response message."
                logger.debug(os_res)
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)
                return
            p_res = json.loads(parsed_res)
            if p_res["success"]:
                __state = storage.state(env.STATE_PATH)
                __state[b_hash]["sold"] = True
                storage.sync(env.STATE_PATH, __state)
            else:
                msg = f"[E]__os_sell_cb Error selling NFT on OpenSea. Error: {p_res['message']}"
                logger.debug(os_res)
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)

        def __image_gen_cb(image_gen_res, b_hash):
            raw_res = image_gen_res.decode('utf-8').split('\n')
            parsed_res = False
            for t in raw_res:
                if "success" in t:
                    parsed_res = t
            if not parsed_res:
                msg = f"[E]__image_gen_cb Error with image_gen script response message."
                logger.debug(image_gen_res)
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)
                return
            p_res = json.loads(parsed_res)
            if p_res["success"]:
                __state = storage.state(env.STATE_PATH)
                __state[b_hash]["image"] = True
                storage.sync(env.STATE_PATH, __state)
                # Request image file transfer to frontend server
                fp = env.PATH_TO_COLLECTION + '/images/' + str(__state[b_hash]["id"]) + '.png'
                __file_created_cb(fp=fp, rfp=env.REMOTE_IMAGE_PATH, rdy_to_sell=True, b_hash=b_hash)
            else:
                msg = f"[E]__image_gen_cb Error processing image and metadata. Error: {p_res['error']}"
                logger.debug(image_gen_res, b_hash)
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)

        #
        # GET_URL REQUEST HANDLER
        if message.topic == env.TOPICS["get_url"]:
            breath_hash = message.payload.decode("utf-8", "ignore")
            u_state = storage.state(env.STATE_PATH)
            # TODO: fix in machine
            if f"0x{breath_hash}" in u_state.keys():
                __breath = u_state[f"0x{breath_hash}"]
                params = urllib.parse.urlencode({
                    "cid": env.COLLECTION,
                    "tid": __breath['id'],
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
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)

        #
        # JSON REQUEST HANDLER
        elif message.topic == env.TOPICS['json']:
            breath: dict = json.loads(message.payload.decode("utf-8", "ignore"))
            # Parse strings to numbers
            # TODO: Fix in the machine and in the bot
            breath["coord"]["latitude"] = float(breath["coord"]["latitude"])
            breath["coord"]["longitude"] = float(breath["coord"]["longitude"])
            for v in ["ref1", "breath"]:
                breath[v]["CO2"] = int(breath[v]["CO2"])
                breath[v]["eCO2"] = int(breath[v]["eCO2"])
                breath[v]["tvoc"] = int(breath[v]["tvoc"])
                breath[v]["h2"] = int(breath[v]["h2"])
                breath[v]["ethanol"] = int(breath[v]["ethanol"])
                breath[v]["temp"] = float(breath[v]["temp"])
                breath[v]["hum"] = float(breath[v]["hum"])
            #
            _state = storage.state(env.STATE_PATH)
            _state[breath["hash"]] = {
                "data": breath,
                "nft": False,
                "image": False,
                "id": _state["count"] + 1
            }
            response = __gen_url_response(breath, _state["count"] + 1)
            _reason_code, mid = client.publish(env.TOPICS['url'], json.dumps(response))
            if not _reason_code == 0:
                msg = f"[E]{header} Failed to send NFT URL on topic {env.TOPICS['url']}"
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)
                return
            _state["count"] += 1
            _state[breath["hash"]]["nft"] = response
            storage.sync(env.STATE_PATH, _state)
            # WRITE JSON FILE WITH BREATH DATA
            thread.async_write_json(fp=f'{env.PATH_TO_COLLECTION}/breath/{_state["count"]}.json',
                                    callback=__file_created_cb, cb_kwargs={"rfp": env.REMOTE_BREATH_PATH},
                                    data=_state[breath["hash"]], encoding='utf-8')
            # WRITE METADATA FILE
            metadata = deepcopy(env.METADATA_FILE)
            metadata['name'] = metadata['name'].format(_state["count"])
            metadata['image'] = metadata['image'].format(env.METADATA_DOMAIN, env.COLLECTION, _state["count"])
            __breath = _state[breath["hash"]]
            lat = __breath["data"]["coord"]["latitude"]
            lon = __breath["data"]["coord"]["longitude"]
            co2 = __breath["data"]["breath"]["CO2"]
            temp = __breath["data"]["breath"]["temp"]
            ethanol = __breath["data"]["breath"]["ethanol"]
            humidity = __breath["data"]["breath"]["hum"]
            AR165213 = metadata['attributes'][0]['value']
            GO422134 = metadata['attributes'][1]['value']
            IW122409 = metadata['attributes'][2]['value']
            PM040103 = metadata['attributes'][3]['value']
            ATP10040 = metadata['attributes'][4]['value']
            x = lambda a: 0 if a else 1
            y = lambda b, c: (abs(b)/c + 3) / 100
            metadata['attributes'][0]['value'] = AR165213[x(random.random() < y(lat + lon, 100))]
            metadata['attributes'][1]['value'] = GO422134[x(random.random() < y(co2, 1000))]
            metadata['attributes'][2]['value'] = IW122409[x(random.random() < y(temp, 10))]
            metadata['attributes'][3]['value'] = PM040103[x(random.random() < y(ethanol, 10000))]
            metadata['attributes'][4]['value'] = ATP10040[x(random.random() < y(humidity, 100))]
            thread.async_write_json(fp=f'{env.PATH_TO_COLLECTION}/metadata/{_state["count"]}',
                                    callback=__file_created_cb, cb_kwargs={"rfp": env.REMOTE_META_PATH},
                                    data=metadata, encoding='utf-8')
            # Request image generation
            _reason_code, mid = client.publish(env.TOPICS['image'], json.dumps(_state[breath["hash"]]))
            if not _reason_code == 0:
                msg = f"[E]{header} Failed to send NFT on topic {env.TOPICS['image']}"
                logger.debug(msg)
                client.publish(env.TOPICS['error'], msg)

        #
        # IMAGE REQUEST HANDLER
        elif message.topic == env.TOPICS['image']:
            breath = json.loads(message.payload.decode("utf-8", "ignore"))
            cmd_string = env.IG_CMD.format(env.NODE_PATH, env.PATH_TO_COLLECTION, breath["id"],
                                                 env.PATH_TO_COLLECTION, breath["id"])
            cmds = shlex.split(cmd_string)
            thread.async_subprocess(cmds=cmds, callback=__image_gen_cb, cb_kwargs={"b_hash": breath["data"]["hash"]},
                                    cwd=env.IG_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    start_new_session=True)

        #
        # SELL REQUEST HANDLER
        elif message.topic == env.TOPICS['sell']:
            b_hash = message.payload.decode("utf-8", "ignore")
            __state = storage.state(env.STATE_PATH)
            os_cmds = shlex.split(env.OS_CMD.format(env.NODE_PATH, __state[b_hash]["id"]))
            thread.async_subprocess(cmds=os_cmds, callback=__os_sell_cb,
                                    cb_kwargs={"b_hash": __state[b_hash]["data"]["hash"]},
                                    cwd=env.OS_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    start_new_session=True)

        #
        # FILE TRANSFER REQUEST HANDLER
        elif message.topic == env.TOPICS['transfer']:
            request = json.loads(message.payload.decode("utf-8", "ignore"))
            cmd_str = env.SCP_CMD.format(env.SCP_PATH, request['fp'], request['rfp'])
            scp_cmds = shlex.split(cmd_str)
            thread.async_subprocess(cmds=scp_cmds, callback=__scp_cb,
                                    cb_kwargs={"rdy_to_sell": request['rdy_to_sell'], "b_hash":  request['b_hash']},
                                    cwd=env.SCP_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    start_new_session=True)

    except Exception as err:
        header = f"{env.BANNER}[{message.topic}]"
        msg = f"[E]{header} Unexpected {err=}, {type(err)=}"
        logger.debug(msg)
        client.publish(env.TOPICS['error'], msg)


def __gen_url_response(breath, token_count):
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


if __name__ == '__main__':
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(*env.CREDENTIALS)
    mqtt_client.on_connect = connect_callback
    mqtt_client.on_message = on_message_callback
    mqtt_client.connect(*env.MQTT_BROKER)
    mqtt_client.loop_forever()
