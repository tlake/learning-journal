from pytest_bdd import scenario, given, when, then


@scenario('features/homepage.feature', 'The homepage lists entries for anon')
def test_home_listing_as_anon():
    pass

    # FEATURES


@given('an anonymous user')
def an_anonymous_user(app):
    return app


    # Given an anonymous user
    # And a list of three entries
    # When the user visits the homepage
    # Then they see a list of three entries