# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pytest_bdd import scenario, given, when, then
# from test_journal import login_helper

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
    import pdb; pdb.set_trace()
    assert response.html.find('code')
    assert response.html.find('pre')


# NEW SCENARIO


# # Scenario: The homepage has a New Entry button for authn
# @scenario('features/homepage.feature',
#           'The homepage has a New Entry button for authn')
# def test_home_new_entry_btn_as_authn():
#     pass


# # Given an authenticated user
# @given('an authenticated user')
# def an_authenticated_user(app):
#     username, password = ('admin', 'secret')
#     login_helper(username, password, app)  # maybe add .follow()?

# # def test_login_success(app):
# # username, password = ('admin', 'secret')
# # redirect = login_helper(username, password, app)
# # assert redirect.status_code == 302
# # response = redirect.follow()
# # assert response.status_code == 200
# # actual = response.body
# # soup = BeautifulSoup(actual)
# # assert soup.find(id='new-entry-btn')


# # When the user navigates to the homepage
# when('the user navigates to the homepage', fixture='homepage')


# # Then they see a New Entry button
# @then('they see a New Entry button')
# def see_new_entry_button():
#     pass


# # As an author I want to have a permalink for each journal entry where
# # I can view it in detail.
# # Scenario: The homepage lists permalinked entry headings
# @scenario('features/homepage.feature',
#           'The homepage lists permalinked entry headings')
# def test_home_permalinks_an_authn():
#     pass


# # Given an authenticated user
# # @given('an authenticated user')
# # def an_authenticated_user(app):
# #     pass  # test_login_


# # Given a list of three entry headings
# # When the user clicks on a heading
# # Then they are taken to a detailed view of that entry


# # !! OPTIONAL !!
# # I want that same functionality as anonymous, too:
#     # Given an anonymous user
#     # Given a list of three entry headings
#     # When the user clicks on a heading
#     # Then they see a detailed view of that entry


# # As an author I want to edit my journal entries so I can fix errors.
#     # Given an authenticated user
#     # Given a detail view of an entry
#     # When the user navigates to the detail view
#     # Then they see an edit button


# # !! OPTIONAL !!
# # It follows, then, that an unauthenticated user should NOT be
# # able to edit an entry
#     # Given an anonymous user
#     # Given a detail view of an entry
#     # When the user navigates to the detail view
#     # Then they DO NOT see an edit button


# # As an author I want to use MarkDown to create and edit my entries so
# # that I can format them nicely.
#     # Given an authenticated user
#     # Given a journal entry to edit
#     # When they type using MarkDown
#     # Then the entry will display as desired


# # As an author I want to see colorized code samples in my journal
# # entries so that I can more easily understand them.
#     # Given an authenticated user
#     # Given an entry
#     # When the user navigates to the detail view of that entry
#     # Then parts of that entry that have been formatted as code will
#     # be colorized in their display.
