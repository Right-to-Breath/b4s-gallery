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

import paho.mqtt.client as mqtt

import env
from lib import storage, thread
from lib.machine import get_url_handler, handle_file_transfer, log_error
from lib.nft import generate_nft_metadata, gen_url_response, handle_nft_sell

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
                logger.debug(scp_res)
                log_error(client, msg)
                return
            p_res = json.loads(parsed_res)
            if not p_res["success"]:
                msg = f"[E]__scp_cb Error copying files to the frontend. Error: {p_res['message']}"
                logger.debug(scp_res)
                log_error(client, msg)
                return
            if rdy_to_sell:
                # Request NFT Sell
                _reason_code, mid = client.publish(env.TOPICS['sell'], b_hash)
                if not _reason_code == 0:
                    msg = f"[E]__scp_cb Failed to send transfer message on topic {env.TOPICS['sell']}"
                    log_error(client, msg)

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
                log_error(client, msg)

        def __os_sell_cb(os_res, b_hash):
            raw_res = os_res.decode('utf-8').split('\n')
            parsed_res = False
            for t in raw_res:
                if "success" in t:
                    parsed_res = t
            if not parsed_res:
                msg = f"[E]__os_sell_cb Error with os_sell script response message."
                logger.debug(os_res)
                log_error(client, msg)
                return
            p_res = json.loads(parsed_res)
            if p_res["success"]:
                __state = storage.state(env.STATE_PATH)
                __state[b_hash]["sold"] = True
                storage.sync(env.STATE_PATH, __state)
            else:
                msg = f"[E]__os_sell_cb Error selling NFT on OpenSea. Error: {p_res['message']}"
                logger.debug(os_res)
                log_error(client, msg)

        def __image_gen_cb(image_gen_res, b_hash):
            raw_res = image_gen_res.decode('utf-8').split('\n')
            parsed_res = False
            for t in raw_res:
                if "success" in t:
                    parsed_res = t
            if not parsed_res:
                msg = f"[E]__image_gen_cb Error with image_gen script response message."
                logger.debug(image_gen_res)
                log_error(client, msg)
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
                log_error(client, msg)
        #
        # GET_URL REQUEST HANDLER
        if message.topic == env.TOPICS["get_url"]:
            get_url_handler(client, header, message)
        #
        # JSON REQUEST HANDLER
        elif message.topic == env.TOPICS['json']:
            handle_breath_json_creation(__file_created_cb, client, header, message)
        #
        # IMAGE REQUEST HANDLER
        elif message.topic == env.TOPICS['image']:
            handle_nft_image_gen(__image_gen_cb, message)
        #
        # SELL REQUEST HANDLER
        elif message.topic == env.TOPICS['sell']:
            handle_nft_sell(__os_sell_cb, message)
        #
        # FILE TRANSFER REQUEST HANDLER
        elif message.topic == env.TOPICS['transfer']:
            handle_file_transfer(__scp_cb, message)

    except Exception as err:
        header = f"{env.BANNER}[{message.topic}]"
        msg = f"[E]{header} Unexpected {err=}, {type(err)=}"
        log_error(client, msg)


def handle_breath_json_creation(__file_created_cb, client, header, message):
    breath = json.loads(message.payload.decode("utf-8", "ignore"))
    _state = storage.state(env.STATE_PATH)
    _state[breath["hash"]] = {
        "data": breath,
        "nft": False,
        "image": False,
        "id": _state["count"] + 1
    }
    response = gen_url_response(breath, _state["count"] + 1)
    _reason_code, mid = client.publish(env.TOPICS['url'], json.dumps(response))
    if not _reason_code == 0:
        msg = f"[E]{header} Failed to send NFT URL on topic {env.TOPICS['url']}"
        log_error(client, msg)
    else:
        _state["count"] += 1
        _state[breath["hash"]]["nft"] = response
        storage.sync(env.STATE_PATH, _state)
        # WRITE JSON FILE WITH BREATH DATA
        thread.async_write_json(fp=f'{env.PATH_TO_COLLECTION}/breath/{_state["count"]}.json',
                                callback=__file_created_cb, cb_kwargs={"rfp": env.REMOTE_BREATH_PATH},
                                data=_state[breath["hash"]], encoding='utf-8')
        # WRITE METADATA FILE
        __breath = _state[breath["hash"]]
        metadata = generate_nft_metadata(__breath)
        thread.async_write_json(fp=f'{env.PATH_TO_COLLECTION}/metadata/{_state["count"]}',
                                callback=__file_created_cb, cb_kwargs={"rfp": env.REMOTE_META_PATH},
                                data=metadata, encoding='utf-8')
        # Request image generation
        _reason_code, mid = client.publish(env.TOPICS['image'], json.dumps(_state[breath["hash"]]))
        if not _reason_code == 0:
            msg = f"[E]{header} Failed to send NFT on topic {env.TOPICS['image']}"
            log_error(client, msg)


def handle_nft_image_gen(__image_gen_cb, message):
    breath = json.loads(message.payload.decode("utf-8", "ignore"))
    cmd_string = env.IG_CMD.format(env.NODE_PATH, env.PATH_TO_COLLECTION, breath["id"],
                                   env.PATH_TO_COLLECTION, breath["id"])
    cmds = shlex.split(cmd_string)
    thread.async_subprocess(cmds=cmds, callback=__image_gen_cb, cb_kwargs={"b_hash": breath["data"]["hash"]},
                            cwd=env.IG_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            start_new_session=True)


if __name__ == '__main__':
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(*env.CREDENTIALS)
    mqtt_client.on_connect = connect_callback
    mqtt_client.on_message = on_message_callback
    mqtt_client.connect(*env.MQTT_BROKER)
    mqtt_client.loop_forever()
