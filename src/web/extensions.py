from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"

oauth = OAuth()
mail = Mail()
