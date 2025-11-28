import os
from datetime import datetime, date, timedelta, timezone
import json
import random

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import func

from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Optional, Email

# Import Flask-Dance for Google Login
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized

# ----------------- APP CONFIGURATION ----------------- #
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'a_very_secret_key_change_me'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

# Replace with your actual Google Credentials
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'signin'

# ----------------- DATABASE MODELS (ALL DEFINED HERE, BEFORE ROUTES) ----------------- #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True) # Nullable for Google users
    first_login = db.Column(db.DateTime, nullable=True, default=None)
    last_login = db.Column(db.DateTime, nullable=True, default=None)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    agreed_to_terms_on = db.Column(db.DateTime, nullable=True) # Nullable for users created via admin
    sessions = db.relationship('TranslationSession', backref='user', lazy=True, cascade="all, delete-orphan")

class OAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    token = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User)

class TranslationSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ----------------- HELPER FUNCTIONS & FLASK-LOGIN ----------------- #
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------- FLASK-DANCE (GOOGLE LOGIN) SETUP ----------------- #
google_blueprint = make_google_blueprint(
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
)
app.register_blueprint(google_blueprint, url_prefix="/google_login")

@oauth_authorized.connect
def on_google_authorized(blueprint, token):
    if not token: return False
    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok: return False
    info = resp.json()
    email = info["email"]
    user = User.query.filter_by(email=email).first()
    if not user:
        username = email.split('@')[0]
        while User.query.filter_by(username=username).first():
            username = f"{email.split('@')[0]}{random.randint(100,999)}"
        user = User(email=email, username=username, agreed_to_terms_on=datetime.utcnow())
        db.session.add(user)
        db.session.commit()
    login_user(user)
    if user.first_login is None: user.first_login = datetime.utcnow()
    user.last_login = datetime.utcnow()
    db.session.commit()
    flash("Successfully signed in with Google!", "success")
    return False

# ----------------- ADMIN PANEL SETUP ----------------- #
class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional()])
    is_admin = BooleanField('Is Admin?')

class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have permission to access the Admin Panel.', 'danger')
        return redirect(url_for('index'))
    @expose('/')
    def index(self):
        total_users = User.query.count()
        today_start = datetime.combine(date.today(), datetime.min.time())
        new_users_today = User.query.filter(User.first_login >= today_start).count()
        recent_users = User.query.filter(User.last_login != None).order_by(User.last_login.desc()).limit(5).all()
        # Chart logic can be added here as before
        return self.render('admin/index.html', total_users=total_users, new_users_today=new_users_today, recent_users=recent_users)

class UserAdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    column_list = ('id', 'username', 'email', 'is_admin', 'first_login', 'last_login')
    can_export = True
    form = UserForm
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        elif is_created and not form.password.data:
            flash('Password is required when creating a new user.', 'error')
            return False # This will prevent the user from being created without a password
        
admin = Admin(app, name='Gallaudet Admin', index_view=CustomAdminIndexView(name='Dashboard', url='/admin'))
admin.add_view(UserAdminView(User, db.session, endpoint='user'))

# ----------------- PAGE ROUTES (Defined After All Models and Setups) ----------------- #
@app.route('/')
def index(): return render_template('index.html')

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/careers')
def careers(): return render_template('careers.html')

@app.route('/contact')
def contact(): return render_template('contact.html')

@app.route('/faq')
def faq(): return render_template('faq.html')

@app.route('/privacy')
def privacy(): return render_template('privacy.html')

@app.route('/terms')
def terms(): return render_template('terms.html')

@app.route('/practice')
@login_required
def practice():
    return render_template('practice.html')
    
@app.route('/live-translation')
@login_required
def live_translation():
    # This now works because TranslationSession is defined above.
    new_session = TranslationSession(user_id=current_user.id)
    db.session.add(new_session)
    db.session.commit()
    return render_template('live_translation.html', session_id=new_session.id)

@app.route('/dashboard')
@login_required
def dashboard():
    total_sessions = TranslationSession.query.filter_by(user_id=current_user.id).count()
    total_duration_secs = db.session.query(func.sum(TranslationSession.duration_seconds)).filter_by(user_id=current_user.id).scalar() or 0
    recent_sessions = TranslationSession.query.filter_by(user_id=current_user.id).order_by(TranslationSession.start_time.desc()).limit(3).all()
    return render_template('dashboard.html', total_sessions=total_sessions, total_duration_secs=total_duration_secs, recent_sessions=recent_sessions, last_active=current_user.last_login)

# ----------------- AUTH & SESSION ROUTES ----------------- #
@app.route('/session/end', methods=['POST'])
@login_required
def session_end():
    session = TranslationSession.query.filter_by(id=request.json.get('session_id'), user_id=current_user.id).first()
    if session and not session.end_time:
        session.end_time = datetime.now(timezone.utc)
        session.duration_seconds = int((session.end_time - session.start_time).total_seconds())
        db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first() or User.query.filter_by(email=request.form.get('email')).first():
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))
        new_user = User(
            username=request.form.get('username'), 
            email=request.form.get('email'), 
            password_hash=bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8'),
            agreed_to_terms_on=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('signin'))
    return render_template('register.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated: return redirect(url_for('admin.index') if current_user.is_admin else url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
            if user.first_login is None: user.first_login = datetime.utcnow()
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for('admin.index') if user.is_admin else url_for('dashboard'))
        flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('signin.html')

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    # Your full /account route logic goes here (unchanged)
    return render_template('account.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ----------------- RUN THE APP ----------------- #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)