from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    identifier = db.Column(db.String(50), nullable=False, unique=True) # e.g., 'intro', 'tableaux'
    questions = db.relationship('Question', backref='chapter', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False) # 'MCQ' or 'TrueFalse'
    difficulty = db.Column(db.String(20), nullable=False) # 'Easy', 'Medium', 'Hard'
    concept = db.Column(db.String(100), nullable=False) # e.g., 'Boucles', 'Variables'
    text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    choices = db.relationship('Choice', backref='question', lazy=True, cascade="all, delete-orphan")

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text, nullable=True) # JSON string of concept mastery
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False) # store Markdown or HTML
    topic = db.Column(db.String(100), nullable=False, index=True)
    difficulty = db.Column(db.String(50), nullable=False, index=True) # Easy, Medium, Hard
    template_code = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to test cases
    test_cases = db.relationship('TestCase', backref='problem', lazy=True, cascade="all, delete-orphan")

class TestCase(db.Model):
    __tablename__ = 'test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_public = db.Column(db.Boolean, default=False) # Only public cases used for "Run Tests"
