import json
import re
from pathlib import Path

from flask import Flask

from web.models import Problem, TestCase, db

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / 'algocompiler.db'
OUT_DIR = Path(__file__).resolve().parent / 'problems'


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip('-')
    return s


def export_problems_to_json(out_dir=OUT_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()
    with app.app_context():
        problems = Problem.query.order_by(Problem.id.asc()).all()
        files = []
        for idx, p in enumerate(problems, start=1):
            tests = TestCase.query.filter_by(problem_id=p.id).order_by(TestCase.id.asc()).all()
            payload = {
                'title': p.title,
                'topic': p.topic,
                'difficulty': p.difficulty,
                'description': p.description,
                'template_code': p.template_code,
                'test_cases': [
                    {
                        'input': tc.input_data,
                        'expected_output': tc.expected_output,
                        'is_public': bool(tc.is_public),
                    }
                    for tc in tests
                ],
            }
            file_name = f"{idx:02d}-{slugify(p.title)}.json"
            with open(out_dir / file_name, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write('\n')
            files.append(file_name)

        with open(out_dir / 'manifest.json', 'w', encoding='utf-8') as f:
            json.dump({'files': files}, f, ensure_ascii=False, indent=2)
            f.write('\n')

    print(f'Exported {len(files)} problems to {out_dir}')


if __name__ == '__main__':
    export_problems_to_json()
