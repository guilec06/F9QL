from typing import Dict, Callable, List, Any
from enum import Enum

from src.Config import Config
from src.MessageRepo import MessageRepo, Message
from src.Filter import Filter, FILTERS
from src.FilterEngine import FilterEngine
from src.CLI.CommandReturn import CommandReturn
import src.Stat as s
import src.utils.Strings as strings

import os
import runpy

COMMAND_DIR_PATH = os.path.join(os.path.dirname(__file__), "commands")

def fn_Help(args: List[str], env: Dict[str, Any]) -> CommandReturn:
    command_list = [c for c in os.listdir(COMMAND_DIR_PATH) if c.split('.')[-1] == 'py']

    if len(args) == 1:
        for file in command_list:
            command = file.split('.')[0]
            path = os.path.join(COMMAND_DIR_PATH, file)
            ns = runpy.run_path(path)
            print(f"\t{command:<20} {ns.get("SHORT_DESCRIPTION", "")}")
    else:
        command = args[1]
        if command + ".py" not in command_list:
            return CommandReturn.COMMAND_NOT_FOUND
        path = os.path.join(COMMAND_DIR_PATH, command + ".py")
        ns = runpy.run_path(path)
        print("USAGE:")
        for usage in ns.get("USAGE", []):
            print("\t" + usage)
        print("DESCRIPTION:")
        print(ns.get("DESCRIPTION", ""))
    return CommandReturn.SUCCESS

def fn_Quit(args: List[str], env: Dict[str, Any]) -> CommandReturn:
    return CommandReturn.QUIT

BUILTINS: Dict[str, Callable[[List[str], List[str]], Any]] = {
    "help": fn_Help,
    "quit": fn_Quit
}

def run_command(args: List[str], env: Dict[str, Any]) -> int:
    ns = runpy.run_path(os.path.join(COMMAND_DIR_PATH, args[0] + ".py"))
    if ns.get("command", ""):
        return ns["command"](args, env)

def run_command_or_builtin(args: List[str], env: Dict[str, Any]) -> int:
    ret_value: CommandReturn = CommandReturn.SUCCESS
    command_list = [c.split('.')[0] for c in os.listdir(COMMAND_DIR_PATH) if c.split('.')[-1] == 'py']
    command = args[0]


    if command in BUILTINS:
        ret_value = BUILTINS[command](args, env)
    elif command in command_list:
        ret_value = run_command(args, env)
    else:
        ret_value = CommandReturn.COMMAND_NOT_FOUND

    return ret_value


def start():
    repo = MessageRepo(Config.MESSAGES)

    print("\n\tWelcome to the F9 Quickload Command Line Interface.")
    print(f"\tThe given path to the discord package is {Config.ROOT}.")
    print(f"\tThe user this package belongs to is {Config.USER_DATA["username"]} (global name: {Config.USER_DATA["global_name"]}, id: {Config.USER_ID})")
    print(f"\tThe package contains {repo.get_n_messages()} messages in {repo.get_n_channels()} channels.")

    print()
    print("If this is not your account, and if the owner of this account hasn't given you permission to exploit his data, please quit immediately and delete the archive.")
    print("This is a serious privacy violation.")
    print()
    print("type 'help' for the help page")
    print("to exit the cli, type 'quit' or press CTRL+D, CTRL+C or CTRL+Z (Windows)")

    last_return: CommandReturn = CommandReturn.SUCCESS

    while True:
        try:
            line = input("> ")
            tokens = strings.tokenize(line)
            if len(tokens) > 0:
                last_return = run_command_or_builtin(tokens, {})
            if last_return == CommandReturn.QUIT:
                break
            if last_return == CommandReturn.COMMAND_NOT_FOUND:
                print(f"Unknown command '{tokens[0]}'. Type help to list all commands")
                continue
            if last_return != CommandReturn.SUCCESS:
                print(f"Error processing command: {last_return.name}")
                break
        except EOFError:
            print("CTRL+D / CTRL+Z pressed. Quitting...")
            break
        except KeyboardInterrupt:
            print("CTRL+C pressed. Quitting...")
            break
