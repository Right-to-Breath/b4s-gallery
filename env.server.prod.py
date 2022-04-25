METADATA_FILE = {
  "name": "X {}",
  "description": "A Thousand Breaths. Breathing Collectively for a Right to Breathe",
  "image": "https://{}/{}/images/{}.png",
  "attributes": [
    {
      "trait_type": "AR165213",
      "value": ["In discarding rights altogether", "one discards a symbol too deeply enmeshed",
                "in the psyche of the oppressed", "to lose without trauma and much resistance.",
                "Instead, society must give them away.", "Unlock them from reification by giving them to slaves.",
                "Give them to trees. Give them to cows.", "Give them to history. Give them to rivers and rocks.",
                "Give to all of society's objects and untouchables",
                "the rights of privacy, integrity, and self-assertion;",
                "give them distance and respect.",
                "Flood them with the animating spirit",
                "that rights mythology fires in this country\'s most oppressed psyches",
                "and wash away the shrouds of inanimate-object status",
                "so that we may say not that we own gold but that a luminous golden spirit owns us.",
                "– P. J. Williams"]
    },
    {
      "trait_type": "GO422134",
      "value": ["Animals and minerals", "plants and animals", "and photoautotrophs and chemoheterotrophs",
                "are extimates— each is external to the other",
                "only if the scale of our perception is confine to the skin", "to a set of epidermal enclosures.",
                "But human lungs are constant reminders", "that this separation is imaginary.",
                "Where is the human body", "if it is viewed from with the lung?", "– E. A. Povinelli"]
    },
    {
      "trait_type": "IW122409",
      "value": ["There is, too, a connection between", "the lungs and the weather.",
                "The supposedly transformative properties of", "breathing free air.",
                "That which throws off the mantle of slavery.", "And the transformative properties of",
                "being “free” to breathe fresh air.", "These discourses run through", "freedom narratives habitually.",
                "But who has access to freedom?", "Who can breathe free?", "– C. Sharpe"]
    },
    {
      "trait_type": "PM040103",
      "value": ["To take back value", "is to revalue value", "beyond normativity", "and standard judgment.",
                "More radically", "it is to move beyond", "the reign of judgment itself.", "– B.Massumi"]
    },
    {
      "trait_type": "ATP10040",
      "value": ["God is a Lobster", "or a double pincer", "a double bind.", "– G. Deleuze & F. Guattari"]
    },
  ]
}
"""
json - where the breath json arrives 
url - awaits for the server to reply the NFT url
get_url - request a url by sending the hash of the json
image - requests here are collected by the automation that generates the nft images
error - messages that go to the telegram bot
"""
TOPICS = {
    'json': 'one_dollar_breath/json',
    'url': 'one_dollar_breath/url',
    'get_url': 'one_dollar_breath/geturl',
    'image': 'one_dollar_breath/image',
    'error': 'one_dollar_breath/error',
}
BANNER = "[SERVER]"
MQTT_BROKER = 'one-dollar-breath.cloud.shiftr.io', 1883
CREDENTIALS = 'one-dollar-breath', 'public'
METADATA_DOMAIN = 'api.breath4.sale'
DOMAIN = "art.breath4.sale"
COLLECTION = "PH_8747"
IG_CMD = "{} generate.js -b {}/breath/{}.json -p {}/images/{}"
OS_CMD = "{} auction.js -n {}"
STATE_PATH = "./state.pkl"
# ERROR_STORAGE = "./error_users.pkl"
# URL_STORAGE = "./url_users.pkl"
# TELEGRAM_BOT_TOKEN = "5319524868:AAHf1EsmAlulnf23h_bSWoiXVb7O0YZLt4k"

PATH_TO_COLLECTION = f"/home/admin/nft-collection-api/collections/{COLLECTION}"
NODE_PATH = "/home/admin/.nvm/versions/node/v16.14.2/bin/node --no-warnings"
IG_PATH = "/home/admin/breath_machine-master/scripts/image"
OS_PATH = "/home/admin/breath_machine-master/scripts/opensea"
