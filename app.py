import os
import json
import requests
from flask import Flask, request

from chat_bot import CrmnextChatBot
from storeState import state_mdb
from user_data import UserStateData
from Custompayload import send_message
from skills_api import authenticate_user
import json

user_db = state_mdb()
user_data = UserStateData()
# user_state = user_data.data
app = Flask(__name__)

bot = CrmnextChatBot()

app = Flask(__name__, static_url_path='')


@app.route('/', methods=['POST'])
def fb_webhook():
    """
    To get data from  the user and reponse back
    :return:
    """
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for msg in entry["messaging"]:
                if msg.get("message"):
                        sender_id = msg["sender"]["id"]
                        message_text = msg["message"]["text"]
                        #get last status of the user
                        u_data = get_user_state()
                        print("user_state:" + str(u_data))
                        u_state = ''
                        if sender_id in u_data.keys():
                            u_state = u_data[sender_id]
                            if u_state["user_stage"] == 0:
                                u_state["intent_type"] = ""
                        else:
                            u_state = u_data["0"]

                        #Check to execute skills
                        u_state["user_text"] = authenticate_user(u_state, message_text)
                        res = bot.run_bot(u_state)
                        upd_state(sender_id, res, u_data)
                        send_message(sender_id, res)

    return "ok", 200


@app.route('/', methods=['GET'])
def v():
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Ready to Rock!", 200


def get_user_state():

    return user_db.get_user_state("user_data")[0]

def update_user_data(us):

    return user_db.insert_user_state(us)

def upd_state(id, res, last_state):

    user_state = {"user_data":[{id: {"intent_type": "", "user_text": "", "user_stage": 0, "card_type": ""}}]}
    user_state = user_state["user_data"][0]
    user_state[id]["intent_type"] = res["user_intent"]
    user_state[id]["user_stage"] = res["user_stage"]
    user_state[id]["user_text"] = res["response_text"]
    user_state[id]["card_type"] = res["card_type"]
    print("update_user_data: " + str(user_state))
    if id in last_state.keys():
        last_state[id] = user_state[id]
        update_user_data({"user_data":last_state})
    else:
        last_state.update(user_state)
        print("update data :" + str(last_state))
        update_user_data({"user_data":[last_state]})

if __name__ == '__main__':
    app.run(debug=True)
