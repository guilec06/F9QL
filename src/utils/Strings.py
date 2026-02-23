from typing import Tuple, List

def tokenize(s: str, quotes: Tuple[str] = ('"'), seps: Tuple[str] = (" ")) -> List[str]:
    tokens: List[str] = []
    curr_tok: str = ""
    in_quotes: bool = False

    for c in s:
        if c in seps and not in_quotes:
            if curr_tok:
                tokens.append(curr_tok)
                curr_tok = ""
        elif c in quotes:
            in_quotes = not in_quotes
        else:
            curr_tok += c
    if curr_tok:
        tokens.append(curr_tok)
    
    return tokens
