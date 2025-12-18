from src.MessageRepo import MessageRepo, Message
from src.Channel import Channel
from src.Guild import Guild
from enum import Enum
from typing import Set
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


class Filter:
    class Type(Enum):
        # Time-based
        AFTER = 1
        BEFORE = 2
        BETWEEN = 3
        ON_DATE = 4
        HOUR_RANGE = 5  # Messages sent at certain hours (e.g., late night posts)
        DAY_OF_WEEK = 6
        YEAR = 7
        MONTH = 8
        
        # Location-based
        CHANNEL_ID = 9
        GUILD_ID = 10
        CHANNEL_NAME = 11
        GUILD_NAME = 12
        IS_DM = 13  # DMs you sent
        IS_GROUP_DM = 14
        TO_USER = 15  # DMs to specific user
        
        # Attachment-based
        HAS_ATTACHMENT = 16
        HAS_MORE_THAN_ATTACHMENT = 17
        HAS_LESS_THAN_ATTACHMENT = 18
        NO_ATTACHMENT = 19
        ATTACHMENT_TYPE = 20  # Images, videos, files YOU sent
        
        # Content-based (YOUR content)
        CONTAINS_TEXT = 23
        REGEX_MATCH = 24
        STARTS_WITH = 25
        ENDS_WITH = 26
        CONTAINS_URL = 27
        CONTAINS_EMOJI = 28
        CONTAINS_CUSTOM_EMOJI = 29
        IS_REPLY = 30  # Messages where YOU replied to someone
        
        # Length-based (YOUR message length)
        LENGTH_GT = 31
        LENGTH_LT = 32
        LENGTH_BETWEEN = 33
        WORD_COUNT_GT = 34
        WORD_COUNT_LT = 35
        IS_SHORT_MESSAGE = 36  # e.g., < 10 chars (like "lol", "gg")
        IS_LONG_MESSAGE = 37  # e.g., > 500 chars (essays)
        
        # Message type (things YOU did)
        
        CONTAINS_CODE_BLOCK = 41  # Code you shared
        
        # Mentions (people/roles YOU mentioned)
        MENTIONS_USER = 42  # You mentioned someone
        MENTIONS_ROLE = 43  # You mentioned a role
        MENTIONS_EVERYONE = 44  # You used @everyone
        MENTION_COUNT_GT = 45  # Messages where you mentioned multiple people
        
        # Activity patterns (YOUR behavior)
        FIRST_MESSAGE_IN_CHANNEL = 46  # First time you spoke in a channel
        LAST_MESSAGE_IN_CHANNEL = 47  # Last message you sent there
        
        # Content analysis (YOUR writing style)
        ALL_CAPS = 51  # MESSAGES LIKE THIS
        IS_SINGLE_EMOJI = 54  # Just "👍" or "😂"
        
        # Disabled: require either API calls or remote downloads to evaluate the size of the attachments (represented as links in the data provided)
        # ATTACHMENT_SIZE_GT = 21
        # ATTACHMENT_SIZE_LT = 22
        
        # Disabled: don't know yet how to implement those, mainly because the program currently doesn't parse event archives
        # IS_EDITED = 38  # Messages you edited
        # HAS_EMBEDS = 39  # Messages with embeds you sent
        # HAS_STICKERS = 40  # Stickers you used

        # Disabled: Claude suggested these, i'd say it's irrelevent since it's subjective and that it's already possible to manually check for these
        # SENT_DURING_WORK_HOURS = 48  # 9am-5pm
        # SENT_LATE_NIGHT = 49  # 11pm-6am
        # SENT_ON_WEEKEND = 50
        # HAS_QUESTION_MARK = 52  # Messages with questions
        # HAS_EXCLAMATION = 53  # Excited messages!
        # IS_COMMAND = 55  # Bot commands you sent (starts with !)

    def __new__(cls, type: 'Filter.Type', data, *args):
        """Factory pattern: instantiate the appropriate filter subclass"""
        if type in _FILTER_REGISTRY:
            return _FILTER_REGISTRY[type](data, *args)
        raise ValueError(f"Unknown filter type: {type}")


class BaseFilter:
    """Base class for all filters"""
    def __init__(self, data, *args):
        # data = message repository reference
        # args = filter criteria values (can be multiple for implicit OR logic)
        self.data = data  # Messages list
        self.values = args if args else ()  # Filter criteria
        self.matching_indices: Set[int] = set()
    
    def compute_matches(self):
        """Compute matching indices for all messages in self.data"""
        self.matching_indices = set()
        for i, message in enumerate(self.data):
            if self._matches(message):
                self.matching_indices.add(i)
    
    def _matches(self, message: Message) -> bool:
        """Override in subclasses to implement filter logic"""
        raise NotImplementedError

    def __and__(self, other: 'BaseFilter'):
        from src.FilterEngine import FilterGroup
        combined = FilterGroup(self.data, FilterGroup.Logic.AND)
        combined.filters.append(self)
        combined.filters.append(other)
        return combined

    def __or__(self, other: 'BaseFilter'):
        from src.FilterEngine import FilterGroup
        combined = FilterGroup(self.data, FilterGroup.Logic.OR)
        combined.filters.append(self)
        combined.filters.append(other)
        return combined
    
    def __invert__(self):
        from src.FilterEngine import FilterGroup
        negated = FilterGroup(self.data, FilterGroup.Logic.NOT)
        negated.filters.append(self)
        return negated


# ============================================================================
# TIME-BASED FILTERS
# ============================================================================

class AfterFilter(BaseFilter):
    """Messages after a specific timestamp"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_datetime(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.timestamp > self.values[0]


class BeforeFilter(BaseFilter):
    """Messages before a specific timestamp"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_datetime(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.timestamp < self.values[0]


class BetweenFilter(BaseFilter):
    """Messages between two timestamps"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = tuple(_parse_datetime(v) for v in self.values) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return self.values[0] <= message.timestamp <= self.values[1]


class OnDateFilter(BaseFilter):
    """Messages on one or more specific dates"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = tuple(_parse_date(v) for v in self.values) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return any(message.timestamp.date() == d for d in self.values)


class HourRangeFilter(BaseFilter):
    """Messages sent at certain hours"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = tuple(_parse_int(v) for v in self.values) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return self.values[0] <= message.timestamp.hour <= self.values[1]


class DayOfWeekFilter(BaseFilter):
    """Messages sent on one or more specific days of week"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = tuple(_parse_int(v) for v in self.values) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.timestamp.weekday() in self.values


class YearFilter(BaseFilter):
    """Messages from one or more specific years"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = tuple(_parse_int(v) for v in self.values) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.timestamp.year in self.values


class MonthFilter(BaseFilter):
    """Messages from one or more specific months"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = tuple(_parse_int(v) for v in self.values) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.timestamp.month in self.values


# ============================================================================
# LOCATION-BASED FILTERS
# ============================================================================

class ChannelIdFilter(BaseFilter):
    """Messages in one or more specific channels by ID"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.channel.id in self.values


class GuildIdFilter(BaseFilter):
    """Messages in one or more specific guilds by ID"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.guild.id in self.values


class ChannelNameFilter(BaseFilter):
    """Messages in one or more specific channels by name"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.channel.name in self.values


class GuildNameFilter(BaseFilter):
    """Messages in one or more specific guilds by name"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.guild.name in self.values


class IsDmFilter(BaseFilter):
    """Direct messages (DMs)"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.guild is None


class IsGroupDmFilter(BaseFilter):
    """Group direct messages"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.guild is None and message.is_group_dm


class ToUserFilter(BaseFilter):
    """DMs to one or more specific users"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.recipient.id in self.values


# ============================================================================
# ATTACHMENT-BASED FILTERS
# ============================================================================

class HasAttachmentFilter(BaseFilter):
    """Messages with at least one attachment"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.attachments) > 0


class HasMoreThanAttachmentFilter(BaseFilter):
    """Messages with more than N attachments"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_int(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.attachments) > self.values[0]


class HasLessThanAttachmentFilter(BaseFilter):
    """Messages with fewer than N attachments"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_int(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.attachments) < self.values[0]


class NoAttachmentFilter(BaseFilter):
    """Messages with no attachments"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.attachments) == 0


class AttachmentTypeFilter(BaseFilter):
    """Messages with one or more specific attachment types"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return any(att.type in self.values for att in message.attachments)


# ============================================================================
# CONTENT-BASED FILTERS
# ============================================================================

class ContainsTextFilter(BaseFilter):
    """Messages containing one or more specific text strings"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        content_lower = message.content.lower()
        return any(text.lower() in content_lower for text in self.values)


class RegexMatchFilter(BaseFilter):
    """Messages matching a regex pattern"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return re.search(self.values[0], message.content) is not None


class StartsWithFilter(BaseFilter):
    """Messages starting with one or more specific text strings"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return any(message.content.startswith(prefix) for prefix in self.values)


class EndsWithFilter(BaseFilter):
    """Messages ending with one or more specific text strings"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return any(message.content.endswith(suffix) for suffix in self.values)


class ContainsUrlFilter(BaseFilter):
    """Messages containing URLs"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return re.search(r'https?://', message.content) is not None


class ContainsEmojiFilter(BaseFilter):
    """Messages containing emoji"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return re.search(r'[\U0001F600-\U0001F64F]', message.content) is not None


class ContainsCustomEmojiFilter(BaseFilter):
    """Messages containing custom emoji"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return '<:' in message.content and ':' in message.content


class IsReplyFilter(BaseFilter):
    """Messages that are replies to other messages"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.reference is not None


# ============================================================================
# LENGTH-BASED FILTERS
# ============================================================================

class LengthGtFilter(BaseFilter):
    """Messages longer than N characters"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_int(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.content) > self.values[0]


class LengthLtFilter(BaseFilter):
    """Messages shorter than N characters"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_int(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.content) < self.values[0]


class LengthBetweenFilter(BaseFilter):
    """Messages with length between N and M characters"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = tuple(_parse_int(v) for v in self.values) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return self.values[0] <= len(message.content) <= self.values[1]


class WordCountGtFilter(BaseFilter):
    """Messages with more than N words"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_int(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.content.split()) > self.values[0]


class WordCountLtFilter(BaseFilter):
    """Messages with fewer than N words"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_int(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.content.split()) < self.values[0]


class IsShortMessageFilter(BaseFilter):
    """Very short messages (< 10 characters)"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.content) < 10


class IsLongMessageFilter(BaseFilter):
    """Very long messages (> 500 characters)"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.content) > 500


# ============================================================================
# MESSAGE TYPE FILTERS
# ============================================================================

class ContainsCodeBlockFilter(BaseFilter):
    """Messages containing code blocks"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return '```' in message.content


# ============================================================================
# MENTION FILTERS
# ============================================================================

class MentionsUserFilter(BaseFilter):
    """Messages mentioning one or more specific users"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return any(mention.id in self.values for mention in message.mentions)


class MentionsRoleFilter(BaseFilter):
    """Messages mentioning one or more specific roles"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return any(role.id in self.values for role in message.role_mentions)


class MentionsEveryoneFilter(BaseFilter):
    """Messages using @everyone"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.mention_everyone


class MentionCountGtFilter(BaseFilter):
    """Messages mentioning more than N users/roles"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.values = (_parse_int(self.values[0]),) if self.values else ()
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.mentions) > self.values[0]


# ============================================================================
# ACTIVITY PATTERN FILTERS
# ============================================================================

class FirstMessageInChannelFilter(BaseFilter):
    """First message sent in a channel"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message == message.channel.messages[0]


class LastMessageInChannelFilter(BaseFilter):
    """Last message sent in a channel"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message == message.channel.messages[-1]


# ============================================================================
# CONTENT ANALYSIS FILTERS
# ============================================================================

class AllCapsFilter(BaseFilter):
    """Messages in ALL CAPS"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return message.content.isupper() and len(message.content) > 0


class IsSingleEmojiFilter(BaseFilter):
    """Messages containing only a single emoji"""
    def __init__(self, data, *args):
        super().__init__(data, *args)
        self.compute_matches()
    
    def _matches(self, message: Message) -> bool:
        return len(message.content.strip()) <= 2 and re.search(r'[\U0001F600-\U0001F64F]', message.content) is not None


# ============================================================================
# REGISTRY: Map Filter.Type to filter classes
# ============================================================================

_FILTER_REGISTRY = {
    Filter.Type.AFTER: AfterFilter,
    Filter.Type.BEFORE: BeforeFilter,
    Filter.Type.BETWEEN: BetweenFilter,
    Filter.Type.ON_DATE: OnDateFilter,
    Filter.Type.HOUR_RANGE: HourRangeFilter,
    Filter.Type.DAY_OF_WEEK: DayOfWeekFilter,
    Filter.Type.YEAR: YearFilter,
    Filter.Type.MONTH: MonthFilter,
    Filter.Type.CHANNEL_ID: ChannelIdFilter,
    Filter.Type.GUILD_ID: GuildIdFilter,
    Filter.Type.CHANNEL_NAME: ChannelNameFilter,
    Filter.Type.GUILD_NAME: GuildNameFilter,
    Filter.Type.IS_DM: IsDmFilter,
    Filter.Type.IS_GROUP_DM: IsGroupDmFilter,
    Filter.Type.TO_USER: ToUserFilter,
    Filter.Type.HAS_ATTACHMENT: HasAttachmentFilter,
    Filter.Type.HAS_MORE_THAN_ATTACHMENT: HasMoreThanAttachmentFilter,
    Filter.Type.HAS_LESS_THAN_ATTACHMENT: HasLessThanAttachmentFilter,
    Filter.Type.NO_ATTACHMENT: NoAttachmentFilter,
    Filter.Type.ATTACHMENT_TYPE: AttachmentTypeFilter,
    Filter.Type.CONTAINS_TEXT: ContainsTextFilter,
    Filter.Type.REGEX_MATCH: RegexMatchFilter,
    Filter.Type.STARTS_WITH: StartsWithFilter,
    Filter.Type.ENDS_WITH: EndsWithFilter,
    Filter.Type.CONTAINS_URL: ContainsUrlFilter,
    Filter.Type.CONTAINS_EMOJI: ContainsEmojiFilter,
    Filter.Type.CONTAINS_CUSTOM_EMOJI: ContainsCustomEmojiFilter,
    Filter.Type.IS_REPLY: IsReplyFilter,
    Filter.Type.LENGTH_GT: LengthGtFilter,
    Filter.Type.LENGTH_LT: LengthLtFilter,
    Filter.Type.LENGTH_BETWEEN: LengthBetweenFilter,
    Filter.Type.WORD_COUNT_GT: WordCountGtFilter,
    Filter.Type.WORD_COUNT_LT: WordCountLtFilter,
    Filter.Type.IS_SHORT_MESSAGE: IsShortMessageFilter,
    Filter.Type.IS_LONG_MESSAGE: IsLongMessageFilter,
    Filter.Type.CONTAINS_CODE_BLOCK: ContainsCodeBlockFilter,
    Filter.Type.MENTIONS_USER: MentionsUserFilter,
    Filter.Type.MENTIONS_ROLE: MentionsRoleFilter,
    Filter.Type.MENTIONS_EVERYONE: MentionsEveryoneFilter,
    Filter.Type.MENTION_COUNT_GT: MentionCountGtFilter,
    Filter.Type.FIRST_MESSAGE_IN_CHANNEL: FirstMessageInChannelFilter,
    Filter.Type.LAST_MESSAGE_IN_CHANNEL: LastMessageInChannelFilter,
    Filter.Type.ALL_CAPS: AllCapsFilter,
    Filter.Type.IS_SINGLE_EMOJI: IsSingleEmojiFilter,
}

FilterType = Filter.Type
