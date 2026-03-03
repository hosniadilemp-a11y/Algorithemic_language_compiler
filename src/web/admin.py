"""
Admin Blueprint – Teacher Dashboard
Accessible at /admin, protected by session-based login (Teacher1 / teacher).
Completely separate from the main user auth (Flask-Login).
"""
import datetime
import functools
import os

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from web.models import (
    Chapter, Choice, ChallengeSubmission, Problem,
    Question, QuizAttempt, TestCase, User, UserBadge, UserProgress, db
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ── Credentials (override via env vars) ──────────────────────────────────────
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'Teacher1')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'teacher')


def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.is_json or request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('admin.login_page'))
        return f(*args, **kwargs)
    return decorated


# ── Auth ─────────────────────────────────────────────────────────────────────
@admin_bp.route('/', methods=['GET'])
@admin_bp.route('/dashboard', methods=['GET'])
def login_page():
    if session.get('admin_logged_in'):
        return render_template('admin.html', view='dashboard')
    return render_template('admin.html', view='login')


@admin_bp.route('/login', methods=['POST'])
def do_login():
    data = request.get_json() or {}
    if (str(data.get('username', '')).strip() == ADMIN_USERNAME and
            str(data.get('password', '')) == ADMIN_PASSWORD):
        session['admin_logged_in'] = True
        session.permanent = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Identifiants incorrects'}), 401


@admin_bp.route('/logout')
def do_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login_page'))


# ── Problem Editor Pages ──────────────────────────────────────────────────────
@admin_bp.route('/problems/new')
@admin_required
def problem_new():
    return render_template('admin_problem_editor.html', problem=None, problem_id=None)


@admin_bp.route('/problems/<int:pid>/edit')
@admin_required
def problem_edit(pid):
    p = db.session.get(Problem, pid)
    if not p:
        return redirect(url_for('admin.login_page'))
    return render_template('admin_problem_editor.html', problem=_prob_json(p), problem_id=pid)


# ── Analytics: Overview ───────────────────────────────────────────────────────
@admin_bp.route('/api/stats/overview')
@admin_required
def stats_overview():
    return jsonify({
        'total_users': User.query.count(),
        'total_problems': Problem.query.count(),
        'total_chapters': Chapter.query.count(),
        'total_quiz_attempts': QuizAttempt.query.count(),
        'total_submissions': ChallengeSubmission.query.count(),
        'passed_submissions': ChallengeSubmission.query.filter_by(passed=True).count(),
        'total_badges_awarded': UserBadge.query.count(),
    })


# ── Analytics: Activity ───────────────────────────────────────────────────────
@admin_bp.route('/api/stats/activity')
@admin_required
def stats_activity():
    days = int(request.args.get('days', 30))
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)

    activity = {(start + datetime.timedelta(days=i)).isoformat(): 0 for i in range(days)}

    for row in (
        db.session.query(func.date(QuizAttempt.timestamp).label('d'), func.count(QuizAttempt.id).label('c'))
        .filter(QuizAttempt.timestamp >= start)
        .group_by(func.date(QuizAttempt.timestamp)).all()
    ):
        if row.d in activity:
            activity[row.d] += row.c

    for row in (
        db.session.query(func.date(ChallengeSubmission.timestamp).label('d'), func.count(ChallengeSubmission.id).label('c'))
        .filter(ChallengeSubmission.timestamp >= start)
        .group_by(func.date(ChallengeSubmission.timestamp)).all()
    ):
        if row.d in activity:
            activity[row.d] += row.c

    return jsonify({'labels': list(activity.keys()), 'values': list(activity.values())})


# ── Analytics: Users list ─────────────────────────────────────────────────────
@admin_bp.route('/api/stats/users')
@admin_required
def stats_users():
    users = User.query.order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        q_list = QuizAttempt.query.filter_by(user_id=u.id).all()
        avg_score = 0
        if q_list:
            scores = [q.score / q.total_questions * 100 for q in q_list if q.total_questions]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        c_total = ChallengeSubmission.query.filter_by(user_id=u.id).count()
        c_passed = ChallengeSubmission.query.filter_by(user_id=u.id, passed=True).count()
        badge_count = UserBadge.query.filter_by(user_id=u.id).count()

        last_quiz = QuizAttempt.query.filter_by(user_id=u.id).order_by(QuizAttempt.timestamp.desc()).first()
        last_sub = ChallengeSubmission.query.filter_by(user_id=u.id).order_by(ChallengeSubmission.timestamp.desc()).first()
        dates = [d.timestamp for d in [last_quiz, last_sub] if d]
        last_activity = max(dates).isoformat() if dates else None

        result.append({
            'id': u.id, 'name': u.name, 'last_name': u.last_name or '',
            'email': u.email,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_activity': last_activity,
            'quiz_count': len(q_list), 'avg_quiz_score': avg_score,
            'challenge_total': c_total, 'challenge_passed': c_passed,
            'badge_count': badge_count,
        })
    return jsonify({'users': result})


# ── Analytics: User detail ────────────────────────────────────────────────────
@admin_bp.route('/api/stats/users/<int:user_id>')
@admin_required
def stats_user_detail(user_id):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({'error': 'Not found'}), 404

    chapter_map = {c.id: c.title for c in Chapter.query.all()}
    problem_map = {p.id: p.title for p in Problem.query.all()}
    quizzes = QuizAttempt.query.filter_by(user_id=u.id).order_by(QuizAttempt.timestamp.desc()).all()
    subs = ChallengeSubmission.query.filter_by(user_id=u.id).order_by(ChallengeSubmission.timestamp.desc()).all()

    return jsonify({
        'user': {
            'id': u.id, 'name': u.name, 'last_name': u.last_name or '',
            'email': u.email, 'study_year': u.study_year,
            'created_at': u.created_at.isoformat() if u.created_at else None,
        },
        'quizzes': [{
            'chapter': chapter_map.get(q.chapter_id, f'#{q.chapter_id}'),
            'score': q.score, 'total': q.total_questions,
            'pct': round(q.score / q.total_questions * 100, 1) if q.total_questions else 0,
            'timestamp': q.timestamp.isoformat(),
        } for q in quizzes],
        'submissions': [{
            'problem': problem_map.get(s.problem_id, f'#{s.problem_id}'),
            'score': round(s.score, 1), 'passed': s.passed,
            'time_taken': s.time_taken_seconds,
            'timestamp': s.timestamp.isoformat(),
        } for s in subs],
    })


# ── Analytics: Problem stats ──────────────────────────────────────────────────
@admin_bp.route('/api/stats/problems')
@admin_required
def stats_problems():
    problems = Problem.query.order_by(Problem.id.asc()).all()
    result = []
    for p in problems:
        subs = ChallengeSubmission.query.filter_by(problem_id=p.id).all()
        total = len(subs)
        passed = sum(1 for s in subs if s.passed)
        result.append({
            'id': p.id, 'title': p.title, 'topic': p.topic, 'difficulty': p.difficulty,
            'total_attempts': total, 'total_passed': passed,
            'unique_solvers': len(set(s.user_id for s in subs if s.passed)),
            'avg_score': round(sum(s.score for s in subs) / total, 1) if total else 0,
            'avg_time_seconds': round(sum(s.time_taken_seconds for s in subs) / total, 1) if total else 0,
            'pass_rate': round(passed / total * 100, 1) if total else 0,
        })
    return jsonify({'problems': result})


# ── User management ───────────────────────────────────────────────────────────
@admin_bp.route('/api/users/<int:user_id>/reset_password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({'error': 'Not found'}), 404
    pwd = str((request.get_json() or {}).get('password', '')).strip()
    if len(pwd) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    u.password_hash = generate_password_hash(pwd)
    db.session.commit()
    return jsonify({'success': True})


# ── Problems CRUD ─────────────────────────────────────────────────────────────
def _prob_json(p):
    return {
        'id': p.id, 'title': p.title, 'description': p.description,
        'topic': p.topic, 'difficulty': p.difficulty, 'template_code': p.template_code,
        'test_cases': [
            {'id': tc.id, 'input': tc.input_data, 'expected_output': tc.expected_output, 'is_public': bool(tc.is_public)}
            for tc in sorted(p.test_cases, key=lambda x: x.id)
        ],
    }


def _normalize_prob(payload):
    for f in ['title', 'description', 'topic', 'difficulty']:
        if not str(payload.get(f, '')).strip():
            raise ValueError(f"'{f}' is required")
    tcs = payload.get('test_cases', [])
    if not isinstance(tcs, list):
        raise ValueError("'test_cases' must be a list")
    return {
        'title': str(payload['title']).strip(), 'description': str(payload['description']),
        'topic': str(payload['topic']).strip(), 'difficulty': str(payload['difficulty']).strip(),
        'template_code': str(payload.get('template_code', '')),
        'test_cases': [{'input': str(t.get('input', '')), 'expected_output': str(t.get('expected_output', '')), 'is_public': bool(t.get('is_public', False))} for t in tcs],
    }


@admin_bp.route('/api/problems', methods=['GET'])
@admin_required
def admin_list_problems():
    return jsonify({'items': [_prob_json(p) for p in Problem.query.order_by(Problem.id).all()]})


@admin_bp.route('/api/problems/<int:pid>', methods=['GET'])
@admin_required
def admin_get_problem(pid):
    p = db.session.get(Problem, pid)
    return jsonify(_prob_json(p)) if p else (jsonify({'error': 'Not found'}), 404)


@admin_bp.route('/api/problems', methods=['POST'])
@admin_required
def admin_create_problem():
    try:
        data = _normalize_prob(request.get_json(force=True))
        p = Problem(title=data['title'], description=data['description'], topic=data['topic'],
                    difficulty=data['difficulty'], template_code=data['template_code'])
        db.session.add(p)
        db.session.flush()
        for tc in data['test_cases']:
            db.session.add(TestCase(problem_id=p.id, input_data=tc['input'], expected_output=tc['expected_output'], is_public=tc['is_public']))
        db.session.commit()
        return jsonify(_prob_json(p)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/problems/<int:pid>', methods=['PUT'])
@admin_required
def admin_update_problem(pid):
    p = db.session.get(Problem, pid)
    if not p:
        return jsonify({'error': 'Not found'}), 404
    try:
        data = _normalize_prob(request.get_json(force=True))
        p.title = data['title']; p.description = data['description']
        p.topic = data['topic']; p.difficulty = data['difficulty']
        p.template_code = data['template_code']
        TestCase.query.filter_by(problem_id=p.id).delete()
        db.session.flush()
        for tc in data['test_cases']:
            db.session.add(TestCase(problem_id=p.id, input_data=tc['input'], expected_output=tc['expected_output'], is_public=tc['is_public']))
        db.session.commit()
        return jsonify(_prob_json(p))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/problems/<int:pid>', methods=['DELETE'])
@admin_required
def admin_delete_problem(pid):
    p = db.session.get(Problem, pid)
    if not p:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(p); db.session.commit()
    return jsonify({'ok': True})


# ── Chapters CRUD ─────────────────────────────────────────────────────────────
@admin_bp.route('/api/chapters', methods=['GET'])
@admin_required
def admin_list_chapters():
    return jsonify({'items': [
        {'id': c.id, 'identifier': c.identifier, 'title': c.title,
         'question_count': Question.query.filter_by(chapter_id=c.id).count()}
        for c in Chapter.query.order_by(Chapter.id).all()
    ]})


@admin_bp.route('/api/chapters', methods=['POST'])
@admin_required
def admin_create_chapter():
    data = request.get_json(force=True) or {}
    title = str(data.get('title', '')).strip()
    identifier = str(data.get('identifier', '')).strip()
    if not title or not identifier:
        return jsonify({'error': 'title and identifier required'}), 400
    c = Chapter(title=title, identifier=identifier)
    db.session.add(c)
    try:
        db.session.commit()
        return jsonify({'id': c.id, 'title': c.title, 'identifier': c.identifier}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/chapters/<int:cid>', methods=['PUT'])
@admin_required
def admin_update_chapter(cid):
    c = db.session.get(Chapter, cid)
    if not c:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(force=True) or {}
    c.title = str(data.get('title', c.title)).strip() or c.title
    c.identifier = str(data.get('identifier', c.identifier)).strip() or c.identifier
    try:
        db.session.commit(); return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/chapters/<int:cid>', methods=['DELETE'])
@admin_required
def admin_delete_chapter(cid):
    c = db.session.get(Chapter, cid)
    if not c:
        return jsonify({'error': 'Not found'}), 404
    q_ids = [q.id for q in Question.query.filter_by(chapter_id=c.id).all()]
    if q_ids:
        Choice.query.filter(Choice.question_id.in_(q_ids)).delete(synchronize_session=False)
        Question.query.filter_by(chapter_id=c.id).delete(synchronize_session=False)
    UserProgress.query.filter_by(chapter_id=c.id).delete(synchronize_session=False)
    db.session.delete(c); db.session.commit()
    return jsonify({'ok': True})


# ── Questions CRUD ────────────────────────────────────────────────────────────
def _q_json(q):
    return {
        'id': q.id, 'chapter_id': q.chapter_id, 'type': q.type,
        'difficulty': q.difficulty, 'concept': q.concept,
        'text': q.text, 'explanation': q.explanation,
        'choices': [{'id': c.id, 'text': c.text, 'is_correct': bool(c.is_correct)} for c in sorted(q.choices, key=lambda x: x.id)],
    }


def _normalize_q(payload):
    for f in ['type', 'difficulty', 'concept', 'text', 'explanation']:
        if not str(payload.get(f, '')).strip():
            raise ValueError(f"'{f}' is required")
    try:
        chapter_id = int(payload['chapter_id'])
    except Exception:
        raise ValueError("'chapter_id' must be an integer")
    choices = payload.get('choices', [])
    if not isinstance(choices, list) or len(choices) < 2:
        raise ValueError("Need at least 2 choices")
    normalized = [{'text': str(c.get('text', '')).strip(), 'is_correct': bool(c.get('is_correct', False))} for c in choices]
    if not any(c['is_correct'] for c in normalized):
        raise ValueError("At least one choice must be correct")
    return {'chapter_id': chapter_id, 'type': str(payload.get('type', 'MCQ')).strip(),
            'difficulty': str(payload.get('difficulty', 'Medium')).strip(),
            'concept': str(payload['concept']).strip(), 'text': str(payload['text']),
            'explanation': str(payload['explanation']), 'choices': normalized}


@admin_bp.route('/api/questions', methods=['GET'])
@admin_required
def admin_list_questions():
    chapter_id = request.args.get('chapter_id', type=int)
    query = Question.query
    if chapter_id:
        query = query.filter_by(chapter_id=chapter_id)
    return jsonify({'items': [_q_json(q) for q in query.order_by(Question.id).all()]})


@admin_bp.route('/api/questions/<int:qid>', methods=['GET'])
@admin_required
def admin_get_question(qid):
    q = db.session.get(Question, qid)
    return jsonify(_q_json(q)) if q else (jsonify({'error': 'Not found'}), 404)


@admin_bp.route('/api/questions', methods=['POST'])
@admin_required
def admin_create_question():
    try:
        data = _normalize_q(request.get_json(force=True))
        q = Question(chapter_id=data['chapter_id'], type=data['type'], difficulty=data['difficulty'],
                     concept=data['concept'], text=data['text'], explanation=data['explanation'])
        db.session.add(q); db.session.flush()
        for c in data['choices']:
            db.session.add(Choice(question_id=q.id, text=c['text'], is_correct=c['is_correct']))
        db.session.commit()
        return jsonify(_q_json(q)), 201
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/questions/<int:qid>', methods=['PUT'])
@admin_required
def admin_update_question(qid):
    q = db.session.get(Question, qid)
    if not q:
        return jsonify({'error': 'Not found'}), 404
    try:
        data = _normalize_q(request.get_json(force=True))
        q.chapter_id = data['chapter_id']; q.type = data['type']
        q.difficulty = data['difficulty']; q.concept = data['concept']
        q.text = data['text']; q.explanation = data['explanation']
        Choice.query.filter_by(question_id=q.id).delete(); db.session.flush()
        for c in data['choices']:
            db.session.add(Choice(question_id=q.id, text=c['text'], is_correct=c['is_correct']))
        db.session.commit()
        return jsonify(_q_json(q))
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/questions/<int:qid>', methods=['DELETE'])
@admin_required
def admin_delete_question(qid):
    q = db.session.get(Question, qid)
    if not q:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(q); db.session.commit()
    return jsonify({'ok': True})
