import os
from dotenv import load_dotenv
load_dotenv()

bot_token = os.getenv('bot_token')
port = os.environ['PORT']
sunset_sv_status_msg_link = "https://discord.com/api/v9/channels/926148025007607908/messages?limit=50" # server-status
