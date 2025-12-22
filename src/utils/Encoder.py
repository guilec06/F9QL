from json import JSONEncoder
from src.MessageRepo import MessageRepo, Message
from src.Channel import Channel
from enum import Enum
from datetime import datetime

class QuickloadEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
            
        if isinstance(obj, datetime):
            return obj.isoformat()
            
        if isinstance(obj, Enum):
            return obj.name

        if hasattr(obj, '__dict__'):
            return obj.__dict__

        return super().default(obj)
