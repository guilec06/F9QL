from typing import List, Dict, Any
from src.CLI.CommandReturn import CommandReturn

SHORT_DESCRIPTION: str = "je plope tu plopes il plope nous plopons vous plopez ils plopent"
USAGE: List[str] = [
    "plop",
    "big plop"
]
DESCRIPTION: str = "\tjust plops"

def command(args: List[str], env: Dict[str, Any]) -> CommandReturn:
    print("plop")
    return CommandReturn.SUCCESS
