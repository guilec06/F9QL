from typing import List, Dict, Any
from src.CLI.CommandReturn import CommandReturn

SHORT_DESCRIPTION: str = "Displays the status of the program"
USAGE: List[str] = [
    "status",
]
DESCRIPTION: str = "\tDisplays the status of the program"

def command(args: List[str], env: Dict[str, Any]) -> CommandReturn:
    print("status")
    return CommandReturn.SUCCESS
