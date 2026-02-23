from enum import Enum

class CommandReturn(Enum):
    SUCCESS = 0
    COMMAND_NOT_FOUND = 1
    QUIT = 2