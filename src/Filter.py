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

type FilterCallableNoarg = Callable[[], bool]
type FilterCallableSingle = Callable[[Message, str], bool]
type FilterCallableMultiple = Callable[[Message, list[str]], bool]
type FilterAny = FilterCallableNoarg | FilterCallableSingle | FilterCallableMultiple

class FILTERS(Enum):
    AlwaysTrue: FilterCallableNoarg = lambda: True
    After: FilterCallableSingle = lambda message, timestamp: message.timestamp > _parse_datetime(timestamp)
    Before: FilterCallableSingle = lambda message, timestamp: message.timestamp < _parse_datetime(timestamp)
    Between: FilterCallableMultiple = lambda message, *periods: _parse_datetime(periods[0]) < message.timestamp < _parse_datetime(periods[1])
    Recipients: FilterCallableMultiple = lambda message, *recipients: all(r in message.channel.recipients for r in recipients)

class Filter:
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
