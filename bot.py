import json
from re import search

from paho.mqtt.client import Client, MQTTMessage
import logging
from socket import gaierror as GetAddressInfoException

from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.error import BadRequest

from lib import storage
from lib.simulator import json_publisher
from env import TOPICS, MQTT_BROKER, CREDENTIALS, STATE_PATH, ERROR_STORAGE, URL_STORAGE, TELEGRAM_BOT_TOKEN

storage.init(STATE_PATH)
storage.init(ERROR_STORAGE, {})
storage.init(URL_STORAGE, {})


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

help_msg2 = "\n\nUse /register_me to receive server error messages or /unregister_me to stop." \
           "\n\nSend me a message with the word `breath` and I will create a beautiful NFT." \
            "\n\nI only understand text and commands for now."

""" connect and configure MQTT """
mqtt_client: Client = Client()
mqtt_client.username_pw_set(*CREDENTIALS)


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    try:
        user = update.effective_user
        update.message.reply_text(f'Hi {user.username}!{help_msg2}')

    except BaseException as err:
        logger.error(f"[E][HELP] Unexpected {err=}, {type(err)=}")


def register_command(update: Update, context: CallbackContext) -> None:
    try:
        error_users = storage.state(ERROR_STORAGE)
        error_users[update.effective_chat.id] = update.effective_user.name
        storage.sync(ERROR_STORAGE, error_users)
        update.message.reply_text('You are now registered for error messages.')

    except BaseException as err:
        logger.error(f"[E][REGISTER] Unexpected {err=}, {type(err)=}")


def unregister_command(update: Update, context: CallbackContext) -> None:
    try:
        error_users = storage.state(ERROR_STORAGE)
        del error_users[update.effective_chat.id]
        storage.sync(ERROR_STORAGE, error_users)
        update.message.reply_text('You are now unregistered.')

    except BaseException as err:
        logger.error(f"[E][UNREGISTER] Unexpected {err=}, {type(err)=}")


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    try:
        if not update.message:
            return
        if search("chat_id", update.message.text):
            update.message.reply_text(update.effective_chat.id)
        elif search("[Bb]reath", update.message.text) or search("[Ss]igh", update.message.text) or \
                search("[Bb]low", update.message.text):
            update.message.reply_text("Breathing into B4S machine.")
            _state = storage.state(STATE_PATH)
            breath_state = json_publisher(client=mqtt_client, state=_state)
            url_users = storage.state(URL_STORAGE)
            url_users[breath_state["data"]["hash"]] = update.message.from_user.id
            storage.sync(URL_STORAGE, url_users)
        else:
            help_command(update, context)

    except BaseException as err:
        logger.error(f"[E][ECHO] Unexpected {err=}, {type(err)=}")


def broadcast(message: str, user_list: list):
    """ Send a message over Telegram """
    try:
        bot: Bot = Bot(TELEGRAM_BOT_TOKEN)
        for _id in user_list:
            bot.send_message(
                chat_id=_id,
                text=message,
                # parse_mode="TEXT",
                disable_web_page_preview=True,
            )
    except BadRequest as e:
        logger.error("❌  Unable to send message to Telgram cause '%s'" % e.message)
    except Exception as e:
        logger.error("❌  Unable to connect to Telegram cause '%s'" % e)


def on_connect(_client: Client, userdata, flags, rc):
    """ subscribe to the topic and notify the user """
    _client.subscribe(TOPICS["error"])
    _client.subscribe(TOPICS["url"])
    # broadcast("🐝  Telegram notifier connected to MQTT.")


def on_message(_client: Client, userdata, msg: MQTTMessage):
    """ Send the received message over Telegram """
    try:
        if msg.topic == TOPICS['error']:
            error_users: dict = storage.state(ERROR_STORAGE)
            broadcast(msg.payload.decode(), user_list=list(error_users.keys()))
        elif msg.topic == TOPICS['url']:
            url_users = storage.state(URL_STORAGE)
            url = json.loads(msg.payload.decode())
            uid = url_users[url['hash']]
            broadcast(url['url'], user_list=[uid])
            del url_users[url['hash']]
            storage.sync(URL_STORAGE, url_users)

    except BaseException as err:
        logger.error(f"[E][MESSAGE_HANDLER] Unexpected {err=}, {type(err)=}")


def main2() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("register_me", register_command))
    dispatcher.add_handler(CommandHandler("unregister_me", unregister_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(*MQTT_BROKER)
        mqtt_client.loop_start()
    except GetAddressInfoException as e:
        logger.error("❌  Unable to connect to MQTT cause '%s'" % e)
    except ValueError as e:
        logger.error("❌  Malformed host cause '%s'" % e)
    except ConnectionRefusedError as e:
        logger.error("❌  MQTT is down cause '%s'" % e)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main2()
