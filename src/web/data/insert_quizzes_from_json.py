import argparse
import json
from pathlib import Path

from flask import Flask

from web.models import Chapter, Choice, Question, UserProgress, db

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / 'algocompiler.db'
DEFAULT_QUIZZES_DIR = Path(__file__).resolve().parent / 'quizzes'

VALID_DIFFICULTIES = {'Easy', 'Medium', 'Hard'}


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def _normalize_difficulty(value):
    if not value:
        return 'Medium'
    v = str(value).strip().lower()
    mapping = {
        'easy': 'Easy',
        'facile': 'Easy',
        'medium': 'Medium',
        'moyen': 'Medium',
        'hard': 'Hard',
        'difficile': 'Hard',
    }
    out = mapping.get(v, str(value).strip())
    return out if out in VALID_DIFFICULTIES else 'Medium'


def _normalize_question_item(item):
    text = (item.get('text') or item.get('question') or '').strip()
    if not text:
        raise ValueError('question/text is required')

    q_type = (item.get('type') or '').strip() or 'MCQ'
    if q_type not in {'MCQ', 'TrueFalse'}:
        q_type = 'MCQ'

    explanation = (item.get('explanation') or '').strip() or 'No explanation provided.'
    concept = (item.get('concept') or 'General').strip() or 'General'
    difficulty = _normalize_difficulty(item.get('difficulty'))

    raw_choices = item.get('choices')
    if not isinstance(raw_choices, list) or len(raw_choices) < 2:
        raise ValueError("'choices' must be a list with at least 2 items")

    normalized_choices = []

    if isinstance(raw_choices[0], dict):
        for c in raw_choices:
            c_text = str(c.get('text', '')).strip()
            if not c_text:
                raise ValueError('choice text cannot be empty')
            normalized_choices.append({
                'text': c_text,
                'is_correct': bool(c.get('is_correct', False)),
            })
    else:
        answer = item.get('answer')
        if answer is None:
            raise ValueError("legacy format requires 'answer'")

        answer_text = str(answer).strip()
        found_correct = False
        for c in raw_choices:
            c_text = str(c).strip()
            if not c_text:
                raise ValueError('choice text cannot be empty')
            is_correct = c_text == answer_text
            found_correct = found_correct or is_correct
            normalized_choices.append({'text': c_text, 'is_correct': is_correct})

        if not found_correct:
            raise ValueError("legacy format answer does not match any choice")

    if not any(c['is_correct'] for c in normalized_choices):
        raise ValueError('at least one choice must be correct')

    if q_type == 'MCQ' and sum(1 for c in normalized_choices if c['is_correct']) > 1:
        # Keep first correct for MCQ to avoid ambiguous grading.
        first_seen = False
        for c in normalized_choices:
            if c['is_correct'] and not first_seen:
                first_seen = True
                continue
            if c['is_correct']:
                c['is_correct'] = False

    if q_type == 'TrueFalse' and len(normalized_choices) != 2:
        q_type = 'MCQ'

    return {
        'type': q_type,
        'difficulty': difficulty,
        'concept': concept,
        'text': text,
        'explanation': explanation,
        'choices': normalized_choices,
    }


def _iter_quiz_files(quizzes_dir: Path):
    return sorted(p for p in quizzes_dir.glob('*.json'))


def insert_quizzes_from_json(quizzes_dir=DEFAULT_QUIZZES_DIR, reset=True):
    quizzes_dir = Path(quizzes_dir)
    if not quizzes_dir.exists():
        raise FileNotFoundError(f"Quizzes directory not found: {quizzes_dir}")

    files = _iter_quiz_files(quizzes_dir)
    if not files:
        raise RuntimeError(f"No quiz json files found in: {quizzes_dir}")

    app = create_app()
    with app.app_context():
        db.create_all()

        if reset:
            Choice.query.delete()
            Question.query.delete()
            UserProgress.query.delete()
            Chapter.query.delete()
            db.session.commit()

        chapters_added = 0
        questions_added = 0
        choices_added = 0

        for file_path in files:
            chapter_identifier = file_path.stem
            chapter_title = chapter_identifier.replace('_', ' ').replace('-', ' ').title()

            chapter = Chapter.query.filter_by(identifier=chapter_identifier).first()
            if chapter is None:
                chapter = Chapter(title=chapter_title, identifier=chapter_identifier)
                db.session.add(chapter)
                db.session.flush()
                chapters_added += 1
            elif not reset:
                Choice.query.filter(Choice.question_id.in_(
                    db.session.query(Question.id).filter_by(chapter_id=chapter.id)
                )).delete(synchronize_session=False)
                Question.query.filter_by(chapter_id=chapter.id).delete(synchronize_session=False)
                UserProgress.query.filter_by(chapter_id=chapter.id).delete(synchronize_session=False)
                db.session.flush()

            with open(file_path, 'r', encoding='utf-8-sig') as f:
                payload = json.load(f)

            if not isinstance(payload, list) or not payload:
                raise ValueError(f"{file_path.name}: expected a non-empty JSON array")

            for index, item in enumerate(payload, start=1):
                if not isinstance(item, dict):
                    raise ValueError(f"{file_path.name} question #{index}: expected object")

                normalized = _normalize_question_item(item)
                q = Question(
                    chapter_id=chapter.id,
                    type=normalized['type'],
                    difficulty=normalized['difficulty'],
                    concept=normalized['concept'],
                    text=normalized['text'],
                    explanation=normalized['explanation'],
                )
                db.session.add(q)
                db.session.flush()
                questions_added += 1

                for c in normalized['choices']:
                    db.session.add(Choice(
                        question_id=q.id,
                        text=c['text'],
                        is_correct=c['is_correct'],
                    ))
                    choices_added += 1

        db.session.commit()

        print(f"Inserted quizzes from {quizzes_dir}")
        print(f"- chapters: {chapters_added}")
        print(f"- questions: {questions_added}")
        print(f"- choices: {choices_added}")


def main():
    parser = argparse.ArgumentParser(description='Insert chapter quizzes from JSON files')
    parser.add_argument('--dir', default=str(DEFAULT_QUIZZES_DIR), help='Directory containing quiz JSON files')
    parser.add_argument('--no-reset', action='store_true', help='Do not delete existing quiz data before insert')
    args = parser.parse_args()

    insert_quizzes_from_json(args.dir, reset=not args.no_reset)


if __name__ == '__main__':
    main()
