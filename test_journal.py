# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

TEST_DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'postgresql://tanner@localhost:5432/test-learning-journal'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL
os.environ['TESTING'] = 'True'

import journal

# This decorator registers the connection function as a fixture with pytest.
# The scope argument passed to the decorator determines how often a fixture is run:
#   session scope: only once each time test.py is invoked.
#   module scope: once for each module of tests (once per Python file).
#   function scope: once for each test function (default)
@pytest.fixture(scope='session')
def connection(request):
    engine = create_engine(TEST_DATABASE_URL)
    journal.Base.metadata.create_all(engine)
    connection = engine.connect()
    journal.DBSession.registry.clear()
    journal.DBSession.configure(bind=connection)
    journal.Base.metadata.bind = engine
    request.addfinalizer(journal.Base.metadata.drop_all)
    return connection
# We want to have same connection across all tests, so scope fixture to session.
# A fixture function may be defined with parameters.
# The names of the parameters must match registered fixtures.
# The fixtures named as parameters will be run surrounding the new fixture,
#   like the layers of an onion.
# The request parameter is a special fixture that pytest registers. You use it to
#   add a method that will be run after this fixture goes out of scope using 
#   .addfinalizer()
# By returning connection from this fixture, tests or fixtures that depend on it
#   will be able to access the same connection created here.


# This fixture is responsible for providing a database session to be used in tests.
@pytest.fixture()
def db_session(request, connection):
    from transaction import abort
    trans = connection.begin()
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)

    from journal import DBSession
    return DBSession
# Notice that this fixture requires not only the request fixture provided by
#   pytest, but also the connection fixture you just wrote.
# You start a new transaction here in this fixture, mocking the actions usually
#   handled by pyramid-tm.
# You also add finalizers to rollback and then abort that transaction, which
#   ensure that no work in the database will persist between tests
# This means that this fixture must be used for each test. That is the default
#   scope so we do not designate a scope for this fixture.



def test_write_entry(db_session):
    kwargs = {'title': "Test Title", 'text': "Test entry text"}
    kwargs['session'] = db_session
    # first, assert that there are no entries in the database
    assert db_session.query(journal.Entry).count() == 0
    # now, create an entry using the 'write' class method
    entry = journal.Entry.write(**kwargs)
