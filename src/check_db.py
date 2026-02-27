import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from web.app import app
from web.models import Chapter, Question

with app.app_context():
    chapters = Chapter.query.all()
    count = Question.query.count()
    print(f"CHAPTERS: {[c.identifier for c in chapters]}")
    print(f"TOTAL QUESTIONS: {count}")
    
    # Check if 'intro' exist specifically
    intro = Chapter.query.filter_by(identifier='intro').first()
    if intro:
        q_count = Question.query.filter_by(chapter_id=intro.id).count()
        print(f"Questions for 'intro': {q_count}")
    else:
        print("Chapter 'intro' NOT FOUND in DB")
