import my_secrets
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

#def sendMessage(bracket, threadID, message):

domain = 'https://pbds-39c532296638.herokuapp.com/'

def getToken():
    return os.getenv('SLACK_TOKEN', my_secrets.token)

class SlackClient:
    def __init__(self, channel, token):
        self.client = WebClient(token)
        self.channel = ""
        channels = self.client.conversations_list()["channels"]
        for c in channels:
            if c['name'] == channel:
                self.channel = c['id']
                break

    def sendRecordConfirmation(self, bracket, text):
        convs = self.getMessages()
        for conv in convs:
            print(conv)
            if conv['text'] == bracket:
                self.replyToMessageInThread(self.channel, conv['ts'], text)

    def replyToMessageInThread(self, channelID, thread_ts, text):
        try:
            self.client.chat_postMessage(
                channel=channelID,
                text=text,
                thread_ts=thread_ts,
            )
        except SlackApiError as e:
            print(f"Error posting message: {e.response['error']}")


    def getMessages(self):
        message_data = []

        try:
            result = self.client.conversations_history(channel=self.channel)
            messages = result["messages"]

            # Extract messages and their timestamps
            message_data = [{"text": msg["text"], "ts": msg["ts"]} for msg in messages]
            return message_data
        except SlackApiError as e:
            print(f"Error fetching messages: {e.response['error']}")
            return message_data



    def sendBrackets(self, brackets):
        for bracket in brackets:
            try:
                self.client.chat_postMessage(
                    channel=self.channel,
                    text=bracket
                )
            except SlackApiError as e:
                print(f"Error posting message: {e.response['error']}")
                return None


