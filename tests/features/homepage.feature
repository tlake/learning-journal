Feature: Homepage
    A listing of entries from the learning journal in reverse
    chronological order


Scenario: The homepage lists entries for anon
    Given an anonymous user
    And a list of three entries
    When the user visits the homepage
    Then they see a list of three entries
