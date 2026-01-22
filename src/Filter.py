from src.MessageRepo import MessageRepo, Message
from src.Channel import Channel
from src.Guild import Guild
from enum import Enum
from typing import Set, Callable
from datetime import datetime, date
import re

# ============================================================================
# HELPER FUNCTIONS FOR TYPE CONVERSION
# ============================================================================

def _parse_datetime(value):
    """Convert string to datetime if needed"""
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value

def _parse_date(value):
    """Convert string or datetime to date if needed"""
    if isinstance(value, str):
        return datetime.fromisoformat(value).date()
    elif isinstance(value, datetime):
        return value.date()
    return value

def _parse_int(value):
    """Convert string to integer if needed"""
    if isinstance(value, str):
        return int(value)
    return value

def _match_regex(message, pattern):
    # Implement cache and pre compiling ?
    return re.search(pattern, message.content) is not None

def _unpack_args(join_symbol, args):
    return f'{join_symbol}'.join(map(str, args))

USER_MENTION_PATTERN = re.compile(r"<@\d{17,20}>")
CHANNEL_MENTION_PATTERN = USER_MENTION_PATTERN

type FilterCallableNoarg = Callable[[], bool]
type FilterCallableSingle = Callable[[Message, str], bool]
type FilterCallableMultiple = Callable[[Message, list[str]], bool]
type FilterAny = FilterCallableNoarg | FilterCallableSingle | FilterCallableMultiple

class FILTERS(Enum):
    AlwaysTrue: FilterCallableNoarg = lambda: True
    SentAfter: FilterCallableSingle = lambda message, timestamp: message.timestamp > _parse_datetime(timestamp)
    SentBefore: FilterCallableSingle = lambda message, timestamp: message.timestamp < _parse_datetime(timestamp)
    SentBetween: FilterCallableMultiple = lambda message, *periods: _parse_datetime(periods[0]) < message.timestamp < _parse_datetime(periods[1])
    ChannelRecipients: FilterCallableMultiple = lambda message, *recipients: all(r in message.channel.recipients for r in recipients)
    MentionsUser: FilterCallableMultiple = lambda message, *users: _match_regex(message, rf"<@({_unpack_args('|', users)})>")
    HasUserMention: FilterCallableNoarg = lambda message: _match_regex(message, USER_MENTION_PATTERN)
    HasUserMentionCountGt: FilterCallableSingle = lambda message, count: len(re.match(USER_MENTION_PATTERN, message.content)) > count
    HasUserMentionCountLt: FilterCallableSingle = lambda message, count: len(re.match(USER_MENTION_PATTERN, message.content)) < count
    HasUserMentionCountEq: FilterCallableSingle = lambda message, count: len(re.match(USER_MENTION_PATTERN, message.content)) == count
    MentionsChannel: FilterCallableMultiple = lambda message, *channels: _match_regex(message, rf"<#{_unpack_args('|', channels)}>")
    HasChannemMentionCountGt: FilterCallableSingle = lambda message, count: len(re.match(CHANNEL_MENTION_PATTERN, message.content)) > count
    HasChannemMentionCountLt: FilterCallableSingle = lambda message, count: len(re.match(CHANNEL_MENTION_PATTERN, message.content)) < count
    HasChannemMentionCountEq: FilterCallableSingle = lambda message, count: len(re.match(CHANNEL_MENTION_PATTERN, message.content)) == count
    HasChannelMention: FilterCallableNoarg = lambda message: _match_regex(message, CHANNEL_MENTION_PATTERN)
    IsDM: FilterCallableNoarg = lambda message: message.channel.type == Channel.Type.DM
    IsGroupDM: FilterCallableNoarg = lambda message: message.channel.type == Channel.Type.GROUP_DM
    IsGuild: FilterCallableNoarg = lambda message: message.channel.type == Channel.Type.GUILD

    MessageContains: FilterCallableMultiple = lambda message, *search: _match_regex(message, _unpack_args('|', search))
    MessageLengthGt: FilterCallableSingle = lambda message, count: len(message.content) > count
    MessageLengthGt: FilterCallableSingle = lambda message, count: len(message.content) < count
    MessageLengthEq: FilterCallableSingle = lambda message, count: len(message.content) == count
    MessageRegex: FilterCallableMultiple = lambda message, *regexes: all(_match_regex(message, regex) for regex in regexes)

    HasAttachments: FilterCallableNoarg = lambda message: len(message.attachments) != 0
    AttachmentCountGt: FilterCallableSingle = lambda message, count: len(message.attachments.split(' ')) > count
    AttachmentCountLt: FilterCallableSingle = lambda message, count: len(message.attachments.split(' ')) < count
    AttachmentCountEq: FilterCallableSingle = lambda message, count: len(message.attachments.split(' ')) == count

    ContainsUrl: FilterCallableNoarg = lambda message: _match_regex(message, r'(?:https?://|www\.)[^\s<>]+')

class Filter:
    def to_dict(self):
        return {
            "type": next((k for k, v in FILTERS.__dict__.items() if v == self.func), "Unknown"),
            "params": [
                arg for arg in self.args
            ]
        }

    def __init__(self, type: FILTERS, *args):
        self.func: FILTERS = type
        self.args = (*args,)
        self.matching_indices: Set[int] = set()
    
    def compute_matches(self, data: list[Message]):
        self.matching_indices = set()
        for i, message in enumerate(data):
            if self.match(message):
                self.matching_indices.add(i)
        return self.matching_indices

    def match(self, message: Message):
        return self.func(message, *self.args)
    
    def __and__(self, other: 'Filter'):
        if self.func == FILTERS.AlwaysTrue:
            return other
        from src.FilterEngine import FilterGroup
        combined = FilterGroup(FilterGroup.Logic.AND)
        combined.filters.append(self)
        combined.filters.append(other)
        return combined

    def __or__(self, other: 'Filter'):
        if self.func == FILTERS.AlwaysTrue:
            return other
        from src.FilterEngine import FilterGroup
        combined = FilterGroup(FilterGroup.Logic.OR)
        combined.filters.append(self)
        combined.filters.append(other)
        return combined
    
    def __invert__(self):
        from src.FilterEngine import FilterGroup
        negated = FilterGroup(FilterGroup.Logic.NOT)
        negated.filters.append(self)
        return negated
