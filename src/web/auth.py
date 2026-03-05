from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from web.models import db, User
from web.extensions import oauth, mail
import re

auth_bp = Blueprint('auth', __name__)

# Register OAuth clients
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

oauth.register(
    name='github',
    api_base_url='https://api.github.com/',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    client_kwargs={'scope': 'user:email'},
)

import random
from datetime import datetime, timedelta

def generate_verification_code():
    return f"{random.randint(100000, 999999)}"

def generate_math_captcha():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operator = random.choice(['+', '-'])
    if operator == '-' and num1 < num2: 
        num1, num2 = num2, num1
    answer = num1 - num2 if operator == '-' else num1 + num2
    session['captcha_answer'] = str(answer)
    return f"Combien font {num1} {operator} {num2} ?"

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    try:
         mail.send(msg)
         return True
    except Exception as e:
         print(f"Failed to send email: {e}")
         return False

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Adresse e-mail ou mot de passe incorrect.', 'danger')
            return redirect(url_for('auth.login'))
            
        if user.lockout_until and user.lockout_until > datetime.utcnow():
            flash('Votre compte est temporairement bloqué en raison de trop nombreuses tentatives. Réessayez plus tard.', 'danger')
            return redirect(url_for('auth.login'))
            
        if not user.password_hash or not check_password_hash(user.password_hash, password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 3:
                flash('Trop de tentatives échouées. Veuillez réinitialiser votre mot de passe.', 'warning')
            else:
                flash('Adresse e-mail ou mot de passe incorrect.', 'danger')
            db.session.commit()
            return redirect(url_for('auth.login'))
            
        # EMAIL VERIFICATION FROZEN: skip email_verified check
        # if not user.email_verified:
        #     session['verify_email'] = user.email
        #     flash('Veuillez vérifier votre adresse e-mail. Vous pouvez saisir le code envoyé ou en demander un nouveau.', 'warning')
        #     return redirect(url_for('auth.verify'))
            
        # Success login
        if user.failed_login_attempts and user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            db.session.commit()
            
        login_user(user, remember=True)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
        
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')
        date_of_birth_str = request.form.get('date_of_birth')
        study_year = request.form.get('study_year')
        password = request.form.get('password')
        captcha_input = request.form.get('captcha')
        
        # Verify Captcha
        if not captcha_input or captcha_input.strip() != session.get('captcha_answer'):
            flash('Réponse de sécurité (Captcha) incorrecte.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Validation
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
            return redirect(url_for('auth.signup'))
            
        # Check existing
        user = User.query.filter_by(email=email).first()
        if user:
            # If user exists but is locked out or has too many resend attempts, check lockout time
            if user.lockout_until and user.lockout_until > datetime.utcnow():
                flash('Ce compte est temporairement bloqué. Réessayez plus tard.', 'danger')
                return redirect(url_for('auth.signup'))
            flash('Un compte avec cet e-mail existe déjà.', 'danger')
            return redirect(url_for('auth.signup'))
            
        # Parse date
        date_of_birth = None
        if date_of_birth_str:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        # Create user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            email=email, 
            name=name,
            security_question=security_question,
            security_answer=security_answer,
            date_of_birth=date_of_birth, 
            study_year=study_year, 
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        
        # EMAIL VERIFICATION FROZEN: auto-verify account immediately
        new_user.email_verified = True
        db.session.commit()

        session.pop('captcha_answer', None)
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    captcha_text = generate_math_captcha()
    return render_template('auth/signup.html', captcha_text=captcha_text)

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    email = session.get('verify_email')
    
    if request.method == 'POST':
        form_email = request.form.get('email') or email
        code = request.form.get('code')
        user = User.query.filter_by(email=form_email).first()
        
        if not user:
            flash('Utilisateur introuvable.', 'danger')
            return redirect(url_for('auth.login'))
            
        if user.email_verified:
            flash('Le compte a déjà été vérifié. Veuillez vous connecter.', 'success')
            return redirect(url_for('auth.login'))
            
        if user.verification_code == code:
            user.email_verified = True
            user.verification_code = None
            db.session.commit()
            flash('Votre compte a été vérifié avec succès. Vous pouvez maintenant vous connecter.', 'success')
            # Clear session
            session.pop('verify_email', None)
            return redirect(url_for('auth.login'))
        else:
            flash('Code de vérification incorrect.', 'danger')
            return render_template('auth/verify.html', email=form_email)
            
    if not email:
        return redirect(url_for('auth.login'))
        
    captcha_text = generate_math_captcha()
    return render_template('auth/verify.html', email=email, captcha_text=captcha_text)

@auth_bp.route('/resend_code', methods=['POST'])
def resend_code():
    email = session.get('verify_email') or request.form.get('email')
    captcha_input = request.form.get('captcha')
    
    # Check simple captcha if provided
    if not captcha_input or captcha_input.strip() != session.get('captcha_answer', ''):
        flash('Réponse de sécurité (Captcha) incorrecte.', 'danger')
        return redirect(url_for('auth.verify'))
        
    user = User.query.filter_by(email=email).first()
    
    if user and not user.email_verified:
        # Check lockout
        if user.lockout_until and user.lockout_until > datetime.utcnow():
            flash("Vous avez atteint la limite de renvoi. Veuillez revenir dans 6 heures.", "danger")
            return redirect(url_for('auth.verify'))
            
        user.resend_attempts = (user.resend_attempts or 0) + 1
        
        if user.resend_attempts > 2:
            # Lock out for 6 hours
            user.lockout_until = datetime.utcnow() + timedelta(hours=6)
            db.session.commit()
            flash("Nombre maximal de renvois atteint. Votre compte est bloqué pour 6 heures. Veuillez réessayer plus tard.", "danger")
            return redirect(url_for('auth.verify'))
            
        code = generate_verification_code()
        user.verification_code = code
        db.session.commit()
        
        html = render_template('auth/activate.html', code=code, name=user.name)
        subject = "Nouveau code de vérification AlgoCompiler"
        send_email(user.email, subject, html)
        print(f"\n--- DEBUG: RESEND EMAIL CODE FOR {user.email}: {code} ---\n")
        
        session.pop('captcha_answer', None)
        flash('Un nouveau code de vérification a été envoyé !', 'info')
    else:
        flash("Impossible d'envoyer un nouveau code. Compte introuvable ou déjà vérifié.", "danger")
        
    return redirect(url_for('auth.verify'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user and user.password_hash:
            session['reset_email'] = user.email
            session['reset_verified'] = False
            return redirect(url_for('auth.security_check'))
        else:
            flash('Aucun compte (avec mot de passe) n\'est associé à cet e-mail.', 'danger')
            
    return render_template('auth/forgot_password.html')

@auth_bp.route('/security_check', methods=['GET', 'POST'])
def security_check():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))
        
    user = User.query.filter_by(email=email).first()
    if not user:
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        answer = request.form.get('security_answer')
        if answer and answer.strip().lower() == user.security_answer.strip().lower():
            session['reset_verified'] = True
            flash('Parfait ! Saisissez votre nouveau mot de passe.', 'info')
            return redirect(url_for('auth.new_password'))
        else:
            flash('Réponse incorrecte.', 'danger')
            
    return render_template('auth/security_check.html', question=user.security_question)

@auth_bp.route('/verify_reset', methods=['GET', 'POST'])
def verify_reset():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        user = User.query.filter_by(email=email).first()
        
        if user and user.reset_code == code and user.reset_code_expires and user.reset_code_expires > datetime.utcnow():
            # Code is correct
            session['reset_verified'] = True
            return redirect(url_for('auth.new_password'))
        else:
            flash('Code invalide ou expiré.', 'danger')
            
    return render_template('auth/verify_reset.html', email=email)

@auth_bp.route('/new_password', methods=['GET', 'POST'])
def new_password():
    email = session.get('reset_email')
    if not email or not session.get('reset_verified'):
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
            return render_template('auth/new_password.html')
            
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            user.reset_code = None
            user.reset_code_expires = None
            user.failed_login_attempts = 0
            user.lockout_until = None
            db.session.commit()
            
            session.pop('reset_email', None)
            session.pop('reset_verified', None)
            
            flash('Votre mot de passe a été réinitialisé avec succès !', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/new_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/login/<provider>')
def oauth_login(provider):
    if provider == 'google':
        redirect_uri = url_for('auth.oauth_auth', provider='google', _external=True)
        return oauth.google.authorize_redirect(redirect_uri)
    elif provider == 'github':
        redirect_uri = url_for('auth.oauth_auth', provider='github', _external=True)
        return oauth.github.authorize_redirect(redirect_uri)
    return redirect(url_for('auth.login'))

@auth_bp.route('/auth/<provider>')
def oauth_auth(provider):
    try:
        if provider == 'google':
             token = oauth.google.authorize_access_token()
             user_info = token.get('userinfo')
             
             if user_info:
                 email = user_info['email']
                 name = user_info.get('name', '')
                 oauth_id = str(user_info['sub'])
             else:
                 flash("Erreur lors de la récupération des informations Google.", "danger")
                 return redirect(url_for('auth.login'))
                 
        elif provider == 'github':
             token = oauth.github.authorize_access_token()
             resp = oauth.github.get('user')
             user_info = resp.json()
             
             # GitHub might not return email directly if private
             email = user_info.get('email')
             if not email:
                 # Fetch emails manually
                 resp_emails = oauth.github.get('user/emails')
                 emails = resp_emails.json()
                 for e in emails:
                     if e.get('primary') and e.get('verified'):
                         email = e['email']
                         break
             
             name = user_info.get('name') or user_info.get('login', '')
             oauth_id = str(user_info['id'])
             
        else:
             return redirect(url_for('auth.login'))
             
        if not email:
            flash("Impossible de récupérer l'adresse e-mail depuis le fournisseur.", "danger")
            return redirect(url_for('auth.login'))
            
        # Find user or create
        user = User.query.filter_by(email=email).first()
        if not user:
             user = User(email=email, name=name, oauth_provider=provider, oauth_id=oauth_id, email_verified=True)
             db.session.add(user)
             db.session.commit()
        else:
             # Update oauth info if missing
             if not user.oauth_provider:
                 user.oauth_provider = provider
                 user.oauth_id = oauth_id
                 user.email_verified = True
                 db.session.commit()
                 
        login_user(user, remember=True)
        return redirect(url_for('index'))
         
    except Exception as e:
        print(f"OAuth Error: {e}")
        flash('Échec de la connexion. Veuillez réessayer.', 'danger')
        return redirect(url_for('auth.login'))
