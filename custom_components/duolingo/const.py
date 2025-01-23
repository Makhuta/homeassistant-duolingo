from typing import Final

DOMAIN: Final = "duolingo"

CONF_USERNAME_LABEL: Final = 'Which usernames to consider:'
CONF_JWT: Final = 'jwt'
CONF_INTERVAL: Final = 'interval'
TIER_LIST: Final = {
                        "0": "Bronze",
                        "1": "Silver",
                        "2": "Gold",
                        "3": "Sapphire",
                        "4": "Ruby",
                        "5": "Emerald",
                        "6": "Amethyst",
                        "7": "Pearl",
                        "8": "Obsidian",
                        "9": "Diamond",
                    }
FORCE_SCRAPE: Final = "scrape_duolingo_data"

functionType: Final = type(lambda _:_)
