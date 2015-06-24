# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from pyramid.config import Configurator
from pyramid.view import view_config
from waitress import serve
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
import datetime
# sessionmaker is a factory that makes factories
#   Session = sessionmaker(bind=engine)
#     recall that Session is a class being defined as a sessionmaker class
#     but where the bind is equal to the engine variable that should be defined
#     elsewhere; the engine is the connection, the Session is the cursor.
#   session = Session()
#     actually starts a session
# scoped_session is similar to that process above, only a scoped session helps to
# maintain the association of one session with one request, even when there are
# many many requests happening all at once.
from sqlalchemy.orm import sessionmaker, scoped_session
from zope.sqlalchemy import ZopeTransactionExtension


# bind a symbol, available to all the code in the project, at the module scope which
# will be responsible creating session for each request. it is the point of access
# to the database.
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


Base = declarative_base()


class Entry(Base):

    __tablename__ = "entries"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.Unicode(255), nullable=False)
    creation_date = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    entry_text = sa.Column(sa.UnicodeText, nullable=False)

    def __repr__(self):
        return "<Entry(title='%s', creation_date='%s')>" % (self.title, self.creation_date)


# make a module-level constant for the connection URI (you'll need it elsewhere):
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://tanner@localhost:5432/learning-journal'
)


def init_db():

    engine = sa.create_engine(DATABASE_URL, echo=True)

    Base.metadata.create_all(engine)


@view_config(route_name='home', renderer='string')
def home(request):
    return "Hello World"


def main():
    """Create a configured wsgi app"""
    settings = {}
    debug = os.environ.get('DEBUG', True)
    settings['reload_all'] = debug
    settings['debug_all'] = debug
    if not os.environ.get("TESTING", False):
        # only bind the session if we are not testing
        engine = sa.create_engine(DATABASE_URL)
        DBSession.configure(bind=engine)
    # configuration setup
    config = Configurator(
        settings=settings
    )
    # we want to use the transaction management provided by pyramid-tm
    config.include("pyramid_tm")
    config.add_route('home', '/')
    config.scan()
    app = config.make_wsgi_app()
    return app


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
