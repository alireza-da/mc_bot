from flask import Flask
from threading import Thread
from credentials import port

app = Flask('')


@app.route('/')
def home():
    return "Bot is alive."


@app.route('/bot_name')
def show_bot_name():
    return "Social Credit Manager"


def run():
    print(f"[INFO]: App is up on port {port}")
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    t1 = Thread(target=run)
    t1.start()
