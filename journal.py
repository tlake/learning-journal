# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from pyramid.config import Configurator
from pyramid.view import view_config
from waitress import serve

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.exc import DBAPIError

import datetime

from pyramid.httpexceptions import HTTPFound
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget

import markdown


HERE = os.path.dirname(os.path.abspath(__file__))
DB_USR = os.environ.get(b"USER", )
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

DATABASE_URL = os.environ.get(
    b'DATABASE_URL',
    b'postgresql://' + str(DB_USR) + b'@localhost:5432/learning-journal',
)

Base = declarative_base()


class Entry(Base):
    __tablename__ = "entries"

    def __repr__(self):
        return "<Entry(title='{}', created='{}')>".format(
            self.title, self.created
        )

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.Unicode(255), nullable=False)
    text = sa.Column(sa.UnicodeText, nullable=False)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow
    )

    @classmethod
    def all(cls, session=None):
        if session is None:
            session = DBSession
        return session.query(cls).order_by(cls.created.desc()).all()

    @classmethod
    def write(cls, title=None, text=None, session=None):
        if session is None:
            session = DBSession
        instance = cls(title=title, text=text)
        session.add(instance)
        return instance

    @classmethod
    def one(cls, entry_id=None, session=None):
        if session is None:
            session = DBSession
        return session.query(cls).get(entry_id)

    @classmethod
    def modify(cls, entry_id=None, title=None, text=None):
        instance = cls.one(entry_id)
        instance.title = title
        instance.text = text
        return instance

    @property
    def mkdwn(self):

        md = markdown.markdown(
            self.text,
            extensions=[
                'codehilite',
                'fenced_code',
            ],
            output_format='html5',
        )

        return md


def init_db():
    engine = sa.create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)


def do_login(request):
    username = request.params.get('username', None)
    password = request.params.get('password', None)
    if not (username and password):
        raise ValueError('both username and password are required')

    settings = request.registry.settings
    # you can always get hold of application settings with
    # `request.registry.settings`
    manager = BCRYPTPasswordManager()
    if username == settings.get('auth.username', ''):
        hashed = settings.get('auth.password', '')
        return manager.check(hashed, password)
    return False


@view_config(context=DBAPIError)
def db_exception(context, request):
    from pyramid.response import Response
    response = Response(context.message)
    response.status_int = 500
    return response


@view_config(route_name='login', renderer='templates/login.jinja2')
def login(request):
    username = request.params.get('username', '')
    error = ''
    if request.method == 'POST':
        error = 'Login Failed'
        authenticated = False
        try:
            authenticated = do_login(request)
        except ValueError as e:
            error = str(e)

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)

    return {'error': error, 'username': username}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url('home'), headers=headers)


new_entry = {
    'entry': {
        'id': 'new',
        'title': '',
        'text': '',
    },
}


@view_config(route_name='home', renderer='templates/list.jinja2')
def list_view(request):
    entries = Entry.all()
    return {
        'entries': entries,
        'entry': new_entry,
    }


@view_config(route_name='detail', renderer='templates/detail.jinja2')
def detail_view(request):
    entry = Entry.one(request.matchdict['id'])

    return {
        "entry": {
            "id": entry.id,
            "title": entry.title,
            "text": entry.mkdwn,
            "created": entry.created
        }
    }


@view_config(route_name="create", renderer="templates/edit.jinja2")
@view_config(route_name='edit', renderer='templates/edit.jinja2')
def edit_view(request):
    # There are three ways to get to the edit page:
    # (1): Creating a brand new entry
    # (previous location: home)
    if len(request.matchdict) == 0:
        to_render = new_entry

    # (2): Redirect from incomplete submission
    # (previous location: edit_entry)
    # This is also where POSTing a valid entry happens, and where
    # invalid entries are handled
    elif request.method == 'POST':
        entry_id = request.matchdict['entry_id']
        title = request.params.get('title')
        text = request.params.get('text')

        if title != '' and text != '':
            if entry_id == 'new':
                Entry.write(title=title, text=text)
                to_render = HTTPFound(request.route_url('home'))

            else:
                Entry.modify(entry_id=entry_id, title=title, text=text)
                to_render = HTTPFound(request.route_url('detail', id=entry_id))

        else:
            to_render = {
                'entry': {
                    'id': entry_id,
                    'title': title,
                    'text': text
                }
            }

    # (3): Modifying an existing entry
    # (previous location: detail)
    else:
        id_to_match = request.matchdict['entry_id']
        entry = Entry.one(id_to_match)
        to_render = {
            'entry': {
                'id': id_to_match,
                'title': entry.title,
                'text': entry.text
            }
        }

    return to_render


def main():
    # Create a configured wsgi app
    settings = {}
    debug = os.environ.get('DEBUG', True)
    settings['reload_all'] = debug
    settings['debug_all'] = debug
    settings['auth.username'] = os.environ.get('AUTH_USERNAME', 'admin')
    manager = BCRYPTPasswordManager()
    settings['auth.password'] = os.environ.get(
        'AUTH_PASSWORD', manager.encode('secret')
    )
    if not os.environ.get("TESTING", False):
        # only bind the session if it isn't already bound, while testing
        engine = sa.create_engine(DATABASE_URL)
        DBSession.configure(bind=engine)

    # add a secret value for auth tkt signing
    auth_secret = os.environ.get('JOURNAL_AUTH_SECRET', 'itsaseekrit')

    # and add a new value to the constructor for our Configurator:
    config = Configurator(
        settings=settings,
        authentication_policy=AuthTktAuthenticationPolicy(
            secret=auth_secret,
            hashalg='sha512',
        ),
        authorization_policy=ACLAuthorizationPolicy(),
    )

    # we want to use the transaction management provided by pyramid-tm
    config.include("pyramid_tm")
    config.include("pyramid_jinja2")
    config.add_static_view('static', os.path.join(HERE, 'static'))
    config.add_route('home', '/')
    config.add_route('detail', '/detail/{id}')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('edit', '/edit/{entry_id}')
    config.add_route('create', '/create')
    config.scan()
    app = config.make_wsgi_app()
    return app


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 8000)
    serve(app, host='0.0.0.0', port=port)
