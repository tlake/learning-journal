# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from pyramid import testing
from cryptacular.bcrypt import BCRYPTPasswordManager


import journal


DB_USR = os.environ.get("USER", )


TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://' + DB_USR + '@localhost:5432/travis_ci_test'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL
os.environ['TESTING'] = 'True'


"""
    This decorator registers the connection function as a fixture with pytest.
    The scope argument passed to the decorator determines how often a fixture
    is run:
        session scope: only once each time test.py is invoked.
        module scope: once for each module of tests (once per Python file).
        function scope: once for each test function (default)
"""


@pytest.fixture(scope='session')
def connection(request):
    engine = create_engine(TEST_DATABASE_URL)
    journal.Base.metadata.create_all(engine)
    connection = engine.connect()
    # Through engine, create a connection to the database
    journal.DBSession.registry.clear()
    # At the start of the session, we're certain our db is clear
    journal.DBSession.configure(bind=connection)
    # Our db system that we're actually using is bound to the
    # connection we're actually using
    journal.Base.metadata.bind = engine
    request.addfinalizer(journal.Base.metadata.drop_all)
    # get rid of everything we just made
    return connection
"""
    Above:

    We want to have same connection across all tests, so scope the fixture
    to session.

    A fixture function may be defined with parameters.

    The names of the parameters must match registered fixtures.

    The fixtures named as parameters will be run surrounding the new fixture,
      like the layers of an onion.

    The request parameter is a special fixture that pytest registers. You use
    it to add a method that will be run after this fixture goes out of scope
    using .addfinalizer()

    By returning connection from this fixture, tests or fixtures that depend
    on it will be able to access the same connection created here.
"""


# This fixture responsible for providing a db session to be used in tests.
"""on the function level:"""


@pytest.fixture()
def db_session(request, connection):
    """ does this inside the transaction that's already opened """
    from transaction import abort
    trans = connection.begin()
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)
    """ These finalizers rollback the session to before any changes were
    made by the tests """

    from journal import DBSession
    return DBSession
    """ because we return DBSession, any test that includes this fixture
    will have a connection to the database session, which will be rolled
    back after we're done with it."""

"""
    Above:

    Notice that the above fixture requires not only the request fixture
    provided by pytest, but also the connection fixture we just wrote.

    We start a new transaction here in this fixture, mocking the actions
    usually handled by `pyramid-tm`.

    We also add finalizers to rollback and then abort that transaction, which
    ensure that no work in the database will persist between tests.

    This means that this fixture must be used for each test. That is the
    default scope so we do not designate a scope for this fixture.
"""


@pytest.fixture()
def app(db_session):
    from webtest import TestApp
    from journal import main
    app = main()
    # """ main is just a factory that builds and returns configured
    # wsgi apps """
    testapp = TestApp(app)
    testapp.set_parser_features(['html5'])
    return testapp


"""
    Below:

    The keys to our 'settings' dict match those we use in the real
    configuration of our application

    The 'setUp' function from 'pyramid.testing' provides the setup needed to
    make a 'DummyRequest' act like a real one

    The 'tearDown' function reverses that process for good test isolation

    The request we return will behave like a real request in that it will
    provide access to the settings we generated
"""


@pytest.fixture(scope='function')
def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'admin',
        'auth.password': manager.encode('secret'),
    }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req


@pytest.fixture()
def entry(db_session):
    entry = journal.Entry.write(
        title='Test Title',
        text='Test Entry Text',
        session=db_session
    )
    db_session.flush()
    return entry


@pytest.fixture()
def homepage(app):
    response = app.get('/')
    return response
