import json
from pathlib import Path
from flask import Flask
from web.models import db, Chapter, Question, Choice

# This script allows updating the JSON content (quizzes/problems) 
# on a live database WITHOUT deleting user progress.

BASE_DIR = Path(__file__).resolve().parents[1]
QUIZZES_DIR = BASE_DIR / 'data' / 'quizzes'

def sync_dataset():
    from web.app import app
    with app.app_context():
        files = sorted(QUIZZES_DIR.glob('*.json'))
        if not files:
            print("No JSON files found.")
            return

        for file_path in files:
            chapter_idnt = file_path.stem
            chapter = Chapter.query.filter_by(identifier=chapter_idnt).first()
            
            if not chapter:
                chapter = Chapter(identifier=chapter_idnt, title=chapter_idnt.replace('_', ' ').title())
                db.session.add(chapter)
                db.session.commit()
                print(f"Added new chapter: {chapter_idnt}")

            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)

            # For each question in JSON, check if it exists by text
            # (Simple heuristic: if text matches exactly, we assume it's the same question)
            for item in data:
                q_text = item.get('text', item.get('question', '')).strip()
                if not q_text: continue

                exists = Question.query.filter_by(chapter_id=chapter.id, text=q_text).first()
                if not exists:
                    # Add new question
                    new_q = Question(
                        chapter_id=chapter.id,
                        text=q_text,
                        type=item.get('type', 'MCQ'),
                        difficulty=item.get('difficulty', 'Medium'),
                        concept=item.get('concept', 'General'),
                        explanation=item.get('explanation', '')
                    )
                    db.session.add(new_q)
                    db.session.flush()

                    for c in item.get('choices', []):
                        db.session.add(Choice(
                            question_id=new_q.id,
                            text=c if isinstance(c, str) else c.get('text'),
                            is_correct=False if isinstance(c, str) else c.get('is_correct', False)
                        ))
                    print(f"  + Added question: {q_text[:50]}...")
        
        db.session.commit()
        print("Dataset sync complete.")

if __name__ == "__main__":
    sync_dataset()
