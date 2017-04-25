from flask import render_template, flash, redirect, url_for, session, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .models import User
from .oauth import OAuthSignIn

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    return render_template("index.html",
                           title="Home",
                           user=user)

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    nickname, name, email = oauth.callback()
    if email is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user=User.query.filter_by(email=email).first()
    if not user:
        if nickname is None or nickname == "":
            nickname = email.split('@')[0]
        nickname = User.make_unique_nickname(nickname)
        if name is None or name == "":
            name = nickname
        user=User(nickname=nickname, name=name, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=False)
    return redirect(url_for('index'))

@app.route('/login')
def login():
    if g.user is not None and g.user.is_authenticated:
        flash('inside if g.user in login()')
        return redirect(url_for('index'))
    return render_template('login.html',
                           title='Sign In')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@lm.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))
