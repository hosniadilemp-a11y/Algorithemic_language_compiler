from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

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

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True) # Nullable for OAuth users
    name = db.Column(db.String(100), nullable=False) # First name
    last_name = db.Column(db.String(100), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    study_year = db.Column(db.String(50), nullable=True)
    
    # Email verification & Password Reset
    email_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    reset_code = db.Column(db.String(6), nullable=True)
    reset_code_expires = db.Column(db.DateTime, nullable=True)
    
    # Security / Rate Limiting
    failed_login_attempts = db.Column(db.Integer, default=0)
    resend_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)
    
    # OAuth fields
    oauth_provider = db.Column(db.String(50), nullable=True) # 'google', 'github', etc.
    oauth_id = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True, cascade="all, delete-orphan")
    challenge_submissions = db.relationship('ChallengeSubmission', backref='user', lazy=True, cascade="all, delete-orphan")

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    
    # Status interpretation
    all_correct = db.Column(db.Boolean, default=False)
    none_correct = db.Column(db.Boolean, default=False)
    
    details = db.Column(db.Text, nullable=True) # JSON string of answers
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ChallengeSubmission(db.Model):
    __tablename__ = 'challenge_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    score = db.Column(db.Float, nullable=False) # e.g. percentage of tests passed
    code = db.Column(db.Text, nullable=True)
    passed = db.Column(db.Boolean, default=False) # True if all test cases passed
    time_taken_seconds = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.String(50), nullable=False) # e.g. "badge1", "badge_hacker_gold"
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    seen = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('badges', lazy=True, cascade="all, delete-orphan"))
