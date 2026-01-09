import re, json, random, requests, logging
_LOGGER = logging.getLogger(__name__)
from datetime import datetime, timedelta, timezone
from json import JSONDecodeError
from typing import Final


class DuolingoException(Exception):
    pass


class AlreadyHaveStoreItemException(DuolingoException):
    pass


class InsufficientFundsException(DuolingoException):
    pass


class CaptchaException(DuolingoException):
    pass

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
class Base:
    USER_AGENT = lambda _, x: "Duodroid/6.58.6 (Linux; Android 12)" \
                           if x else \
                           "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"

    def __init__(self, username, password=None, jwt=None, *args, **kwargs):
        """
        :param username: Username to use for duolingo
        :param password: Password to authenticate as user.
        :param jwt: Duolingo login token. Will be checked and used if it is valid request.
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.jwt = jwt

    def _check_login(self):
        resp = self._make_req(f"https://duolingo.com/users/{self.username}")
        return resp.status_code == 200

    def _make_req(self, url, data=None, params=None, method=None, headers = {}, android=False):
        if self.jwt is not None:
            headers['Authorization'] = 'Bearer ' + self.jwt
            self.session.cookies.set("jwt_token", self.jwt, domain=".duolingo.com")

        headers['User-Agent'] = self.USER_AGENT(android)
        if not method:
            method = 'POST' if data else 'GET'
        req = requests.Request(method,
                               url,
                               json=data,
                               params=params,
                               headers=headers)
        prepped = req.prepare()
        resp = self.session.send(prepped)
        if resp.status_code == 403 and resp.json().get("blockScript") is not None:
            raise CaptchaException(
                "Request to URL: {}, using user agent {}, was blocked, and requested a captcha to be solved. "
                "Try changing the user agent and logging in again.".format(url, self.USER_AGENT(android))
            )
        return resp

    def _make_latest_update_date(self):
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def last_updated(self):
        return self._data["last_update"]
    
    def update(self, *args, **kwargs):
        pass

    def get(self, key, default=None):
        if hasattr(self, key):
            try:
                return getattr(self, key)
            except Exception:
                return default
            
        return default

class DuolingoBase(Base):
    _data: dict = {}

    def get(self, key, default=None):
        if hasattr(self, key):
            try:
                return getattr(self, key)
            except Exception:
                return default

        return self._data.get(key, default)

class DuolingoUserData(DuolingoBase):
    def __init__(self, username, password=None, jwt=None, *args, **kwargs):
        """
        :param username: Username to use for duolingo
        :param password: Password to authenticate as user.
        :param jwt: Duolingo login token. Will be checked and used if it is valid request.
        """
        super().__init__(username, password, jwt, *args, **kwargs)
    
    def update(self, *args, **kwargs):
        old_data = self._data
        try:
            by_username = self._get_data(self.username)
            self._data = {"by_username": by_username, "by_id": self._get_data_by_id(by_username.get("id")), "last_update": self._make_latest_update_date()}
        except:
            self._data = {**old_data, "last_update": self._make_latest_update_date()}

    def _get_data(self, username=None):
        """
        Get user's data from ``https://duolingo.com/users/<username>``.
        """
        if username is None:
            username = self.username

        get = self._make_req(f"https://duolingo.com/users/{username}")
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()

    def _get_data_by_id(self, user_id=None):
        """
        Get user's data from ``https://www.duolingo.com/2017-06-30/users/<username>``.
        """
        if user_id is None:
            user_id = self.user_id
        if user_id is None:
            raise Exception("User ID is None")
        
        get = self._make_req(f"https://www.duolingo.com/2017-06-30/users/{user_id}")
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()
        
    @property
    def user_id(self):
        return self._data.get("by_username", {}).get("id")

    @property
    def courses(self) -> list[dict]:
        try:
            output = []
            for course in self._data.get("by_id", {}).get("courses", []):
                if not all(k in course.keys() for k in ["title", "learningLanguage", "xp", "fromLanguage", "id"]):
                    continue
                output.append({
                    "name": course["title"],
                    "language": course["learningLanguage"],
                    "from": course["fromLanguage"],
                    "xp": course["xp"],
                    "id": course["id"],
                })
            return output
        except:
            return []

    @property
    def gems(self) -> int:
        try:
            return self._data.get("by_id", {}).get("gems", -1)
        except:
            return -1

    @property
    def current_streak(self) -> dict:
        try:
            streak = self._data.get("by_id", {}).get("streakData", {}).get("currentStreak", {})
            return {
                "start": streak.get("startDate", "1900-01-01"),
                "end": streak.get("endDate", "1900-01-01"),
                "last_extended": streak.get("lastExtendedDate", "1900-01-01"),
                "length": streak.get("length", -1),
            }
        except:
            return {
                "start": "1900-01-01",
                "end": "1900-01-01",
                "last_extended": "1900-01-01",
                "length": -1,
            }

    @property
    def previous_streak(self) -> dict:
        try:
            streak = self._data.get("by_id", {}).get("streakData", {}).get("previousStreak", {})
            return {
                "start": streak.get("startDate", "1900-01-01"),
                "end": streak.get("endDate", "1900-01-01"),
                "length": streak.get("length", -1),
            }
        except:
            return {
                "start": "1900-01-01",
                "end": "1900-01-01",
                "length": -1,
            }

    @property
    def longest_streak(self) -> dict:
        try:
            streak = self._data.get("by_id", {}).get("streakData", {}).get("longestStreak", {})
            return {
                "start": streak.get("startDate", "1900-01-01"),
                "end": streak.get("endDate", "1900-01-01"),
                "achieved": streak.get("achieveDate", "1900-01-01"),
                "length": streak.get("length", -1),
            }
        except:
            return {
                "start": "1900-01-01",
                "end": "1900-01-01",
                "achieved": "1900-01-01",
                "length": -1,
            }
        
    def lessons_on(self, midnight:datetime) -> list[dict]:
        try:
            xp_gains = self._data.get("by_username", {}).get("calendar", [])
            next_midnight = midnight + timedelta(days=1)

            midnight_timestamp = midnight.timestamp()
            next_midnight_timestamp = next_midnight.timestamp()

            return [lesson for lesson in xp_gains if midnight_timestamp <= int(lesson['datetime']/1000) <= next_midnight_timestamp]
        except:
            return []

    @property
    def lessons_today(self) -> list[dict]:
        midnight = datetime.fromordinal(datetime.today().replace(hour=0, minute=0, second=0, microsecond=0).date().toordinal())
        return self.lessons_on(midnight)

    @property
    def lessons_week(self) -> dict[str, list]:
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        output = {}
        for day in range(0, 7):
            dt = today-timedelta(days=day)
            midnight = datetime.fromordinal(dt.date().toordinal())
            output[f"{dt.strftime('%d.%m.%Y')}"] = self.lessons_on(midnight)
        return output

    @property
    def xp(self) -> int:
        try:
            midnight = datetime.fromordinal(datetime.today().replace(hour=0, minute=0, second=0, microsecond=0).date().toordinal())

            lessons = self.lessons_on(midnight)
            return sum(x['improvement'] for x in lessons)
        except:
            return -1

    @property
    def xp_week(self) -> dict[str, int]:
        try:
            output = {}
            lessons = self.lessons_week
            for k, lessons_day in lessons.items():
                output[k] = sum([lesson.get("improvement", 0) for lesson in lessons_day])
            return output
        except:
            return {}

    @property
    def week_xp(self) -> int:
        try:
            xps = self.xp_week
            return sum([xp_day for _, xp_day in xps.items()])
        except:
            return -1

    @property
    def streak(self) -> int:
        try:
            return self.current_streak.get("length", -1)
        except:
            return -1
        
    @property
    def daily_goal(self) -> int:
        try:
            return self._data.get("by_username", {}).get("daily_goal", -1)
        except:
            return -1
        
    @property
    def streak_extended_today(self) -> bool:
        try:
            return self._data.get("by_username", {}).get("streak_extended_today", False)
        except:
            return False
        
    @property
    def xp_goal(self) -> int:
        try:
            return self._data.get("by_id", {}).get("xpGoal", -1)
        except:
            return -1
        
    @property
    def streak_start(self) -> str:
        try:
            return self.current_streak.get("start", "1900-01-01")
        except:
            return "1900-01-01"
        
    @property
    def streak_end(self) -> str:
        try:
            return self.current_streak.get("end", "1900-01-01")
        except:
            return "1900-01-01"
        
    @property
    def streak_last_extended(self) -> str:
        try:
            return self.current_streak.get("last_extended", "1900-01-01")
        except:
            return "1900-01-01"

    @property
    def avatar(self) -> str:
        try:
            return f'https:{self._data.get("by_username", {}).get("avatar", "//simg-ssl.duolingo.com/avatar/default_2")}/large'
        except:
            return "https://simg-ssl.duolingo.com/avatar/default_2/large"

    @property
    def total_xp(self) -> int:
        try:
            return self._data.get("by_id", {}).get("totalXp", -1)
        except:
            return -1
        
    @property
    def fullname(self) -> str:
        try:
            return self._data.get("by_username", {}).get("fullname", "?")
        except:
            return "?"
        
    @property
    def uzername(self) -> str:
        try:
            return self._data.get("by_username", {}).get("username", "?")
        except:
            return "?"
        
    @property
    def learning_language(self) -> str:
        try:
            return self._data.get("by_username", {}).get("learning_language_string", "?")
        except:
            return "?"
        
    @property
    def languages(self) -> list[str]:
        try:
            return [f"{course.get("name")} ({course.get("from")})" for course in self.courses]
        except:
            return []

class DuolingoLeaderboardData(DuolingoBase):
    def __init__(self, username, password=None, jwt=None, user_id=None, *args, **kwargs):
        """
        :param username: Username to use for duolingo
        :param password: Password to authenticate as user.
        :param jwt: Duolingo login token. Will be checked and used if it is valid request.
        """
        super().__init__(username, password, jwt, *args, **kwargs)

        self.user_id = user_id

    def update(self, *args, **kwargs):
        old_data = self._data
        try:
            self._data = {**self._get_data(), "last_update": self._make_latest_update_date()}
        except:
            self._data = {**old_data, "last_update": self._make_latest_update_date()}

    def _get_data(self):
        """
        Get user's leadorboard data from ``https://duolingo-leaderboards-prod.duolingo.com/leaderboards/7d9f5dd1-8423-491a-91f2-2532052038ce/users/<user_id>``.
        """
        get = self._make_req(f"https://duolingo-leaderboards-prod.duolingo.com/leaderboards/7d9f5dd1-8423-491a-91f2-2532052038ce/users/{self.user_id}")
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()

    def _get_ranking_and_position(self, cohort:dict) -> tuple[dict, int]:
        output = {}
        user_position = -1
        for pos, player in enumerate(cohort.get("rankings", [])):
            if all(
                [
                    k in player.keys()
                    for k in ["avatar_url", "display_name", "has_plus", "score", "streak_extended_today", "user_id"]
                ]
            ):
                position = pos + 1
                output[f"{position}"] = {
                        "display_name": player["display_name"],
                        "score": player["score"],
                        "avatar": player["avatar_url"],
                        "has_plus": player["has_plus"],
                        "extended_today": player["streak_extended_today"],
                        "user_id": player["user_id"],
                    }
                if player["user_id"] == self.user_id:
                    user_position = pos + 1
        return output, user_position
        
    @property
    def start(self) -> str:
        try:
            return self._data.get("active", {}).get("contest", {}).get("contest_start", "?")
        except:
            return "?"
        
    @property
    def end(self) -> str:
        try:
            return self._data.get("active", {}).get("contest", {}).get("contest_end", "?")
        except:
            return "?"
        
    @property
    def tier(self) -> int:
        try:
            return self._data.get("tier", -1)
        except:
            return -1
        
    @property
    def tier_name(self) -> str:
        try:
            return TIER_LIST[f"{self.tier}"]
        except:
            return TIER_LIST["0"]
        
    @property
    def streak_in_tier(self) -> int:
        try:
            return self._data.get("streak_in_tier", -1)
        except:
            return -1
        
    @property
    def position(self) -> int:
        try:
            cohort: dict = self._data.get("active", {}).get("cohort", {})
            _, position = self._get_ranking_and_position(cohort)
            return position
        except:
            return -1
        
    @property
    def ranking(self) -> dict:
        try:
            cohort: dict = self._data.get("active", {}).get("cohort", {})
            ranking, _ = self._get_ranking_and_position(cohort)
            return ranking
        except:
            return {}

class DuolingoFriendsData(DuolingoBase):
    def __init__(self, username, password=None, jwt=None, user_id=None, *args, **kwargs):
        """
        :param username: Username to use for duolingo
        :param password: Password to authenticate as user.
        :param jwt: Duolingo login token. Will be checked and used if it is valid request.
        """
        super().__init__(username, password, jwt, *args, **kwargs)

        self.user_id = user_id

    def update(self, *args, **kwargs):
        old_data = self._data
        try:
            self._data = {**self._get_data(), "last_update": self._make_latest_update_date()}
        except:
            self._data = {**old_data, "last_update": self._make_latest_update_date()}

    def _get_data(self, limit=1000):
        """
        Get user's friends data from ``https://friends-prod.duolingo.com/users/<user_id>/profile``.
        """
        get = self._make_req(f"https://friends-prod.duolingo.com/users/{self.user_id}/profile", params={"pageSize": limit})
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()
        
    @property
    def followers(self):
        try:
            users = self._data.get("followers", {}).get("users", [])
            return [
                {
                    "username": user["username"],
                    "display_name": user["displayName"],
                    "avatar": f'{user["picture"]}/large',
                    "subscription": user["hasSubscription"],
                    "xp": user["totalXp"],
                    "user_id": user["userId"],
                }
                for user in users if all(
                    k in user.keys() for k in ["displayName", "hasSubscription", "totalXp", "userId", "username", "picture"]
                )
            ]
        except:
            return []
        
    @property
    def following(self):
        try:
            users = self._data.get("following", {}).get("users", [])
            return [
                {
                    "username": user["username"],
                    "display_name": user["displayName"],
                    "avatar": f'{user["picture"]}/large',
                    "subscription": user["hasSubscription"],
                    "xp": user["totalXp"],
                    "user_id": user["userId"],
                }
                for user in users if all(
                    k in user.keys() for k in ["displayName", "hasSubscription", "totalXp", "userId", "username", "picture"]
                )
            ]
        except:
            return []

class DuolingoQuestsData(DuolingoBase):
    def __init__(self, username, password=None, jwt=None, user_id=None, *args, **kwargs):
        """
        :param username: Username to use for duolingo
        :param password: Password to authenticate as user.
        :param jwt: Duolingo login token. Will be checked and used if it is valid request.
        """
        super().__init__(username, password, jwt, *args, **kwargs)

        self.user_id = user_id

    def update(self, *args, **kwargs):
        old_data = self._data
        try:
            self._data = {"progress": self._get_data_progress(), "schema": self._get_data_schema(), "last_update": self._make_latest_update_date()}
        except:
            self._data = {**old_data, "last_update": self._make_latest_update_date()}

    def _get_data_progress(self):
        """
        Get user's progress data from ``https://goals-api.duolingo.com/users/<user_id>/progress``.
        """
        headers = {
            'Accepts-Encoding': "gzip, deflate, br, zstd",
            'Accept': "application/json; charset=UTF-8"
        }
        get = self._make_req(f"https://goals-api.duolingo.com/users/{self.user_id}/progress", headers=headers, params={"timezone": datetime.now().astimezone().tzinfo, "ui_language": "en"}, android=True)
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()

    def _get_data_schema(self):
        """
        Get schema data from ``https://goals-api.duolingo.com/schema``.
        """
        headers = {
            'Accepts-Encoding': "gzip, deflate, br, zstd",
            'Accept': "application/json; charset=UTF-8"
        }
        get = self._make_req(f"https://goals-api.duolingo.com/schema", headers=headers, params={"timezone": datetime.now().astimezone().tzinfo, "ui_language": "en"}, android=True)
        if get.status_code == 404:
            raise Exception('Schema not found')
        else:
            return get.json()

    @property
    def monthly(self):
        try:
            quests = self._data.get("progress", {}).get("goals", {}).get("details", {})
            goals = self._data.get("schema", {}).get("goals", [])
            for key, quest in quests.items():
                if key.endswith("monthly_challenge"):
                    limit = len(quest.get("progressIncrements", [])) * 3
                    for goal in goals:
                        if goal.get("goalId") is not None and goal["goalId"] == key:
                            if goal.get("threshold") is not None:
                                limit = goal["threshold"]
                            break
                    return {
                        "progress": quest.get("progress", -1),
                        "increments": quest.get("progressIncrements", []),
                        "limit": limit   # theoretical, based on that every day you can complete max 3 quests (not counting friend quests)
                    }
            raise Exception
        except:
            return {
                "progress": -1,
                "increments": [],
                "limit": -1
            }

    @property
    def friends(self) -> dict:
        try:
            quests = self._data.get("progress", {}).get("goals", {}).get("details", {})
            for key, quest in quests.items():
                try:
                    friend_progress = quest.get("socialProgress", [])
                    if len(friend_progress) > 0:
                        friend_progress = friend_progress[0]
                    else:
                        raise Exception
                    friend = {
                        "user_id": friend_progress.get("userId", "?"),
                        "display_name": friend_progress.get("displayName", "?"),
                        "avatar": f'{friend_progress.get("avatarUrl", "https://simg-ssl.duolingo.com/avatar/default_2")}/large',
                        "increments": friend_progress.get("progressIncrements", []),
                        "xp": sum(friend_progress.get("progressIncrements", [])),
                    }
                except:
                    friend = {
                        "user_id": "?",
                        "display_name": "?",
                        "avatar": "https://simg-ssl.duolingo.com/avatar/default_2/large",
                        "increments": [],
                        "xp": 0,
                    }
                if key.endswith("friends_quest"):
                    return {
                        "progress": quest.get("progress", -1),
                        "increments": quest.get("progressIncrements", []),
                        "xp": sum(quest.get("progressIncrements", [])),
                        "friend": friend
                    }
            raise Exception
        except:
            return {
                "progress": -1,
                "increments": [],
                "xp": -1,
                "friend": {
                    "user_id": "?",
                    "display_name": "?",
                    "avatar": "https://simg-ssl.duolingo.com/avatar/default_2/large",
                    "increments": [],
                    "xp": -1,
                }
            }

class DuolingoFriendStreaksData(DuolingoBase):
    def __init__(self, username, password=None, jwt=None, user_id=None, *args, **kwargs):
        """
        :param username: Username to use for duolingo
        :param password: Password to authenticate as user.
        :param jwt: Duolingo login token. Will be checked and used if it is valid request.
        """
        super().__init__(username, password, jwt, *args, **kwargs)

        self.user_id = user_id

    def update(self, *args, **kwargs):
        old_data = self._data
        try:
            streaks = self._get_data()
            matches = [match["matchId"] for match in streaks.get("friendsStreak", {}).get("confirmedMatches", []) if "matchId" in match]
            self._data = {"friend_streak": streaks, "matches": self._get_data_matches(matches), "last_update": self._make_latest_update_date()}
        except:
            self._data = {**old_data, "last_update": self._make_latest_update_date()}

    def _get_data(self):
        """
        Get user's quests data from ``https://www.duolingo.com/2017-06-30/friends/users/<user_id>/matches``.
        """
        get = self._make_req(f"https://www.duolingo.com/2017-06-30/friends/users/{self.user_id}/matches", params={"activityName": "friendsStreak"})
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()

    def _get_data_matches(self, matches:list):
        """
        Get user's quests data from ``https://www.duolingo.com/2017-06-30/friends/users/<user_id>/matches``.
        """
        get = self._make_req(f"https://www.duolingo.com/friends-streak/matches", params={"matchIds": ",".join(list(matches))})
        if get.status_code == 404:
            raise Exception('User not found')
        else:
            return get.json()

    @property
    def confirmed(self) -> list[dict]:
        try:
            confirmed_matches = self._data.get("friend_streak", {}).get("friendsStreak", {}).get("confirmedMatches", [])
            matches = self._data.get("matches", {}).get("friendsStreak", [])
            output = []
            for confirmed_match in confirmed_matches:
                output_row:dict = {}
                for user_in_match in confirmed_match.get("usersInMatch", []):
                    user_in_match_id = user_in_match.get("userId")
                    detailed_match = None
                    for match in matches:
                        detailed_match_id = match.get("matchId")
                        if detailed_match_id == confirmed_match.get("matchId") and detailed_match_id is not None:
                            detailed_match = match
                            break
                    if detailed_match is None:
                        continue
                    detailed_match_info = detailed_match.get("streaks", [
                            {
                                "startDate": "1900-01-01",
                                "endDate": "1900-01-01",
                                "streakLength": 0,
                                "extended": False,
                            }
                        ])[0]
                    if confirmed_match.get("matchId") is None:
                        continue
                    
                    if user_in_match_id == self.user_id:
                        output_row = {
                            "name": user_in_match.get("name", "?"),
                            "avatar": f'{user_in_match.get("picture", "https://simg-ssl.duolingo.com/avatar/default_2")}/large',
                            "user_id": user_in_match_id,
                            "length": detailed_match_info.get("streakLength", 0),
                            "start": detailed_match_info.get("startDate", "1900-01-01"),
                            "end": detailed_match_info.get("endDate", "1900-01-01"),
                            "extended": detailed_match_info.get("extended", False),
                            "id": confirmed_match.get("matchId"),
                            **output_row
                        }
                    else:
                        output_row["friend"] = {
                            "name": user_in_match.get("name", "?"),
                            "avatar": f'{user_in_match.get("picture", "https://simg-ssl.duolingo.com/avatar/default_2")}/large',
                            "user_id": user_in_match_id,
                            "match_id": confirmed_match.get("matchId"),
                        }
                if len(output_row.keys()) < 1:
                    continue
                output.append(output_row)
                        
            return output
        except:
            return []
        
class Duolingo(Base):
    def __init__(self, username, password=None, jwt=None, *args, **kwargs):
        """
        :param username: Username to use for duolingo
        :param password: Password to authenticate as user.
        :param jwt: Duolingo login token. Will be checked and used if it is valid request.
        """
        super().__init__(username, password, jwt, *args, **kwargs)

        if password or jwt:
            self._login()
        else:
            raise DuolingoException("Password, jwt, or session_file must be specified in order to authenticate.")
        
        self.user_data = DuolingoUserData(self.username, self.password, self.jwt)
        self.user_data.update()
        self.leaderboard_data = DuolingoLeaderboardData(self.username, self.password, self.jwt, user_id=self.user_data.user_id)
        self.friends_data = DuolingoFriendsData(self.username, self.password, self.jwt, user_id=self.user_data.user_id)
        self.friend_streaks_data = DuolingoFriendStreaksData(self.username, self.password, self.jwt, user_id=self.user_data.user_id)
        self.quest_data = DuolingoQuestsData(self.username, self.password, self.jwt, user_id=self.user_data.user_id)

    def _login(self):
        """
        Authenticate through ``https://www.duolingo.com/login``.
        """
        if self._check_login():
            return True
        self.jwt = None

        login_url = "https://www.duolingo.com/login"
        data = {"login": self.username, "password": self.password}
        request = self._make_req(login_url, data)
        attempt = request.json()

        if "failure" not in attempt:
            self.jwt = request.headers['jwt']
            return True

        raise DuolingoException("Login failed")

    def update(self, *args, **kwargs):
        self.user_data.update()
        self.leaderboard_data.update()
        self.friends_data.update()
        self.friend_streaks_data.update()
        self.quest_data.update()

        return self