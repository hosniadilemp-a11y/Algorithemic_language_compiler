import uuid
from datetime import datetime, timedelta, timezone
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from web.app import app, db
from web.models import Chapter, UserProgress


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def _set_learner_cookie(client, learner_id):
    client.set_cookie('algo_learner_id', learner_id)


def test_progress_endpoint_sets_cookies(client):
    response = client.get('/api/quiz/progress')
    assert response.status_code == 200

    payload = response.get_json()
    assert payload['success'] is True
    assert payload['snapshot']['overall_percent'] >= 0

    set_cookie = response.headers.getlist('Set-Cookie')
    assert any('algo_learner_id=' in header for header in set_cookie)
    assert any('algo_progress_snapshot=' in header for header in set_cookie)


def test_pass_threshold_and_best_score_wins(client):
    learner_id = f'test_{uuid.uuid4().hex[:12]}'
    _set_learner_cookie(client, learner_id)

    first = client.post(
        '/api/quiz/save_progress',
        json={
            'chapter_identifier': 'intro',
            'score': 14,
            'total': 20,
            'details': {'Boucles': {'total': 4, 'correct': 2}}
        }
    )
    assert first.status_code == 200
    first_payload = first.get_json()
    assert first_payload['success'] is True
    assert first_payload['snapshot']['overall_percent'] == 10
    assert 'intro' in first_payload['snapshot']['completed_chapter_ids']

    second = client.post(
        '/api/quiz/save_progress',
        json={
            'chapter_identifier': 'intro',
            'score': 5,
            'total': 20,
            'details': {'Boucles': {'total': 4, 'correct': 1}}
        }
    )
    assert second.status_code == 200
    second_payload = second.get_json()
    assert second_payload['success'] is True
    assert second_payload['snapshot']['overall_percent'] == 10
    assert 'intro' in second_payload['snapshot']['completed_chapter_ids']


def test_score_below_threshold_does_not_complete_chapter(client):
    learner_id = f'test_{uuid.uuid4().hex[:12]}'
    _set_learner_cookie(client, learner_id)
    response = client.post(
        '/api/quiz/save_progress',
        json={
            'chapter_identifier': 'tableaux',
            'score': 69,
            'total': 100,
            'details': {'Tableaux': {'total': 5, 'correct': 2}}
        }
    )
    assert response.status_code == 200

    payload = response.get_json()
    assert payload['success'] is True
    assert payload['snapshot']['overall_percent'] == 0
    assert 'tableaux' in payload['snapshot']['attempted_chapter_ids']
    assert 'tableaux' not in payload['snapshot']['completed_chapter_ids']


def test_streak_badge_unlocks_after_three_consecutive_days(client):
    learner_id = f'test_{uuid.uuid4().hex[:12]}'
    _set_learner_cookie(client, learner_id)

    with app.app_context():
        chapters = Chapter.query.filter(Chapter.identifier.in_(['intro', 'tableaux', 'chaines'])).all()
        chapter_map = {chapter.identifier: chapter.id for chapter in chapters}
        if len(chapter_map) < 3:
            pytest.skip('Required quiz chapters are not present in DB')

        now = datetime.now(timezone.utc)
        rows = [
            UserProgress(
                chapter_id=chapter_map['intro'],
                learner_id=learner_id,
                score=16,
                total_questions=20,
                percent_score=80.0,
                is_passed=True,
                details='{}',
                completed_at=now
            ),
            UserProgress(
                chapter_id=chapter_map['tableaux'],
                learner_id=learner_id,
                score=16,
                total_questions=20,
                percent_score=80.0,
                is_passed=True,
                details='{}',
                completed_at=now - timedelta(days=1)
            ),
            UserProgress(
                chapter_id=chapter_map['chaines'],
                learner_id=learner_id,
                score=16,
                total_questions=20,
                percent_score=80.0,
                is_passed=True,
                details='{}',
                completed_at=now - timedelta(days=2)
            )
        ]

        db.session.add_all(rows)
        db.session.commit()

    response = client.get('/api/quiz/progress')
    assert response.status_code == 200
    payload = response.get_json()

    assert payload['success'] is True
    assert payload['snapshot']['streak_days'] >= 3

    badges = {badge['id']: badge['unlocked'] for badge in payload['snapshot']['badges']}
    assert badges.get('streak_3_days') is True
