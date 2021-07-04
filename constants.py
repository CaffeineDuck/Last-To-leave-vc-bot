import os

import dotenv

dotenv.load_dotenv()

BOT_PREFIX = os.environ["BOT_PREFIX"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
EVENT_VOICE_CHANNEL_ID = int(os.environ["VC_ID"])
EVENT_LOGGING_CHANNEL_ID = int(os.environ["LOG_ID"])
LTLVC_ROLE_ID = int(os.environ["ROLE_ID"])
GUILD_ID = int(os.environ["GUILD_ID"])
GENERAL_ID=int(os.environ["GENERAL_ID"])
