import logging

METADATA_FILE = {
  "name": "X {}",
  "description": "A Thousand Breaths. Breathing Collectively for a Right to Breathe",
  "image": "https://{}/{}/images/{}.png",
  "attributes": [
    {
      "trait_type": "AR165213",
      "value": ["“In discarding rights altogether, one discards a symbol too deeply enmeshed in the psyche of the oppressed to lose without trauma and much resistance. Instead, society must give them away. Unlock them from reification by giving them to slaves. Give them to trees. Give them to cows. Give them to history. Give them to rivers and rocks. Give to all of society's objects and untouchables the rights of privacy, integrity, and self-assertion; give them distance and respect. Flood them with the animating spirit that rights mythology fires in this country's most oppressed psyches, and wash away the shrouds of inanimate-object status, so that we may say not that we own gold but that a luminous golden spirit owns us.” – P. J. Williams", "luminously"]
    },
    {
      "trait_type": "GO422134",
      "value": ["“Animals and minerals, plants and animals, and photoautotrophs and chemoheterotrophs are extimates— each is external to the other only if the scale of our perception is confine to the skin, to a set of epidermal enclosures. But human lungs are constant reminders that this separation is imaginary. Where is the human body if it is viewed from with the lung?” – E. A. Povinelli", "entangled"]
    },
    {
      "trait_type": "IW122409",
      "value": ["“There is, too, a connection between the lungs and the weather: the supposedly transformative properties of breathing free air—that which throws off the mantle of slavery—and the transformative properties of being “free” to breathe fresh air. These discourses run through freedom narratives habitually. But who has access to freedom? Who can breathe free?” – C. Sharpe", "freely"]
    },
    {
      "trait_type": "PM040103",
      "value": ["To take back value is to revalue value, beyond normativity and standard judgment. More radically, it is to move beyond the reign of judgment itself.” – B.Massumi", "ethically"]
    },
    {
      "trait_type": "ATP10040",
      "value": ["“God is a Lobster, or a double pincer, a double bind.” – G. Deleuze & F. Guattari", "bicisively"]
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
    'sell': 'one_dollar_breath/sell',
    'transfer': 'one_dollar_breath/transfer',
    'error': 'one_dollar_breath/error',
}
LOG_LEVEL = logging.INFO
BANNER = "[SERVER]"

MQTT_BROKER = 'one-dollar-breath.cloud.shiftr.io', 1883
CREDENTIALS = 'one-dollar-breath', 'A4P67SGNTPEqjv8Z4gHt'
METADATA_DOMAIN = 'api.breathfor.sale'
DOMAIN = "art.breathfor.sale"
COLLECTION = "PH_8747"
IG_CMD = "{} generate.js -b {}/breath/{}.json -p {}/images/{}"
OS_CMD = "{} auction.js -n {}"
SCP_CMD = "{}/scp.sh {} {}"

PATH_TO_COLLECTION = f"/home/chris/collections/{COLLECTION}"
STATE_PATH = f"{PATH_TO_COLLECTION}/state.pkl"
NODE_PATH = "/home/julius/.nvm/versions/node/v16.14.2/bin/node"
IG_PATH = "/home/chris/b4s/scripts/image"
OS_PATH = "/home/chris/b4s/scripts/opensea"
SCP_PATH = "/home/chris/b4s/scripts"
REMOTE_META_PATH = f"/var/www/api.breathfor.sale/PH_8747/metadata/"
REMOTE_BREATH_PATH = f"/var/www/api.breathfor.sale/PH_8747/breath/"
REMOTE_IMAGE_PATH = f"/var/www/api.breathfor.sale/PH_8747/images/"
