from main import EVENT_LOGGING_CHANNEL_ID, EVENT_VOICE_CHANNEL_ID
import os

BOT_TOKEN = os.environ['bot_token']
EVENT_VOICE_CHANNEL_ID = int(os.environ['vc_id'])
EVENT_LOGGING_CHANNEL_ID = int(os.environ['log_id'])
LTLVC_ROLE_ID = int(os.environ['role_id'])
GUILD_ID = int(os.environ['guild_id'])