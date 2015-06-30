from pytest_bdd import scenario, given, when, then


@scenario('features/homepage.feature', 'The homepage lists entries for anon')
def test_home_listing_as_anon():
    pass