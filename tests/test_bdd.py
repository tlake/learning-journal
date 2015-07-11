# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pytest_bdd import scenario, given, when, then
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
# assert response.html.find('pre')
# Put ^ that ^ line at the end of detail_view_shows_new_html
# and remove the sys stuff above here to reduplicate
# the weird error with the copyright symbol.

# Don't think that you're safe, UnicodeDecoeError
# I'm coming for you still.

import journal


@scenario('features/homepage.feature',
          'The homepage lists permalinked entries for anon')
def test_home_listing_as_anon():
    pass


@given('an anonymous user')
def an_anonymous_user(app):
    return app


@given('a list of three permalinked entries')
def create_entries(db_session):
    title_template = "Title {}"
    text_template = "Text Entry {}"
    for x in range(3):
        journal.Entry.write(
            title=title_template.format(x),
            text=text_template.format(x),
            session=db_session)
        db_session.flush()


@when('the user visits the homepage')
def visit_homepage(homepage):
    pass


@then('they see a list of three permalinked entries')
def check_entry_list(homepage):
    html = homepage.html
    entries = html.find_all('li', class_='entry-link')
    assert len(entries) == 3


@scenario('features/detail.feature',
          'Entries written with MarkDown are formatted for display')
def test_markdown_displays_as_html():
    pass


@given('an authenticated user')
def an_authenticated_user(app):
    response = app.post(
        '/login',
        params={'username': 'admin', 'password': 'secret'},
        status='*'
    ).follow()

    return {'app': app, 'response': response}


@given('a journal entry written using MarkDown syntax')
def an_entry_with_fenced_code(db_session):
    title = 'here is some title'

    text = """Let's write some fenced code!
    ```python
    Looky here!
    ```
    Regulartype now."""

    entry = journal.Entry.write(
        title=title,
        text=text,
        session=db_session)

    db_session.flush()

    return entry


@when('they visit the detail view')
def visit_detail_view(an_authenticated_user, an_entry_with_fenced_code):
    app = an_authenticated_user['app']
    entry_id = an_entry_with_fenced_code.id
    get_url = '/detail/' + str(entry_id)
    response = app.get(get_url)
    an_authenticated_user['response'] = response


@then('the entry will have converted the MarkDown to HTML')
def detail_view_shows_new_html(an_authenticated_user):
    response = an_authenticated_user['response']
    assert response.html.find('code')
