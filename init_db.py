import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from web.app import app
from web.models import db

with app.app_context():
    print("Creating new database tables if they don't exist...")
    db.create_all()
    print("Done!")
