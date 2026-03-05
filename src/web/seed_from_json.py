"""Compatibility seed entrypoint used by web.app auto-seed."""
from web.data.insert_quizzes_from_json import insert_quizzes_from_json


def seed_from_json(quizzes_dir=None, reset=True):
    """Seed chapter quizzes from JSON files.

    Args:
        quizzes_dir: optional directory path. Defaults to src/web/data/quizzes.
        reset: if True, clears existing quiz data first.
    """
    if quizzes_dir:
        return insert_quizzes_from_json(quizzes_dir=quizzes_dir, reset=reset)
    return insert_quizzes_from_json(reset=reset)
