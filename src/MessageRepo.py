import json
import os
from datetime import datetime
from src.Config import Config
from src.Channel import Channel
from src.Spinner import Spinner

class Message(json.JSONEncoder):
    def __init__(self, id: str, timestamp: str, content: str, attachments: str, channel: Channel):
        self.id = id
        self.content = content
        self.attachments = attachments
        self.timestamp = datetime.fromisoformat(timestamp)
        self.channel = channel

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'attachments': self.attachments,
            'timestamp': self.timestamp.isoformat(),
            'channel': self.channel.to_dict() if hasattr(self.channel, 'to_dict') else str(self.channel)
        }
    
    def __repr__(self):
        return f'<Message id={self.id} sent in channel_id={self.channel.id}>'

class MessageRepo:
    def __init__(self, dir_path: str, use_spinner: bool = True):
        if use_spinner:
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
                    message.get("Contents", ""),
                    message.get("Attachments", ""),
                    channel_obj)
                self.messages.append(message_obj)
        if use_spinner:
            spinner.stop("  ")

    def get_messages(self):
        return self.messages.copy()

    def get_n_messages(self):
        return len(self.messages)

    def get_n_channels(self):
        return len(self.channels)

    def __repr__(self):
        return f"<MessageRepo containing {len(self.messages)} messages in {len(self.channels)} channels>"
        
    def __iter__(self):
        return iter(self.get_messages())

__all__ = ['MessageRepo', 'Message']
