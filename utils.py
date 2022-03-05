import json

import requests


def retrieve_sv_status():
    headers = {
        'authority': "discord.com",
        'method': "GET",
        'path': "/api/v9/channels/926148025007607908/messages?limit=50",
        'scheme': "https",
        'authorization': "mfa.uTxRIKBLTScMJ183dWXsCg-JA5GV9Qdm35CXgbkKv3xvRrYeomBxOLvCZKMgaqBUegkXtjMt4Qp10-KU8g4f",
        'cookie': "_ga=GA1.2.2095365897.1634910912; __cfruid=fbc585948201ce526bfcdd166cc5f31d2fdbfe6d-1642310946; __dcfduid=7ffebd607d6611ec8f37856f79e7e15b; __sdcfduid=7ffebd617d6611ec8f37856f79e7e15b0776b13c1e95eeaafb22984f46937358b4e58082fa2c869524518ba37da8ffa9; __utmc=192184383; __utmz=192184383.1645108295.17.12.utmcsr=docs.fivem.net|utmccn=(referral)|utmcmd=referral|utmcct=/; locale=en-US; OptanonConsent=isIABGlobal=false&datestamp=Wed+Mar+02+2022+05%3A48%3A53+GMT%2B0330+(Iran+Standard+Time)&version=6.17.0&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0&AwaitingReconsent=false; __utma=192184383.2095365897.1634910912.1646182779.1646213587.22; __utmb=192184383.2.9.1646214066307",
        'referer': "https://discord.com/channels/747051409400397894/747051409844862991",
        'x-super-properties': "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzk4LjAuNDc1OC4xMDIgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6Ijk4LjAuNDc1OC4xMDIiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiaHR0cHM6Ly9kaXNjb3JkLmNvbS8iLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiJkaXNjb3JkLmNvbSIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjExNjk2MSwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0="
    }
    reg = requests.get("https://discord.com/api/v9/channels/926148025007607908/messages?limit=50", headers=headers)
    json_res = json.loads(reg.text)
    message = json_res[0]
    return message['embeds'][0]


