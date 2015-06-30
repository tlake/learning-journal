# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pytest_bdd import scenario, given, when, then

import journal


@scenario('features/homepage.feature', 'The homepage lists entries for anon')
def test_home_listing_as_anon():
    pass

    # FEATURES


@given('an anonymous user')
def an_anonymous_user(app):
    return app


@given('a list of three entries')
def create_entries(db_session):
    title_template = "Title {}"
    text_template = "Entry Text {}"
    for x in range(3):
        journal.Entry.write(
            title=title_template.format(x),
            text=text_template.format(x),
            session=db_session)
        db_session.flush()


@when('the user visits the homepage')
def go_to_homepage(homepage):
    pass


@then('they see a list of three entries')
def check_entry_list(homepage):
    html = homepage.html
    entries = html.find_all('article', class_='entry')
    assert len(entries) == 3
