#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, redirect, url_for, session
# from flask.ext.sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler

import os
import uuid
import msal
import requests

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
#db = SQLAlchemy(app)


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app.config['CLIENT_ID'],
        authority=authority or app.config.get('AUTHORITY'),
        client_credential=app.config.get('CLIENT_SECRET'),
        token_cache=cache
    )


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session['token_cache'])
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        session['token_cache'] = cache.serialize()

# Automatically tear down SQLAlchemy.
'''
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
'''

# Login required decorator.
'''
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap
'''
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def home():
    return render_template('pages/placeholder.home.html')


@app.route('/about')
def about():
    return render_template('pages/placeholder.about.html')


@app.route('/login')
def login():
    form = LoginForm(request.form)
    return render_template('forms/login.html', form=form)


@app.route('/msal_login')
def msal_login():
    session['state'] = str(uuid.uuid4())
    auth_url = _build_msal_app().get_authorization_request_url(
        app.config['SCOPE'],
        state=session['state'],
        redirect_uri=url_for('authorized', _external=True)
    )
    return redirect(auth_url)


@app.route(app.config['REDIRECT_PATH'])
def authorized():
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('home'))
    cache = _load_cache()
    result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
        request.args['code'],
        scopes=app.config['SCOPE'],
        redirect_uri=url_for('authorized', _external=True)
    )
    _save_cache(cache)
    if 'access_token' in result:
        session['user'] = result.get('id_token_claims')
        session['token'] = result['access_token']
        return redirect(url_for('profile'))
    return render_template('errors/500.html'), 500


@app.route('/profile')
def profile():
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))
    from graph_api import get_user_profile
    data = get_user_profile(token)
    return render_template('pages/profile.html', result=data)


@app.route('/register')
def register():
    form = RegisterForm(request.form)
    return render_template('forms/register.html', form=form)


@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)

# Error handlers.


@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
