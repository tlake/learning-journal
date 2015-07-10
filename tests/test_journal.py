# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup


DB_USR = os.environ.get("USER", )


TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://' + DB_USR + '@localhost:5432/travis_ci_test'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL
os.environ['TESTING'] = 'True'


import journal


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


def test_empty_listing(app):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No entries here so far'
    assert expected in actual


def test_listing(app, entry):
    response = app.get('/')
    assert response.status_code == 200
    returned_body = response.body
    for field in ['title']:
        expected = getattr(entry, field, 'absent')
        assert expected in returned_body


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


def test_create_new_entry(app):
    entry_data = {
        'id': 'new',
        'title': 'Hello there',
        'text': 'This is a post.',
    }
    response = app.post('/edit/new', params=entry_data, status='3*')
    redirected = response.follow()
    returned_body = redirected.body
    assert entry_data['title'] in returned_body


def test_add_no_params(app):
    response = app.post('/edit/new', status=500)
    assert 'IntegrityError' in response.body


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


def login_helper(username, password, app):
    """
    Encapsulate app login for reuse in tests
    Accept all status codes so that we can make assertions in tests
    """
    login_data = {'username': username, 'password': password}
    return app.post('/login', params=login_data, status='*')


def test_start_as_anonymous(app):
    response = app.get('/', status=200)
    actual = response.body
    soup = BeautifulSoup(actual)
    assert not soup.find(id='new-entry-btn')


def test_login_success(app):
    username, password = ('admin', 'secret')
    redirect = login_helper(username, password, app)
    assert redirect.status_code == 302
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    soup = BeautifulSoup(actual)
    assert soup.find(id=b'new-entry-btn')


def test_login_fails(app):
    username, password = ('admin', 'wrong')
    response = login_helper(username, password, app)
    assert response.status_code == 200
    actual = response.body
    assert "Login Failed" in actual
    soup = BeautifulSoup(actual)
    assert not soup.find(id='new-entry-btn')


def test_logout(app):
    # re-use existing code to ensure we are logged in when we begin
    test_login_success(app)
    redirect = app.get('/logout', status="3*")
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    soup = BeautifulSoup(actual)
    assert not soup.find(id='new-entry-btn')


def test_create_page_exists_if_authn(app):
    test_login_success(app)
    response = app.get('/create', status=200)
    actual = response.body
    soup = BeautifulSoup(actual)
    assert soup.find(id='post-entry-btn')
    assert soup.find('form')


def test_create_page_not_exists_if_unauthn(app):
    response = app.get('/create', status=200)
    actual = response.body
    soup = BeautifulSoup(actual)
    assert not soup.find('form')


def test_add_entry_title_repopulates_on_partial_submit(app):
    test_login_success(app)
    entry_data = {
        'id': 'new',
        'title': 'Hello there',
        'text': '',
    }
    response = app.post('/edit/new', params=entry_data)
    soup = response.html
    assert soup.find(id='entry-title')['value'] == entry_data['title']


def test_add_entry_text_repopulates_on_partial_submit(app):
    test_login_success(app)
    entry_data = {
        'id': 'new',
        'title': 'Hello there',
        'text': '',
    }
    response = app.post('/edit/new', params=entry_data)
    soup = response.html
    assert soup.find(id='entry-text').text == entry_data['text']


def test_add_entry_success(app):
    test_login_success(app)
    entry_data = {
        'title': "The Title of the Entry",
        'text': "The body of the entry"
    }
    submit = app.post("/edit/new", params=entry_data)
    assert submit.status_code == 302
    response = submit.follow()
    assert response.status_code == 200
    soup = response.html
    soup_link = soup.find(class_='entry-link')
    assert entry_data['title'] in soup_link.find('a').text
