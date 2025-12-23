from enum import Enum
from typing import Callable, List, Tuple, Any
import math as m
import re

from src.MessageRepo import MessageRepo, Message
from src.Filter import USER_MENTION_PATTERN, CHANNEL_MENTION_PATTERN

type Number = int | float

type CallableLayer0 = Callable[[List[Message]], List[Number]]
type CallableLayer00 = Callable[[List[Message], str], List[Number]]
type CallableLayer1 = Callable[[List[Number]], Number]
type CallableLayer2 = Callable[[Number, Number], Number]
type CallableLayer3 = Callable[[Number], Number]
type CallableLayerAny = CallableLayer0 | CallableLayer00 | CallableLayer1 | CallableLayer2 | CallableLayer3

type ASTNode = Tuple[CallableLayerAny, Tuple[Any, ...]] | Tuple[CallableLayerAny, Tuple[Any, ...], str]

class STATS(Enum):
    # Operates on List[Message]
    MessageLength: CallableLayer0 = lambda messages: [len(m.content) for m in messages]

    CountWords: CallableLayer0 = lambda messages: [len(m.content.split(' ')) for m in messages]
    CountAttachment: CallableLayer0 = lambda messages: [len(m.attachments.split(' ')) for m in messages]
    CountMentions: CallableLayer0 = lambda messages: [len(re.match(USER_MENTION_PATTERN, m.content)) for m in messages]

    CountCharacters: CallableLayer00 = lambda messages, chars: [sum([m.content.lower().count(c) for c in chars]) for m in messages]

    # Operates on List[Number]
    Average: CallableLayer1 = lambda array: sum(array) / len(array)
    Total: CallableLayer1 = lambda array: sum(array)

    # Operates on Numbers
    Ratio: CallableLayer2 = lambda l, r: l / r

    # Operates on Number
    AsPercentage: CallableLayer3 = lambda n: n * 100


"""
    This is the structure that defines how to map the english language to the stat builder
"""
Human = {
    "layer0": {
        "number of _": {
            "words": STATS.CountWords,
            "attachments": STATS.CountAttachment,
            "mentions": STATS.CountMentions,
            "characters ?": STATS.CountCharacters
        },
        "length of _": {
            "messages": STATS.MessageLength
        }
    },
    "layer1": {
        "average {l0}": STATS.Average,
        "total {l0}": STATS.Total
    },
    "layer2": {
        "ratio of the {l1} over the {l1}": STATS.Ratio
    },
    "layer3": {
        "{l3} as percentage": STATS.AsPercentage
    }
}

class HumanLanguage:
    def __init__(self):
        return

    def parse(self, command: str, context: dict = None):
        command = command.lower()
        idx = command.find("the")
        if idx == -1:
            return None
        command = command[idx+3:].strip()
        return self._parse_recursive(command, context)

    def _parse_recursive(self, text: str, context: dict = None) -> ASTNode | None:
        text = text.strip()
        
        # Iterate layers in reverse order to prefer higher-level constructs
        layers = sorted(Human.items(), key=lambda x: x[0], reverse=True)
        
        for layer_name, patterns in layers:
            # Handle "in #variable" for layer0
            # This syntax is strictly reserved for layer0 to define the scope (message source)
            current_text = text
            variable = None
            
            if layer_name == "layer0":
                match = re.search(r'\s+in\s+#(\w+)$', text)
                if match:
                    var_name = match.group(1)
                    if context and "variables" in context and var_name in context["variables"]:
                        variable = var_name
                        current_text = text[:match.start()].strip()
                    else:
                        # Variable not found or context missing, treat as part of text or fail?
                        # For now, let's assume if it looks like a variable but isn't valid, 
                        # we don't strip it (maybe it's part of the command?)
                        pass

            for pattern, value in patterns.items():
                if isinstance(value, dict):
                    if "_" not in pattern:
                        continue
                    
                    prefix, suffix = pattern.split("_", 1)
                    prefix = prefix.strip()
                    suffix = suffix.strip()
                    
                    if (not prefix or current_text.startswith(prefix)) and (not suffix or current_text.endswith(suffix)):
                        start = len(prefix)
                        end = len(current_text) - len(suffix)
                        if start > end: continue
                        
                        inner_text = current_text[start:end].strip()
                        
                        for sub_pattern, sub_value in value.items():
                            parts = re.split(r'(\{l\d\}|\?)', sub_pattern)
                            parts = [p for p in parts if p]
                            
                            res = self._match_pattern(inner_text, parts, context)
                            if res is not None:
                                if variable:
                                    return (sub_value, res, variable)
                                return (sub_value, res)
                else:
                    parts = re.split(r'(\{l\d\}|\?)', pattern)
                    parts = [p for p in parts if p]
                    
                    result = self._match_pattern(current_text, parts, context)
                    if result is not None:
                        if variable:
                            return (value, result, variable)
                        return (value, result)
        return None

    def _match_pattern(self, text: str, parts: List[str], context: dict = None) -> Tuple | None:
        if not parts:
            return () if not text else None
        
        part = parts[0]
        
        if part == "?":
            if len(parts) == 1:
                return (text,) if text else None
            
            next_part = parts[1]
            start = 0
            while True:
                idx = text.find(next_part, start)
                if idx == -1:
                    break
                
                candidate = text[:idx].strip()
                remainder = text[idx:]
                
                if not candidate:
                    start = idx + 1
                    continue

                res = self._match_pattern(remainder, parts[1:], context)
                if res is not None:
                    return (candidate,) + res
                
                start = idx + 1
            return None

        elif part.startswith("{"):
            if len(parts) == 1:
                res = self._parse_recursive(text, context)
                return (res,) if res else None
            
            next_part = parts[1]
            start = 0
            while True:
                idx = text.find(next_part, start)
                if idx == -1:
                    break
                
                candidate = text[:idx].strip()
                remainder = text[idx:]
                
                if not candidate:
                    start = idx + 1
                    continue

                res1 = self._parse_recursive(candidate, context)
                if res1:
                    res2 = self._match_pattern(remainder, parts[1:], context)
                    if res2 is not None:
                        return (res1,) + res2
                
                start = idx + 1
            return None

        else:
            if text.startswith(part):
                return self._match_pattern(text[len(part):].strip(), parts[1:], context)
            return None

        
