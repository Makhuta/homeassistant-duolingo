import importlib.util
from pathlib import Path


def load_duolingo_user_data():
    module_path = Path(__file__).resolve().parents[1] / "custom_components" / "duolingo" / "duolingo.py"
    spec = importlib.util.spec_from_file_location("duolingo_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DuolingoUserData


DuolingoUserData = load_duolingo_user_data()


def course(course_id="DUOLINGO_FR_EN", xp=100, score=10, title="French"):
    data = {
        "id": course_id,
        "title": title,
        "learningLanguage": "fr",
        "fromLanguage": "en",
        "xp": xp,
    }
    if score is not None:
        data["cefrScore"] = score
    return data


class FakeUserData(DuolingoUserData):
    def __init__(self, *, initial_courses, next_courses):
        self.username = "tester"
        self._data = {
            "by_username": {"id": "user-id", "streak_extended_today": False},
            "by_id": {
                "id": "user-id",
                "currentCourseId": "DUOLINGO_FR_EN",
                "learningLanguage": "en",
                "courses": initial_courses,
                "totalXp": sum(item.get("xp", 0) for item in initial_courses),
            },
            "last_update": "before",
        }
        self._next_courses = next_courses
        self._internal_data = {}
        self.switch_calls = []
        self._update_internal_data()
        self._change_already_updated()

    def _get_data(self, username=None):
        return {"id": "user-id", "streak_extended_today": True}

    def _get_data_by_id(self, user_id=None):
        return {
            "id": "user-id",
            "currentCourseId": "DUOLINGO_FR_EN",
            "learningLanguage": "en",
            "courses": self._next_courses,
            "totalXp": sum(item.get("xp", 0) for item in self._next_courses),
        }

    def _get_xp_summaries_by_id(self, user_id=None):
        return {"summaries": []}

    def switch_language(self, user_id=None, course_id=None, from_lang=None, fields=None):
        self.switch_calls.append((user_id, course_id, from_lang, fields))
        return {"currentCourse": {"scoreMetadata": {"reachedScore": 99}}}


def test_fresh_course_xp_is_preserved_when_score_refresh_is_skipped():
    user = FakeUserData(
        initial_courses=[course(xp=100, score=12)],
        next_courses=[course(xp=125, score=None)],
    )

    user.update()

    [updated] = user._data["by_id"]["courses"]
    assert updated["xp"] == 125
    assert updated["cefrScore"] == 12
    assert user.switch_calls == []


def test_new_course_does_not_raise_and_is_kept():
    user = FakeUserData(
        initial_courses=[course(xp=100, score=12)],
        next_courses=[
            course(xp=100, score=12),
            course(course_id="DUOLINGO_ES_EN", xp=5, score=None, title="Spanish"),
        ],
    )

    user.update()

    courses = user._data["by_id"]["courses"]
    assert [item["id"] for item in courses] == ["DUOLINGO_FR_EN", "DUOLINGO_ES_EN"]
    assert courses[1]["xp"] == 5


def test_course_refresh_failure_keeps_fresh_xp_and_updates_cache():
    class FailingSwitchUserData(FakeUserData):
        def switch_language(self, *args, **kwargs):
            raise RuntimeError("switch failed")

    user = FailingSwitchUserData(
        initial_courses=[course(xp=100, score=12)],
        next_courses=[course(xp=150, score=None)],
    )
    user._internal_data["already_updated"] = False

    user.update()

    assert user._data["by_id"]["courses"][0]["xp"] == 150
    assert user._internal_data["courses_last_xp"]["en->fr"]["xp"] == 150
