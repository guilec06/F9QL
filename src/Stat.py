from typing import Callable, List, Tuple, Any, TypedDict, Iterable, Pattern, Dict
from src.MessageRepo import Message

import re
import random

type Number = int | float
type SourceObj = List[Message | List[Message]]
type SourceEnvironment = Dict[str, SourceObj]

# Layer 0: operates on source and returns a list fo number
type CallableLayer0 = Callable[[SourceObj], List[Number]]
type CallableLayer00 = Callable[[SourceObj, str], List[Number]]

# Layer 1: Operates on a list of number and returns a single number
type CallableLayer1 = Callable[[List[Number]], Number]
type CallableLayer01 = Callable[[List[Number], str], Number]

# Layer 2: Operates on 2 numbers and returns a single one
type CallableLayer2 = Callable[[Number, Number], Number]
type CallableLayer02 = Callable[[Number, Number, str], Number]

# Layer 3: Operates on a single number and returns a single number
type CallableLayer3 = Callable[[Number], Number]
type CallableLayer03 = Callable[[Number, str], Number]

# Source alterers (Layer -1): Take a source obj and variadic arguments, return a new source obj
type CallableAlterSource = Callable[[SourceObj, Iterable], SourceObj]

type CallableLayerNoArgs    =   CallableLayer0\
                            |   CallableLayer1\
                            |   CallableLayer2\
                            |   CallableLayer3

type CallableLayerWithArgs  =   CallableLayer00\
                            |   CallableLayer01\
                            |   CallableLayer02\
                            |   CallableLayer03

# Any layer: used to pass any layer
type CallableLayerAny   =\
                            CallableLayerNoArgs\
                        |   CallableLayerWithArgs\
                        |   CallableAlterSource

USER_MENTION_PATTERN = r"<@\d{17,20}>"

def _split_period(data: List[Message], period: str, combine: bool = False):
    period_map = {
        'month': f'{'%Y-' if not combine else ''}%m',
        'day': f'{'%Y-%m-' if not combine else ''}%d',
        'year': f'%Y',
        'week': f'{'%Y-W' if not combine else ''}%W',
        'hour': f'{'%Y-W%W-d%d-H' if not combine else ''}%H',
        'minute': f'{'%Y-W%W-d%d-H%H-M' if not combine else ''}%M',
    }

    if period not in period_map:
        return [data]

    groups = {}
    for message in data:
        key = message.timestamp.strftime(period_map[period])
        if key not in groups:
            groups[key] = []
        groups[key].append(message)
        
    return list(groups.values())

def _split_by_attr(data: List[Message], *args):
    attr_path = args
    split_dict = {}

    for message in data:
        curr_attr = message
        aborted = False
        for attr in attr_path:
            # the 2nd condition takes advantage of python's boolean logic on empty strings (evalued to False)
            # avoiding putting every non categorized messages in a single group
            # Though a better practice would be for the user to effectively filter these out first before applying statistics
            if not hasattr(curr_attr, attr) or not getattr(curr_attr, attr):
                aborted = True
                break
            curr_attr = getattr(curr_attr, attr)
        if aborted:
            continue
        if curr_attr not in split_dict:
            split_dict[curr_attr] = [message]
        else:
            split_dict[curr_attr].append(message)
    return list(split_dict.values())

class MODIFIERS:
    # Source modifiers
    # Receives SourceEnvironment, returns SourceObj (List[Message] or List[List[Message]])
    CHANGE_SOURCE: CallableAlterSource = lambda env, *args: env.get(args[0], [])
    SPLIT_MONTHLY: CallableAlterSource = lambda env, *args: _split_period(env.get("_use_source", env.get("default", [])), "month")
    SPLIT_YEARLY: CallableAlterSource = lambda env, *args: _split_period(env.get("_use_source", env.get("default", [])), "year")
    SPLIT_WEEKLY: CallableAlterSource = lambda env, *args: _split_period(env.get("_use_source", env.get("default", [])), "week")
    SPLIT_DAILY: CallableAlterSource = lambda env, *args: _split_period(env.get("_use_source", env.get("default", [])), "day")
    SPLIT_HOURLY: CallableAlterSource = lambda env, *args: _split_period(env.get("_use_source", env.get("default", [])), "hour")
    SPLIT_MINUTELY: CallableAlterSource = lambda env, *args: _split_period(env.get("_use_source", env.get("default", [])), "minute")
    SPLIT_GUILDS: CallableAlterSource = lambda env, *args: _split_by_attr(env.get("default", []), "channel", "guild_id")
    SPLIT_CHANNELS: CallableAlterSource = lambda env, *args: _split_by_attr(env.get("default", []), "channel", "id")


class STATS:
    # Operates on List[Message] or List[List[Message]]
    # When input is grouped (List[List[Message]]), recursive calls are summed to produce one number per group
    MESSAGE_LENGTH: CallableLayer0 = lambda messages: [len(m.content) if isinstance(m, Message) else sum(STATS.MESSAGE_LENGTH(m)) for m in messages]
    MESSAGE_COUNT: CallableLayer0 = lambda messages: [1 if isinstance(m, Message) else sum(STATS.MESSAGE_COUNT(m)) for m in messages]

    COUNT_WORDS: CallableLayer0 = lambda messages: [len(m.content.split()) if isinstance(m, Message) else sum(STATS.COUNT_WORDS(m)) for m in messages]
    COUNT_ATTACHMENT: CallableLayer0 = lambda messages: [len(m.attachments.split()) if isinstance(m, Message) else sum(STATS.COUNT_ATTACHMENT(m)) for m in messages]
    COUNT_MENTIONS: CallableLayer0 = lambda messages: [len(re.findall(USER_MENTION_PATTERN, m.content)) if isinstance(m, Message) else sum(STATS.COUNT_MENTIONS(m)) for m in messages]

    COUNT_CHARACTERS: CallableLayer00 = lambda messages, chars: [sum(m.content.lower().count(c) if isinstance(m, Message) else sum(STATS.COUNT_CHARACTERS(sub_msg, chars) for sub_msg in m) for c in chars) for m in messages]

    # Operates on List[Number] or List[List[Number]]
    AVERAGE: CallableLayer1 = lambda array: sum(array) / len(array) if len(array) > 0 else 0
    TOTAL: CallableLayer1 = lambda array: sum(array)

    # Operates on Numbers
    RATIO: CallableLayer2 = lambda l, r: l / r if r != 0 else 0

    # Operates on Number
    AS_PERCENTAGE: CallableLayer3 = lambda n: n * 100

"""
    This variable defines how the language parser should behave:
        what composition translates to what logic
    
    The structure is the following:
        layer-1:
            groupN:
                COMPOSABLE...
        layer0:
            COMPOSABLE...
        layer1:
            COMPOSABLE...
        layer2:
            COMPOSABLE...
        layer3:
            COMPOSABLE...
    
    A "COMPOSABLE" element can be a simple straight entry like 'words' or a nested structure with special characters to traverse it down
    A "COMPOSABLE" always ends with a mapping to a logic entity (function/lambda)
    What can a COMPOSABLE be composed of:
        _ : Defines that at the place of '_' can reside and sub-composable pattern
        ? : Non-optional parameter, this can be anything that the user sets, any COMPOSABLE that have this but is not the end of the tree passes the parameter down, meaning all sub-composable logic components have to handle it
        # : this references a variable places in the environment, similar to '?' but passes the corresponding key in the env
        {N}: Defines that at this spot should reside a COMPOSABLE of the layer N
"""
Human = {
    "layer-1": {
        # Commands in each groups are mutually exclusives:
        # Only one command per group allowed
        # Groups with the lowest index have precedence over groups with higher indexes:
        # group0 is treated BEFORE group1 even if group1 is mentionned before group0
        "group0": {
            "in #": MODIFIERS.CHANGE_SOURCE
        },
        "group1": {
            "per _": {
                "year": MODIFIERS.SPLIT_YEARLY,
                "month": MODIFIERS.SPLIT_MONTHLY,
                "week": MODIFIERS.SPLIT_WEEKLY,
                "day": MODIFIERS.SPLIT_DAILY,
                "hour": MODIFIERS.SPLIT_HOURLY,
                "minute": MODIFIERS.SPLIT_MINUTELY,
                "guild": MODIFIERS.SPLIT_GUILDS,
                "channel": MODIFIERS.SPLIT_CHANNELS
            },
        }
    },
    # Each layer treats on a different data set.
    # Each layer can convert the previous' layer result into the next layer format
    # Layers with lower indexes are treated first
    # LayerN cannot be called if layerN-1 is not called (except layer0)
    "layer0": {
        "number of _": {
            "words": STATS.COUNT_WORDS,
            "messages": STATS.MESSAGE_COUNT,
            "attachments": STATS.COUNT_ATTACHMENT,
            "mentions": STATS.COUNT_MENTIONS,
            "characters ?": STATS.COUNT_CHARACTERS
        },
        "length of _": {
            "messages": STATS.MESSAGE_LENGTH
        }
    },
    "layer1": {
        "average {0}": STATS.AVERAGE,
        "total {0}": STATS.TOTAL
    },
    "layer2": {
        "ratio of the {1} over the {1}": STATS.RATIO
    },
    "layer3": {
        "{2} as percentage": STATS.AS_PERCENTAGE
    }
}

class ASTNode:
    """Represents a node in the parsed AST"""
    def __init__(self, layer: int, fn: CallableLayerAny, args: tuple = (), children: List['ASTNode'] = None):
        self.layer = layer
        self.fn = fn
        self.args = args  # Captured values (?, #)
        self.children = children or []  # Child nodes for {N} references
        self.modifiers: List['ASTNode'] = []  # Layer -1 modifiers

    def __repr__(self):
        child_repr = f", children={self.children}" if self.children else ""
        mod_repr = f", modifiers={self.modifiers}" if self.modifiers else ""
        args_repr = f", args={self.args}" if self.args else ""
        return f"ASTNode(layer={self.layer}{args_repr}{child_repr}{mod_repr})"

    def eval(self, env: SourceEnvironment) -> Number | List[Number]:
        """Evaluate this node against the environment"""
        # Apply modifiers first (layer -1)
        current_source = env.get("default", [])
        for mod in self.modifiers:
            current_source = mod.fn(env, *mod.args)
            env = {**env, "_use_source": current_source}

        # Evaluate based on layer
        if self.layer == 0:
            # Layer 0: source -> List[Number]
            source = env.get("_use_source", env.get("default", []))
            if self.args:
                return self.fn(source, *self.args)
            return self.fn(source)

        elif self.layer == 1:
            # Layer 1: List[Number] -> Number
            child_result = self.children[0].eval(env)
            return self.fn(child_result)

        elif self.layer == 2:
            # Layer 2: Number, Number -> Number
            left = self.children[0].eval(env)
            right = self.children[1].eval(env)
            return self.fn(left, right)

        elif self.layer == 3:
            # Layer 3: Number -> Number
            child_result = self.children[0].eval(env)
            return self.fn(child_result)

        elif self.layer == -1:
            # Modifier: shouldn't be evaluated directly
            return self.fn(env, *self.args)

        raise ValueError(f"Unknown layer: {self.layer}")


class ParseError(Exception):
    """Raised when parsing fails"""
    pass


class Parser:
    # Only skip these at expression boundaries, NOT during pattern matching
    FILLER_WORDS = {"the", "a", "an"}

    @staticmethod
    def tokenize(nl_str: str) -> List[str]:
        """Tokenize input string, handling quoted strings"""
        tokens: List[str] = []
        current: str = ""
        in_quotes: bool = False

        for char in nl_str:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ' ' and not in_quotes:
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += char

        if current:
            tokens.append(current)

        return tokens

    def __init__(self, nl_str: str, context: dict = None):
        self.tokens: List[str] = Parser.tokenize(nl_str.lower())
        self.pos = 0
        self.context = context if context is not None else Human

    # ─── Token Navigation ────────────────────────────────────────────────

    def peek(self, offset: int = 0) -> str | None:
        """Look at token without consuming"""
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def consume(self) -> str | None:
        """Consume and return current token"""
        if self.pos >= len(self.tokens):
            return None
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def skip_filler(self):
        """Skip filler words like 'the', 'a', 'an'"""
        while self.peek() in self.FILLER_WORDS:
            self.consume()

    def save_pos(self) -> int:
        """Save current position for backtracking"""
        return self.pos

    def restore_pos(self, pos: int):
        """Restore position for backtracking"""
        self.pos = pos

    # ─── Pattern Matching ────────────────────────────────────────────────

    def match_pattern(self, pattern: str) -> Tuple[bool, List[Any]]:
        """
        Try to match a pattern against current tokens.
        Returns (success, captured_values).

        Pattern markers:
            _  : expects a sub-key (returned as string to look up)
            ?  : captures next token as user argument
            #  : captures next token as env variable (must start with #)
            {N}: recursively parses layer N expression
        """
        pattern_tokens = pattern.split()
        captures = []
        start_pos = self.save_pos()

        for pt in pattern_tokens:
            current = self.peek()

            if current is None:
                self.restore_pos(start_pos)
                return False, []

            if pt == "_":
                # Capture token as sub-key lookup
                captures.append(("subkey", self.consume()))

            elif pt == "?":
                # Capture next token as user argument
                captures.append(("arg", self.consume()))

            elif pt == "#":
                # Capture env variable (token should start with #)
                if current.startswith("#"):
                    captures.append(("env", self.consume()[1:]))  # Strip #
                else:
                    self.restore_pos(start_pos)
                    return False, []

            elif pt.startswith("{") and pt.endswith("}"):
                # Recursive layer reference - skip filler before recursive parse
                self.skip_filler()
                layer_num = int(pt[1:-1])
                child_node = self.parse_layer(layer_num)
                if child_node is None:
                    self.restore_pos(start_pos)
                    return False, []
                captures.append(("node", child_node))

            else:
                # Literal token match (exact match required)
                if current == pt:
                    self.consume()
                else:
                    self.restore_pos(start_pos)
                    return False, []

        return True, captures

    # ─── Layer Parsing ───────────────────────────────────────────────────

    def parse(self) -> ASTNode | None:
        """Main entry point: parse from highest layer down"""
        self.skip_filler()

        # Try layers from highest (3) to lowest (0)
        for layer in [3, 2, 1, 0]:
            node = self.parse_layer(layer)
            if node is not None:
                return node

        return None

    def parse_layer(self, layer: int) -> ASTNode | None:
        """Parse a specific layer"""
        layer_key = f"layer{layer}"
        layer_def = self.context.get(layer_key, {})

        if not layer_def:
            return None

        start_pos = self.save_pos()
        self.skip_filler()

        for pattern, value in layer_def.items():
            self.restore_pos(start_pos)
            self.skip_filler()

            matched, captures = self.match_pattern(pattern)
            if not matched:
                continue

            # Process captures and resolve nested structures
            result = self.resolve_pattern_value(value, captures, layer)
            if result is not None:
                # Try to attach layer-1 modifiers
                result = self.attach_modifiers(result)
                return result

        self.restore_pos(start_pos)
        return None

    def resolve_pattern_value(self, value: Any, captures: List[Tuple[str, Any]], layer: int) -> ASTNode | None:
        """
        Resolve the pattern's value, handling nested dicts for '_' markers.
        """
        children = []
        args = []

        for cap_type, cap_value in captures:
            if cap_type == "subkey":
                # Look up in nested dict
                if isinstance(value, dict):
                    # Try to match subkey, possibly with additional patterns
                    sub_result = self.resolve_subkey(value, cap_value, layer)
                    if sub_result is None:
                        return None
                    return sub_result
                else:
                    return None

            elif cap_type == "arg":
                args.append(cap_value)

            elif cap_type == "env":
                args.append(cap_value)

            elif cap_type == "node":
                children.append(cap_value)

        # Value should be a callable at this point
        if callable(value):
            return ASTNode(layer=layer, fn=value, args=tuple(args), children=children)

        return None

    def resolve_subkey(self, subdict: dict, key: str, layer: int) -> ASTNode | None:
        """Resolve a subkey in a nested dict, handling patterns with ? or nested _"""
        for pattern, value in subdict.items():
            pattern_parts = pattern.split()

            # Simple key match
            if pattern == key:
                if callable(value):
                    return ASTNode(layer=layer, fn=value)
                elif isinstance(value, dict):
                    # Need to continue matching
                    return None

            # Pattern with key + modifiers (e.g., "characters ?")
            if pattern_parts[0] == key:
                # Match remaining pattern parts
                remaining_pattern = " ".join(pattern_parts[1:])
                if remaining_pattern:
                    matched, captures = self.match_pattern(remaining_pattern)
                    if matched:
                        args = [cv for ct, cv in captures if ct in ("arg", "env")]
                        if callable(value):
                            return ASTNode(layer=layer, fn=value, args=tuple(args))
                else:
                    if callable(value):
                        return ASTNode(layer=layer, fn=value)

        return None

    def attach_modifiers(self, node: ASTNode) -> ASTNode:
        """Try to parse and attach layer-1 modifiers to a node"""
        layer_minus1 = self.context.get("layer-1", {})

        # Sort groups by key to ensure order (group0 before group1)
        sorted_groups = sorted(layer_minus1.items(), key=lambda x: x[0])

        for _, group_patterns in sorted_groups:
            start_pos = self.save_pos()
            self.skip_filler()

            for pattern, value in group_patterns.items():
                self.restore_pos(start_pos)
                self.skip_filler()

                matched, captures = self.match_pattern(pattern)
                if matched:
                    # Create modifier node
                    args = []
                    for cap_type, cap_value in captures:
                        if cap_type == "subkey":
                            # Nested modifier (e.g., "per _")
                            if isinstance(value, dict):
                                if cap_value in value:
                                    mod_node = ASTNode(layer=-1, fn=value[cap_value])
                                    node.modifiers.append(mod_node)
                                    break
                        elif cap_type in ("arg", "env"):
                            args.append(cap_value)
                    else:
                        if callable(value):
                            mod_node = ASTNode(layer=-1, fn=value, args=tuple(args))
                            node.modifiers.append(mod_node)
                    break

        return node


# ─── Test ────────────────────────────────────────────────────────────────

nl = "the ratio of the total number of attachments in #match1 over the total number of attachments in #match2 as percentage"

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "number of words",
        "total number of messages",
        "average number of attachments",
        "number of characters abc",
        "total number of words per month",
        "ratio of the total number of messages over the total number of words",
        nl
    ]

    for test in test_cases:
        print(f"\nParsing: '{test}'")
        parser = Parser(test)
        result = parser.parse()
        print(f"  Result: {result}")
