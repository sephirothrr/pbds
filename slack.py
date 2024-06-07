import secrets
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

#def sendMessage(bracket, threadID, message):

def sendRecordConfirmation(bracket, text):
    convs = getConversations()

    for conv in convs:
        print(conv)
        if conv['text'] == bracket:
            replyToMessageInThread(getChannelID("record-confirmation"), conv['ts'], text)

def replyToMessageInThread(channelID, thread_ts, text):
    client = WebClient(secrets.token)

    try:
        client.chat_postMessage(
            channel=channelID,
            text=text,
            thread_ts=thread_ts,
        )
    except SlackApiError as e:
        print(f"Error posting message: {e.response['error']}")


def getConversations():
    client = WebClient(secrets.token)

    message_data = []

    try:
        result = client.conversations_history(channel=getChannelID("record-confirmation"))
        messages = result["messages"]

        # Extract messages and their timestamps
        message_data = [{"text": msg["text"], "ts": msg["ts"]} for msg in messages]
        return message_data
    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
        return message_data


def getChannelID(name):
    channels = getConevrsations()

    for channel in channels:
        if channel['name'] == name:
            return channel['id']

def getConevrsations():
    client = WebClient(secrets.token)

    try:
        result = client.conversations_list()
        channels = result['channels']

        #channels = [channel['name'] for channel in channels]
        return channels
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")
        return []

sendRecordConfirmation("Anacostia", "Test")
