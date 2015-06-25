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

    @classmethod
    def write(cls, title=None, text=None, session=None):
        if session is None:
            session = DBSession
        instance = cls(title=title, text=text)
        session.add(instance)
        return instance

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.Unicode(255), nullable=False)
    created = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    text = sa.Column(sa.UnicodeText, nullable=False)

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


from pyramid.httpexceptions import HTTPNotFound

@view_config(route_name='home', renderer='templates/test.jinja2')
def home(request):
    # .set_trace() inserts a break point. shell will break into a pdb prompt
#    import pdb; pdb.set_trace()
#    return "Hello World"
    return {'one': 'two', 'stuff': ['a', 'b', 'c']}

@view_config(route_name='other', renderer='string')
def other(request):
    import pdb; pdb.set_trace()
    return request.matchdict

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
    config.include("pyramid_jinja2")
    #config.include("pyramid_tm")
    config.add_route('home', '/')
    config.add_route('other', '/other/{special_val}')
    config.scan()
    app = config.make_wsgi_app()
    return app


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
