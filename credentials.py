import os
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('bot_token')
db_url = os.getenv('DATABASE_URL')
# db_url = os.getenv('db_url')
port = os.environ['PORT']
sunset_sv_status_msg_link = "https://discord.com/api/v9/channels/926148025007607908/messages?limit=5"  # server-status
mc_bot_id = 936315743216218203
mc_chief_id = 798587846868860965
mc_deputy_id = 903940304749600768
interviewer_role_id = 922221364620972094
lobby_vc_id = 852877257609052160
management_role_id = 798587846868860960
supervisor_role_id = 903913968979038209
three_stars_role_id = 916694528134635551
two_stars_role_id = 916694480080494603
one_star_role_id = 916694284323938325
rank_up_manager_role_id = 920045877731659829
gang_employee_role_id = 922148468624072736
warn_role_id = 964633298397704202
