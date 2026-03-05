import argparse
import json
import os
from pathlib import Path

from flask import Flask

from web.models import Problem, TestCase, db

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / 'algocompiler.db'
DEFAULT_PROBLEMS_DIR = Path(__file__).resolve().parent / 'problems'


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def _load_manifest_or_glob(problems_dir: Path):
    manifest = problems_dir / 'manifest.json'
    if manifest.exists():
        with open(manifest, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [problems_dir / name for name in data.get('files', [])]
    return sorted(p for p in problems_dir.glob('*.json') if p.name != 'manifest.json')


def _load_problem_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    required = ['title', 'description', 'topic', 'difficulty', 'template_code', 'test_cases']
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"{path.name}: missing fields: {', '.join(missing)}")
    if not isinstance(payload['test_cases'], list) or not payload['test_cases']:
        raise ValueError(f"{path.name}: 'test_cases' must be a non-empty list")

    return payload


def insert_problems_from_json(problems_dir=DEFAULT_PROBLEMS_DIR, reset=True):
    problems_dir = Path(problems_dir)
    if not problems_dir.exists():
        raise FileNotFoundError(f"Problems directory not found: {problems_dir}")

    files = _load_manifest_or_glob(problems_dir)
    if not files:
        raise RuntimeError(f"No problem json files found in: {problems_dir}")

    app = create_app()
    with app.app_context():
        db.create_all()

        if reset:
            TestCase.query.delete()
            Problem.query.delete()
            db.session.commit()

        inserted = 0
        for file_path in files:
            payload = _load_problem_json(file_path)

            problem = Problem(
                title=payload['title'],
                description=payload['description'].strip(),
                topic=payload['topic'],
                difficulty=payload['difficulty'],
                template_code=payload['template_code'].strip(),
            )
            db.session.add(problem)
            db.session.flush()

            for tc in payload['test_cases']:
                db.session.add(TestCase(
                    problem_id=problem.id,
                    input_data=tc.get('input', ''),
                    expected_output=tc.get('expected_output', ''),
                    is_public=bool(tc.get('is_public', False)),
                ))

            inserted += 1

        db.session.commit()

        print(f"Inserted {inserted} problems from {problems_dir}")
        for p in Problem.query.order_by(Problem.id.asc()).all():
            hidden_count = TestCase.query.filter_by(problem_id=p.id, is_public=False).count()
            print(f"- {p.id}: {p.title} (hidden tests: {hidden_count})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Insert challenge problems from JSON files')
    parser.add_argument('--dir', default=str(DEFAULT_PROBLEMS_DIR), help='Directory containing problem JSON files')
    parser.add_argument('--no-reset', action='store_true', help='Do not delete existing problems/test cases before insert')
    args = parser.parse_args()

    insert_problems_from_json(args.dir, reset=not args.no_reset)
