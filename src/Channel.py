from enum import Enum
from json import JSONEncoder
from datetime import datetime
from src.Config import Config

class Channel:
    class Type(Enum):
        DM = 1
        GUILD = 2
        GROUP_DM = 3
        UNKNOWN = 99

        @staticmethod
        def get_type(string: str) -> 'Channel.Type | None':
            return {"DM": Channel.Type.DM, "GUILD_TEXT": Channel.Type.GUILD, "PUBLIC_THREAD": Channel.Type.GUILD, "GROUP_DM": Channel.Type.GROUP_DM}.get(string)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'recipients': self.recipients,
            'guild_id': self.guild_id
        }

    def __init__(self, id: str, type: 'Channel.Type', name: str = "", recipient: list[str] = [], guild_id: str = ""):
        self.type = type
        self.id = id
        
        self.name = name
        self.recipients = []
        self.guild_id = ""

        if type == Channel.Type.DM:
            if not recipient:
                print(f"Channel id: {id}")
                raise ValueError
            self.recipients = [r for r in recipient if r != Config.USER_ID]
        elif type == Channel.Type.GROUP_DM:
            self.recipients = [r for r in recipient if r != Config.USER_ID]
            self.name = name
        elif type == Channel.Type.GUILD:
            self.name = name
            self.guild_id = guild_id

__all__ = ['Channel']
