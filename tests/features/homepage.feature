Feature: Homepage
    A listing of entries from the learning journal in reverse
    chronological order


Scenario: The homepage lists permalinked entries for anon
    Given an anonymous user
    And a list of three permalinked entries
    When the user visits the homepage
    Then they see a list of three permalinked entries


Scenario: The homepage has a New Entry button for authn
    Given an authenticated user
    When the user navigates to the homepage
    Then they see a New Entry button


Scenario: The homepage lists permalinked entry headings
    Given an authenticated user
    And a list of three entry headings
    When the user clicks on a heading
    Then they are taken to a detailed view of that entry
