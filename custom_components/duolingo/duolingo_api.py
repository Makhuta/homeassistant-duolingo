from .duolingo import Duolingo

class DuolingoAPI():
    def __init__(self, username=None, jwt=None):
        self.username = username
        try:
            self.lingo = Duolingo(username=username, jwt=jwt)
        except:
            raise FailedToLogin

    def get_username(self):
        return self.username
    
    def update(self):
        functions = {
            "user_info": self.lingo.get_user_info,
            "languages_details": self.lingo.get_languages_details,
            "leaderboard": self.lingo.get_leaderboard,
            "leaderboard_position": self.lingo.get_leaderboard_position,
            "streak_info": self.lingo.get_streak_info,
            "friends": self.lingo.get_friends,
        }

        data = {}

        for (key, function) in functions.items():
            try:
                data[key] = function()
            except:
                data[key] = {}
                pass

        return data


class FailedToLogin(Exception):
    "Raised when the Duolingo user fail to Log-in"
    pass