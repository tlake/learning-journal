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


# Given an anonymous user
# Given a list of three entry headings
# When the user visits the homepage
# Then they see a list of three entry headings


# As an author I want to have a permalink for each journal entry where
# I can view it in detail.
    # Given an authenticated user
    # Given a list of three entry headings
    # When the user clicks on a heading
    # Then they see a detailed view of that entry


# !! OPTIONAL !!
# I want that same functionality as anonymous, too:
    # Given an anonymous user
    # Given a list of three entry headings
    # When the user clicks on a heading
    # Then they see a detailed view of that entry


# As an author I want to edit my journal entries so I can fix errors.
    # Given an authenticated user
    # Given a detail view of an entry
    # When the user navigates to the detail view
    # Then they see an edit button


# !! OPTIONAL !!
# It follows, then, that an unauthenticated user should NOT be
# able to edit an entry
    # Given an anonymous user
    # Given a detail view of an entry
    # When the user navigates to the detail view
    # Then they DO NOT see an edit button


# As an author I want to use MarkDown to create and edit my entries so
# that I can format them nicely.
    # Given an authenticated user
    # Given a journal entry to edit
    # When they type using MarkDown
    # Then the entry will display as desired


# As an author I want to see colorized code samples in my journal
# entries so that I can more easily understand them.
    # Given an authenticated user
    # Given an entry
    # When the user navigates to the detail view of that entry
    # Then parts of that entry that have been formatted as code will
    # be colorized in their display.
