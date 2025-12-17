import json
import os
from datetime import datetime
from Config import Config
from Channel import Channel
from Spinner import Spinner


class Message:
    def __init__(self, id: str, timestamp: str, content: str, attachments: str, channel: Channel):
        self.id = id
        self.content = content
        self.attachments = attachments
        self.timestamp = datetime.fromisoformat(timestamp)
        self.channel = channel

class MessageRepo:
    def __init__(self, dir_path: str):
        spinner = Spinner("")
        spinner.start()
        self.messages = []
        self.channels = []
        
        self.origin_path = os.path.realpath(dir_path)
        self.context = json.loads(open(os.path.join(self.origin_path, "index.json"), "r").read())

        for channel in [c for c in os.listdir(self.origin_path) if c != "index.json"]:
            full_path = os.path.join(self.origin_path, channel)
            channel_data = json.loads(open(os.path.join(full_path, "channel.json"), "r").read())
            channel_messages = json.loads(open(os.path.join(full_path, "messages.json"), "r").read())
            channel_obj = Channel(
                channel_data["id"],
                Channel.Type.get_type(channel_data["type"]),
                name=channel_data.get("name", ""),
                recipient=channel_data.get("recipients", ""),
                guild_id=channel_data.get("guild", "")["id"] if channel_data.get("guild") else "")
            self.channels.append(channel_obj)
            for message in channel_messages:
                message_obj = Message(
                    message.get("ID", ""),
                    message.get("Timestamp", ""),
                    message.get("Content", ""),
                    message.get("Attachments", ""),
                    channel_obj)
                self.messages.append(message_obj)
        spinner.stop(str(self))

    def __repr__(self):
        return f"<MessageRepo - Message Repository containing {len(self.messages)} messages in {len(self.channels)} channels>"

__all__ = ['Messagerepo', 'Message']
