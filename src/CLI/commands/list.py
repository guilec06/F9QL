from typing import List, Dict, Any
from src.CLI.CommandReturn import CommandReturn

SHORT_DESCRIPTION: str = "Lists the content of the dynamic environment"
USAGE: List[str] = [
    "list [TYPE...]",
]
DESCRIPTION: str = "\tLists the content of the dynamic environment" \
"\n\n\tTYPE\tThe type of the content to display" \
"\n\n\tAvailable types are as follow:" \
"\n\n\tcollections\tDifferent collections loaded along with the filters that they matched with"

def command(args: List[str], env: Dict[str, Any]) -> CommandReturn:
    for elem in env:
        print(elem)
    return CommandReturn.SUCCESS
