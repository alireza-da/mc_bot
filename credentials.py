import os
from dotenv import load_dotenv
load_dotenv()

bot_token = os.getenv('bot_token')
db_url = os.getenv('db_url')
port = os.environ['PORT']
sunset_sv_status_msg_link = "https://discord.com/api/v9/channels/926148025007607908/messages?limit=50" # server-status
mc_bot_id = 936315743216218203
mc_chief_id = 798587846868860965
mc_deputy_id = 903940304749600768
