#!/usr/bin/env python3

import os
import json

class ReadOnlyMeta(type):
    """Metaclass to make class variables read-only after initialization"""
    _initializing = False
    
    def __setattr__(cls, name, value):
        if name == '_initializing' or cls._initializing:
            super().__setattr__(name, value)
        else:
            raise AttributeError(f"Cannot modify read-only Config attribute '{name}'")

class Config(metaclass=ReadOnlyMeta):
    ROOT = ""
    LANG = ""
    USER_ID = ""
    USER_DATA = {}
    ACTIVITIES = ""
    ACTIVITY = ""
    ACCOUNT = ""
    SUPPORT = ""
    MESSAGES = ""
    ADS = ""
    GUILDS = ""

    @staticmethod
    def init(root: str = "package", lang :str = "en"):
        """Initialize the environment for the program

        Args:
            root (str): The root where the discord files are located
            lang (str): The ISO 639-1 locale code of the language the archive is in in order to load the proper files
        """
        Config._initializing = True
        
        Config.ROOT = os.path.realpath(root)
        Config.LANG = lang

        locale_file = json.loads(open(f"locale/{lang}.json", "r").read())

        Config.ACTIVITIES = os.path.join(Config.ROOT, locale_file["activities"])
        Config.ACTIVITY = os.path.join(Config.ROOT, locale_file["activity"])
        Config.ACCOUNT = os.path.join(Config.ROOT, locale_file["account"])
        Config.SUPPORT = os.path.join(Config.ROOT, locale_file["support"])
        Config.MESSAGES = os.path.join(Config.ROOT, locale_file["messages"])
        Config.ADS = os.path.join(Config.ROOT, locale_file["ads"])
        Config.GUILDS = os.path.join(Config.ROOT, locale_file["guilds"])
        
        Config.USER_DATA = json.loads(open(os.path.join(Config.ACCOUNT, "user.json"), "r").read())
        Config.USER_ID = Config.USER_DATA["id"]
        
        Config._initializing = False

__all__ = ['Config']
