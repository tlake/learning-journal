# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from pyramid import testing


TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://tanner@localhost:5432/test-learning-journal'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL
os.environ['TESTING'] = 'True'


import journal

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
    """Through engine, create a connection to the database"""
    journal.DBSession.registry.clear()
    """At the start of the session, we're certain our db is clear"""
    journal.DBSession.configure(bind=connection)
    """Our db system that we're actually using is bound to the
    connection we're actually using"""
    journal.Base.metadata.bind = engine
    request.addfinalizer(journal.Base.metadata.drop_all)
    """get rid of everything we just made"""
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
Notice that the above fixture requires not only the request fixture provided
by
  pytest, but also the connection fixture you just wrote.
You start a new transaction here in this fixture, mocking the actions usually
  handled by pyramid-tm.
You also add finalizers to rollback and then abort that transaction, which
  ensure that no work in the database will persist between tests
This means that this fixture must be used for each test. That is the default
  scope so we do not designate a scope for this fixture.
"""


def test_write_entry(db_session):
    kwargs = {'title': "Test Title", 'text': "Test entry text"}
    kwargs['session'] = db_session
    # first, assert that there are no entries in the database
    assert db_session.query(journal.Entry).count() == 0
    # now, create an entry using the 'write' class method
    entry = journal.Entry.write(**kwargs)
    # the entry we get back ought to be an instance of Entry
    assert isinstance(entry, journal.Entry)
    # id and created are generated automatically, but only on writing to
    # the database
    # the method should have no id or created attributes at first
    auto_fields = ['id', 'created']
    for field in auto_fields:
        assert getattr(entry, field, None) is None
    # flush the session to "write" the data to the database
    db_session.flush()
    # now we should have one entry:
    assert db_session.query(journal.Entry).count() == 1
    for field in kwargs:
        if field != 'session':
            assert getattr(entry, field, '') == kwargs[field]
    # id and created should be set automaticall upon writing to db:
    for auto in ['id', 'created']:
        assert getattr(entry, auto, None) is not None


def test_entry_no_title_fails(db_session):
    bad_data = {'text': 'test text'}
    journal.Entry.write(session=db_session, **bad_data)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_entry_no_text_fails(db_session):
    bad_data = {'title': 'test title'}
    journal.Entry.write(session=db_session, **bad_data)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_read_entries_empty(db_session):
    entries = journal.Entry.all()
    assert len(entries) == 0


def test_read_entries_one(db_session):
    title_template = "Title {}"
    text_template = "Entry Test {}"
    # write three entries, with order clear in the title and text
    for x in range(3):
        journal.Entry.write(
            title=title_template.format(x),
            text=text_template.format(x),
            session=db_session)
        db_session.flush()
    entries = journal.Entry.all()
    assert len(entries) == 3
    assert entries[0].title > entries[1].title > entries[2].title
    for entry in entries:
        assert isinstance(entry, journal.Entry)


@pytest.fixture()
def app():
    from webtest import TestApp
    from journal import main
    app = main()
    # """ main is just a factory that builds and returns configured
    # wsgi apps """
    return TestApp(app)


def test_empty_listing(app):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No entries here so far'
    assert expected in actual


@pytest.fixture()
def entry(db_session):
    entry = journal.Entry.write(
        title='Test Title',
        text='Test Entry Text',
        session=db_session
    )
    db_session.flush()
    return entry


def test_listing(app, entry):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    for field in ['title', 'text']:
        expected = getattr(entry, field, 'absent')
        assert expected in actual


"""
    Below:

    use app fixture because we want to ensure that we have an
    application to work with.

    'post' method sends an 'HTTP POST' request to provided URL.

    'params' arg represents for input data. IRL, user would have
    entered data into HTML <form> elements.

    'status' arg asserts that the HTTP status code of the response
    matches. Here, we're looking for a 'redirect' response because we're
    expecting the browser to be redirected to a different page once the
    user submits their information.
 """


def test_post_to_add_view(app):
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post.',
    }
    response = app.post('/add', params=entry_data, status='3*')
    redirected = response.follow()
    actual = redirected.body
    for expected in entry_data.values():
        assert expected in actual


def test_add_no_params(app):
    response = app.post('/add', status=500)
    assert 'IntegrityError' in response.body


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
    settings = {
        'auth.username': 'admin',
        'auth.password': 'secret',
    }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req


"""
    Below:

    Tests that use our new 'auth_req' feature
"""


def test_do_login_success(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'admin', 'password': 'secret'}
    assert do_login(auth_req)


def test_do_login_bad_pass(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'admin', 'password': 'wrong'}
    assert not do_login(auth_req)


def test_do_login_bad_user(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'bad', 'password': 'secret'}
    assert not do_login(auth_req)


def test_do_login_missing_params(auth_req):
    from journal import do_login
    for params in ({'username': 'admin'}, {'password': 'secret'}):
        auth_req.params = params
        with pytest.raises(ValueError):
            do_login(auth_req)
